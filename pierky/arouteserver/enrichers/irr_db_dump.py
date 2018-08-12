# Copyright (C) 2017-2018 Pier Carlo Chiodi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import logging
import os

from .base import BaseConfigEnricher
from ..ipaddresses import IPNetwork
from ..errors import ARouteServerError, BuilderError

class GenericIRRWhoisRecord_Proxy(object):

    def __init__(self, asn, path, allow_longer_prefixes):
        self.asn = asn
        self.path = path
        self.allow_longer_prefixes = allow_longer_prefixes

    @property
    def prefixes(self):
        with open(self.path, "r") as f:
            prefix_lst = json.load(f)
            for prefix in prefix_lst:
                net = IPNetwork(prefix)
                yield {
                    "prefix": net.ip,
                    "length": net.prefixlen,
                    "max_length": net.max_prefixlen,
                    "exact": not self.allow_longer_prefixes,
                    "ge": net.prefixlen,
                    "le": net.prefixlen if not self.allow_longer_prefixes else net.max_prefixlen
                }

class GenericIRRWhoisDBDumpEnricher(BaseConfigEnricher):

    DESCR = None
    DIR_NAME = None
    CONFIG_SECTION_NAME = None
    PARSER_CLASS = None
    BUILDER_TARGET_DICT_NAME = None

    def enrich(self):
        if self.builder.irrdb_info is None:
            raise BuilderError(
                "{} Whois DB records can be fetched only after that the "
                "list of authorized origin ASNs has been built.".format(
                    self.DESCR
                )
            )

        # List of all the origin ASNs.
        origin_asns = set()
        for bundle_id in self.builder.irrdb_info:
            bundle = self.builder.irrdb_info[bundle_id]
            origin_asns.update(bundle.asns)

        if not origin_asns:
            return

        logging.info("Updating entries from the {} Whois DB dump...".format(
            self.DESCR))

        cache_dir = self.builder.cache_dir

        db_dir = os.path.join(cache_dir, self.DIR_NAME)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
            except OSError as e:
                raise ARouteServerError(str(e))

        afis = [4, 6] if self.builder.ip_ver is None else [self.builder.ip_ver]

        irrdb_cfg = self.builder.cfg_general["filtering"]["irrdb"]
        whois_db_dump = irrdb_cfg[self.CONFIG_SECTION_NAME]
        source = whois_db_dump["source"]

        whois_db_dump = self.PARSER_CLASS(
            cache_dir=cache_dir, cache_expiry=self.builder.cache_expiry,
            source=source)
        whois_db_dump.load_data()
        whois_records = whois_db_dump.whois_records

        # "ASx": ["1.2.3.0/24", ...]
        asn_prefixes = {}

        for record in whois_records:
            asn = record["originas"]
            prefix = record["prefix"]

            # If the current prefix is for an origin ASN that is
            # not allowed for any client then skip it.
            if int(asn[2:]) not in origin_asns:
                continue

            prefix_obj = IPNetwork(prefix)
            if prefix_obj.version not in afis:
                continue

            asn = asn.upper()
            if asn not in asn_prefixes:
                asn_prefixes[asn] = set()
            asn_prefixes[asn].add(prefix)

        allow_longer_prefixes = self.builder.cfg_general["filtering"]["irrdb"]["allow_longer_prefixes"]
        for asn in asn_prefixes:
            path = os.path.join(db_dir, "{}.json".format(asn))
            with open(path, "w") as f:
                json.dump(list(asn_prefixes[asn]), f)
            target_dic = getattr(self.builder, self.BUILDER_TARGET_DICT_NAME)
            target_dic[asn] = \
                GenericIRRWhoisRecord_Proxy(asn, path, allow_longer_prefixes)

        del asn_prefixes
        del whois_records

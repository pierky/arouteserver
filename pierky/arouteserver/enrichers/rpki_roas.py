# Copyright (C) 2017 Pier Carlo Chiodi
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
from ..ripe_rpki_cache import RIPE_RPKI_ROAs

class RPKIROAs_Proxy(object):

    def __init__(self, asn, path):
        self.asn = asn
        self.path = path

    @property
    def roas(self):
        with open(self.path, "r") as f:
            roas = json.load(f)
            for roa in roas:
                net = IPNetwork(roa["prefix"])
                yield {
                    "prefix": net.ip,
                    "length": net.prefixlen,
                    "max_length": net.max_prefixlen,
                    "exact": net.prefixlen == roa["max_len"],
                    "ge": net.prefixlen,
                    "le": roa["max_len"]
                }

class RPKIROAsEnricher(BaseConfigEnricher):

    def enrich(self):
        if self.builder.irrdb_info is None:
            raise BuilderError(
                "RPKI ROAs can be fetched only after that the "
                "list of authorized origin ASNs has been built."
            )

        # List of all the origin ASNs.
        origin_asns = set()
        for bundle_id in self.builder.irrdb_info:
            bundle = self.builder.irrdb_info[bundle_id]
            origin_asns.update(bundle.asns)

        if not origin_asns:
            return

        logging.info("Updating RPKI ROAs...")

        cache_dir = self.builder.cache_dir

        asn_roas_dir = os.path.join(cache_dir, "asn_roas")
        if not os.path.exists(asn_roas_dir):
            try:
                os.makedirs(asn_roas_dir)
            except OSError as e:
                raise ARouteServerError(str(e))

        afis = [4, 6] if self.builder.ip_ver is None else [self.builder.ip_ver]

        irrdb_cfg = self.builder.cfg_general["filtering"]["irrdb"]
        roas_as_route_objects_cfg = irrdb_cfg["use_rpki_roas_as_route_objects"]
        url = roas_as_route_objects_cfg["ripe_rpki_validator_url"]

        ripe_cache = RIPE_RPKI_ROAs(cache_dir=cache_dir,
                                    cache_expiry=self.builder.cache_expiry,
                                    ripe_rpki_validator_url=url)
        ripe_cache.load_data()
        roas = ripe_cache.roas

        allowed_tas = roas_as_route_objects_cfg["allowed_trust_anchors"]

        # "ASx": {"prefix": "a/b", "max_len": c}
        asn_roas = {}

        invalid_roas_cnt = 0
        max_invalid_roas = 10
        for roa in roas["roas"]:
            try:
                ta = roa.get("ta", None)
                if not ta:
                    raise ValueError("missing trust anchor")
                if ta not in allowed_tas:
                    continue

                asn = roa.get("asn", None)
                if not asn:
                    raise ValueError("missing ASN")
                if not asn.startswith("AS"):
                    raise ValueError("invalid ASN: " + asn)
                if not asn[2:].isdigit():
                    raise ValueError("invalid ASN: " + asn)

                # If the current ROA is for an origin ASN that is
                # not allowed for any client then skip it.
                if int(asn[2:]) not in origin_asns:
                    continue

                prefix = roa.get("prefix", None)
                if not prefix:
                    raise ValueError("missing prefix")
                try:
                    prefix_obj = IPNetwork(prefix)
                except:
                    raise ValueError("invalid prefix: " + prefix)

                if prefix_obj.version not in afis:
                    continue

                max_len = roa.get("maxLength", None)
                if not max_len:
                    raise ValueError("missing maxLength")
                if not isinstance(max_len, int):
                    if not max_len.isdigit():
                        raise ValueError("invalid maxLength: " + max_len)
                    max_len = int(max_len)

            except ValueError as e:
                logging.warning("Invalid ROA: {}, {}".format(
                    str(roa), str(e)
                ))

                invalid_roas_cnt += 1
                if invalid_roas_cnt > max_invalid_roas:
                    logging.error(
                        "More than {} invalid ROAs have been found. "
                        "Aborting.".format(max_invalid_roas)
                    )
                    raise BuilderError()

                continue

            asn = asn.upper()
            if asn not in asn_roas:
                asn_roas[asn] = []

            roa_payload = {"prefix": prefix, "max_len": max_len}
            if roa_payload not in asn_roas[asn]:
                asn_roas[asn].append(roa_payload)

        for asn in asn_roas:
            path = os.path.join(asn_roas_dir, "{}.json".format(asn))
            with open(path, "w") as f:
                json.dump(asn_roas[asn], f)
            self.builder.rpki_roas_as_route_objects[asn] = RPKIROAs_Proxy(asn, path)

        del asn_roas
        del roas

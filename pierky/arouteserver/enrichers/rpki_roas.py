# Copyright (C) 2017-2020 Pier Carlo Chiodi
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

import logging

from .base import BaseConfigEnricher
from ..ipaddresses import IPNetwork
from ..errors import BuilderError
from ..ripe_rpki_cache import RIPE_RPKI_ROAs

class RPKIROAsEnricher(BaseConfigEnricher):

    def _use_roas_for_this_origin(self, asn):
        """Return True if ROAs for the given origin ASN must be used

        When ROAs are used only as route objects (so, no BGP Origin
        Validation is configured) only ROAs for authorized origin ASNs
        are returned.
        """

        if self._origin_validation:
            # ROAs are used to perform BGP Origin Validation, so
            # every ROA must be used.
            return True

        if self._roas_as_route_object:
            # If the current ROA is for an origin ASN that is
            # not allowed for any client then skip it.
            if asn in self.origin_asns:
                return True

        return False

    def enrich(self):
        logging.info("Updating RPKI ROAs...")

        filtering = self.builder.cfg_general["filtering"]
        self._roas_as_route_object = \
            filtering["irrdb"]["use_rpki_roas_as_route_objects"]["enabled"]
        self._origin_validation = \
            filtering["rpki_bgp_origin_validation"]["enabled"]

        assert self._roas_as_route_object or self._origin_validation, \
            ("Why here? use_rpki_roas_as_route_objects and "
             "rpki_bgp_origin_validation are both False")

        if self._roas_as_route_object:
            logging.debug("RPKI ROAs will be used as route objects")
        if self._origin_validation:
            logging.debug("RPKI ROAs will be used for origin validation")

        # List of all the origin ASNs.
        if self._roas_as_route_object:
            if self.builder.irrdb_info is None:
                raise BuilderError(
                    "RPKI ROAs can be fetched only after that the "
                    "list of authorized origin ASNs has been built."
                )

            self.origin_asns = set()
            for bundle_id in self.builder.irrdb_info:
                bundle = self.builder.irrdb_info[bundle_id]
                self.origin_asns.update(bundle.asns)

        afis = [4, 6] if self.builder.ip_ver is None else [self.builder.ip_ver]

        rpki_roas_cfg = self.builder.cfg_general["rpki_roas"]
        assert rpki_roas_cfg["source"] == "ripe-rpki-validator-cache", \
            "source is not ripe-rpki-validator-cache"
        urls = rpki_roas_cfg["ripe_rpki_validator_url"]

        ripe_cache = RIPE_RPKI_ROAs(cache_dir=self.builder.cache_dir,
                                    cache_expiry=self.builder.cache_expiry,
                                    ripe_rpki_validator_url=urls)
        ripe_cache.load_data()
        roas = ripe_cache.roas

        allowed_tas = rpki_roas_cfg["allowed_trust_anchors"]

        roas_cnt = {
            "total": 0,
            "invalid_ta": 0,
            "unused": 0,
            "used": {
                "4": 0,
                "6": 0
            }
        }
        for roa in roas["roas"]:
            roas_cnt["total"] += 1

            asn = int(roa["asn"][2:])
            if not self._use_roas_for_this_origin(asn):
                roas_cnt["unused"] += 1
                continue

            ta = roa["ta"]
            if ta not in allowed_tas:
                roas_cnt["invalid_ta"] += 1
                continue

            prefix = roa["prefix"]

            prefix_obj = IPNetwork(prefix)
            if prefix_obj.version not in afis:
                continue

            max_len = int(roa["maxLength"])

            roa_payload = {"prefix": prefix, "length": prefix_obj.prefixlen,
                           "max_len": max_len, "asn": asn}

            prefix_len = str(prefix_obj.prefixlen)
            if prefix_len not in self.builder.rpki_roas:
                self.builder.rpki_roas[prefix_len] = [roa_payload]
            else:
                self.builder.rpki_roas[prefix_len].append(roa_payload)

            roas_cnt["used"][str(prefix_obj.version)] += 1

        stats = "RPKI ROAs: "
        stats += "{} total".format(roas_cnt["total"])
        if roas_cnt["invalid_ta"] > 0:
            stats += ", {} from not allowed TAs".format(roas_cnt["invalid_ta"])
        if roas_cnt["unused"] > 0:
            stats += ", {} unused".format(roas_cnt["unused"])
        for afi in afis:
            stats += ", {} used for IPv{}".format(
                roas_cnt["used"][str(afi)], afi
            )
        logging.info(stats)

        del roas

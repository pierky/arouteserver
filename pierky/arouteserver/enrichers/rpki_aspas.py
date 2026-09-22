# Copyright (C) 2017-2026 Pier Carlo Chiodi
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


class RPKIASPAsEnricher(BaseConfigEnricher):

    def enrich(self):
        logging.info("Updating RPKI ASPAs...")

        rpki_aspas_cfg = self.builder.cfg_general["rpki_aspas"]
        assert rpki_aspas_cfg["source"] == "json", "source is not json"

        urls = rpki_aspas_cfg["json_url"]
        allowed_tas = rpki_aspas_cfg["allowed_trust_anchors"]

        cache = self.builder.get_rpki_json_cache(urls)
        aspas = cache.aspas

        aspas_cnt = {
            "total": 0,
            "invalid_ta": 0,
            "missing_ta": 0,
        }

        # customer ASN -> set of provider ASNs.
        # Multiple ASPAs for the same customer ASN must be merged into
        # a single record: both BIRD ('route aspa <n> providers ...')
        # and OpenBGPD ('aspa-set { customer-as <n> ... }') reject a
        # customer ASN that is used more than once.
        merged = {}
        expires = {}

        for aspa in aspas:
            aspas_cnt["total"] += 1

            ta = aspa.get("ta", None)
            if ta is None:
                # Only the original RIPE NCC RPKI Validator format
                # includes the trust anchor of each ASPA, so for the
                # other formats 'allowed_trust_anchors' can't be
                # honoured.
                aspas_cnt["missing_ta"] += 1
            elif ta not in allowed_tas:
                aspas_cnt["invalid_ta"] += 1
                continue

            customer_asn = int(aspa["customer"][2:])

            providers = merged.setdefault(customer_asn, set())
            providers.update(int(provider[2:]) for provider in aspa["providers"])

            if "expires" in aspa:
                # When the same customer ASN is covered by more than
                # one ASPA, the earliest expiration time is used.
                if customer_asn in expires:
                    expires[customer_asn] = min(expires[customer_asn],
                                                int(aspa["expires"]))
                else:
                    expires[customer_asn] = int(aspa["expires"])

        if aspas_cnt["missing_ta"] > 0:
            logging.warning(
                "{} ASPAs were gathered from a source that does not provide "
                "any trust anchor information, so the "
                "'rpki_aspas.allowed_trust_anchors' option could not be "
                "honoured for them and they are all used. Only the original "
                "RIPE NCC RPKI Validator JSON format includes the 'ta' "
                "attribute of ASPAs; the rpki-client, NTT and OctoRPKI "
                "formats do not.".format(aspas_cnt["missing_ta"])
            )

        for customer_asn in sorted(merged):
            aspa_payload = {
                "customer_asn": customer_asn,
                "providers": sorted(merged[customer_asn])
            }
            if customer_asn in expires:
                aspa_payload["expires"] = expires[customer_asn]

            self.builder.rpki_aspas.append(aspa_payload)

        stats = "RPKI ASPAs: "
        stats += "{} total".format(aspas_cnt["total"])
        if aspas_cnt["invalid_ta"] > 0:
            stats += ", {} from not allowed TAs".format(aspas_cnt["invalid_ta"])
        if aspas_cnt["missing_ta"] > 0:
            stats += ", {} without TA info".format(aspas_cnt["missing_ta"])
        stats += ", {} used".format(len(self.builder.rpki_aspas))
        logging.info(stats)

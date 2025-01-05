# Copyright (C) 2017-2025 Pier Carlo Chiodi
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
import shutil
import tempfile
import unittest
import requests

from pierky.arouteserver.arin_db_dump import ARINWhoisDBDump
from pierky.arouteserver.config.general import ConfigParserGeneral
from pierky.arouteserver.irrdb import ASSet, RSet
from pierky.arouteserver.last_version import LastVersion
from pierky.arouteserver.peering_db import PeeringDBNet, PeeringDBIXList, \
                                           PeeringDBNetNeverViaRouteServers
from pierky.arouteserver.ripe_rpki_cache import RIPE_RPKI_ROAs
from pierky.arouteserver.euro_ix import EuroIXMemberList
from pierky.arouteserver.commands.ixf_member_list_from_clients import IXFMemberListFromClientsCommand

cache_dir = None
cache_cfg = {
    "cache_dir": None
}


class TestExternalResources(unittest.TestCase):

    def setUp(self):
        global cache_dir
        cache_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")
        cache_cfg["cache_dir"] = cache_dir

    def tearDown(self):
        shutil.rmtree(cache_dir, ignore_errors=True)

    def test_peeringdb(self):
        """External resources: PeeringDB, max-prefix and AS-SET"""
        net = PeeringDBNet(3333, **cache_cfg)
        net.load_data()
        self.assertTrue(net.info_prefixes4 > 0)
        self.assertTrue(net.info_prefixes6 > 0)
        self.assertEqual(net.irr_as_sets, ["AS-RIPENCC"])

    def test_peeringdb_never_via_route_servers(self):
        """External resources: PeeringDB, never via route-servers"""
        net = PeeringDBNetNeverViaRouteServers()
        net.load_data()
        self.assertTrue(len(net.networks) > 0)
        self.assertTrue({"asn": 2914} in net.networks)

    def test_ixf_db(self):
        """External resources: PeeringDB IX list"""
        ixp_list = PeeringDBIXList()
        ixp_list.load_data()
        self.assertTrue(len(ixp_list.ixp_list) > 0)

    def test_last_version(self):
        """External resources: last version via PyPI"""
        last_ver = LastVersion(**cache_cfg)
        last_ver.load_data()
        ver = last_ver.last_version
        self.assertTrue(int(ver.split(".")[0]) >= 1)
        self.assertTrue(int(ver.split(".")[1]) >= 0)
        self.assertTrue(int(ver.split(".")[2]) >= 0)

    def _test_rpki_roas_per_provider(self, provider, use_expires_attr=False):
        cfg = ConfigParserGeneral()
        urls = cfg.get_schema()["cfg"]["rpki_roas"]["ripe_rpki_validator_url"].default
        for url in urls:
            if provider in url:
                rpki_roas = RIPE_RPKI_ROAs(ripe_rpki_validator_url=[url], **cache_cfg)
                break
        rpki_roas.load_data()
        self.assertTrue(len(rpki_roas.roas) > 0)
        self.assertTrue(any([r for r in rpki_roas.roas["roas"] if r["prefix"] == "193.0.0.0/21"]))
        if use_expires_attr:
            self.assertTrue(
                all(
                    r.get("expires", None) > 0
                    for r in rpki_roas.roas["roas"]
                )
            )

        allowed_per_ta = {}

        allowed_tas = cfg.get_schema()["cfg"]["rpki_roas"]["allowed_trust_anchors"].default
        for roa in rpki_roas.roas["roas"]:
            ta = roa["ta"]
            if ta not in allowed_per_ta:
                allowed_per_ta[ta] = 0
            if roa["ta"] in allowed_tas:
                allowed_per_ta[ta] += 1

        tas_with_allowed_roas = 0
        for ta in allowed_per_ta:
            if allowed_per_ta[ta] > 0:
                tas_with_allowed_roas += 1

        self.assertTrue(tas_with_allowed_roas >= 4)

    def test_rpki_roas_ripe(self):
        """External resources: RPKI ROAs, RIPE"""
        self._test_rpki_roas_per_provider("ripe.net")

    def test_rpki_roas_ntt(self):
        """External resources: RPKI ROAs, NTT"""
        self._test_rpki_roas_per_provider("ntt.net", use_expires_attr=True)

    def test_rpki_roas_rpki_client(self):
        """External resources: RPKI ROAs, rpki-client"""
        self._test_rpki_roas_per_provider("rpki-client.org", use_expires_attr=True)

    def test_asset_bgpq3(self):
        """External resources: ASNs from AS-SET via bgpq3"""
        asset = ASSet(["AS-RIPENCC"], bgpq3_path="bgpq3", **cache_cfg)
        asset.load_data()
        self.assertTrue(len(asset.asns) > 0)
        self.assertTrue(3333 in asset.asns)

    def test_asset_bgpq4(self):
        """External resources: ASNs from AS-SET via bgpq4"""
        asset = ASSet(["AS-RIPENCC"], bgpq3_path="bgpq4", **cache_cfg)
        asset.load_data()
        self.assertTrue(len(asset.asns) > 0)
        self.assertTrue(3333 in asset.asns)

    def test_rset_bgpq3(self):
        """External resources: prefixes from AS-SET via bgpq3"""
        rset = RSet(["AS-RIPENCC"], 4, False, bgpq3_path="bgpq3", **cache_cfg)
        rset.load_data()
        self.assertTrue(len(rset.prefixes) > 0)
        self.assertTrue(any([p for p in rset.prefixes if p["prefix"] == "193.0.0.0"]))

    def test_rset_bgpq4(self):
        """External resources: prefixes from AS-SET via bgpq4"""
        rset = RSet(["AS-RIPENCC"], 4, False, bgpq3_path="bgpq4", **cache_cfg)
        rset.load_data()
        self.assertTrue(len(rset.prefixes) > 0)
        self.assertTrue(any([p for p in rset.prefixes if p["prefix"] == "193.0.0.0"]))

    def test_routeservers_excluded_from_clients(self):
        """External resources: route servers excluded from clients-from-euroix"""

        # The idea behind this check is to be sure that the most recent version of
        # the Euro-IX Member list JSON file will be always processed correctly, and
        # that the route server IPs will always be excluded from the output of the
        # clients-from-euroix command.
        #
        # Here, the INEX members list is retrieve from their member-export endpoint.
        # INEX is behind IXPManager, and hopefully they will always export their
        # member list using the most recent version of the Euro-IX Member JSON format.
        # Doing this, hopefully this test will catch any major issue that could affect
        # the integration with IXPManager and the processing of the latest version of
        # the Euro-IX schema.
        euro_ix = EuroIXMemberList("https://www.inex.ie/ixp/api/v4/member-export/ixf", None, None)
        clients = euro_ix.get_clients(ixp_id=1, vlan_id=2)
        client_ips = [client["ip"] for client in clients]

        for rs_ip in (
            "185.6.36.8",
            "2001:7f8:18::8",
        ):
            self.assertTrue(rs_ip not in client_ips)

        for member_ip in (
            "185.6.36.60",
            "2001:7f8:18::60",
        ):
            self.assertTrue(member_ip in client_ips)

    def test_euroix_json_file_from_clients(self):
        """External resources: Euro-IX from clients build and validation"""
        clients_path = "config.d/clients.yml"

        json_data = IXFMemberListFromClientsCommand.build_json(
            clients_path, 1, "Test IX", 1, 1
        )

        validator_response = requests.post(
            "https://api.ixpdb.net/v1/validation/",
            json=json_data
        )
        validator_response.raise_for_status()

        validator_results = validator_response.json()

        self.assertTrue(validator_results["errors"] == [])

    def test_euroix_json_file_from_clients_merge_file_docs(self):
        """External resources: Euro-IX from clients build and validation (using merge-file)"""
        clients_path = "config.d/clients.yml"

        merge_file_content = json.load(open("tests/static/data/ixf_member_list_from_clients_merge_file_for_docs.json"))

        json_data = IXFMemberListFromClientsCommand.build_json(
            clients_path, 1, "Test IX", 1, 1
        )

        final_output = IXFMemberListFromClientsCommand.apply_merge_file(
            json_data, merge_file_content, {
                "ixp_id": 1,
                "ixf_id": 2,
                "shortname": "Test short name",
                "vlan": 1
            }
        )

        validator_response = requests.post(
            "https://api.ixpdb.net/v1/validation/",
            json=final_output
        )
        validator_response.raise_for_status()

        validator_results = validator_response.json()

        self.assertTrue(validator_results["errors"] == [])

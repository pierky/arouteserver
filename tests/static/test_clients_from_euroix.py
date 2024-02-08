# Copyright (C) 2017-2024 Pier Carlo Chiodi
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
import os
import unittest
import yaml

from pierky.arouteserver.euro_ix import EuroIXMemberList
from pierky.arouteserver.config.clients import merge_clients

class TestClientsFromEuroIX(unittest.TestCase):

    def _load(self, filename):
        path = os.path.join(
            os.path.dirname(__file__),
            "euroix_data",
            filename + ".json"
        )
        with open(path, "r") as f:
            return json.load(f)

    def _run(self, filename, *args, **kwargs):
        data = self._load(filename)
        euro_ix = EuroIXMemberList(data, None, None)
        self.clients = euro_ix.get_clients(*args, **kwargs)

    def _result_match_file(self, json_in_filename, yml_res_filename=None,
                           *args, **kwargs):
        self._run(json_in_filename, *args, **kwargs)
        res = {"clients": self.clients}

        yml_res_path = os.path.join(
            os.path.dirname(__file__),
            "euroix_data",
            "{}.yml".format(yml_res_filename or json_in_filename)
        )
        with open(yml_res_path, "r") as f:
            expected_result = yaml.safe_load(f.read())

        self.assertEqual(res, expected_result)

        return res

    def test_official_basic_example(self):
        """Clients from Euro-IX: official basic example"""
        self._run("official_basic_example", ixp_id=42)
        self.assertEqual(self.clients, [])

    def test_official_more_complex_example(self):
        """Clients from Euro-IX: official more complex example"""
        self._result_match_file("official_more_complex_example",
            ixp_id=42)

        self._result_match_file("official_more_complex_example",
            ixp_id=42, vlan_id=0)

        self._result_match_file("official_more_complex_example",
            ixp_id=42, vlan_id=0, routeserver_only=True)

        with self.assertRaisesRegex(Exception, "IXP ID 1 not found"):
            self._run("official_more_complex_example", ixp_id=1)

        self._run("official_more_complex_example", ixp_id=42, vlan_id=1)
        self.assertEqual(len(self.clients), 0)

    def test_routeserver_only(self):
        """Clients from Euro-IX: --routeserver-only filter"""
        self._result_match_file("routeserver_only",
            ixp_id=42, routeserver_only=True)
        self._result_match_file("routeserver_only", "routeserver_only_no_flag",
            ixp_id=42)

    def test_ixpmanager_workaround(self):
        """Clients from Euro-IX: IXP-Manager workaround"""
        self._result_match_file("ixpmanager_workaround", ixp_id=1)

    # List of export files:
    # http https://api.ixpdb.net/v1/provider/list | jq '.[].apis.ixfexport'
    #
    # Set name of local file (no extension)
    # LOCAL_FILE=tests/static/euroix_data/skip_routeserver_06
    #
    # Download a JSON file:
    # http http://www.trex.fi/memberlist.json > $LOCAL_FILE.json
    #
    # Create the clients.yml file:
    # ./scripts/arouteserver clients-from-euroix --cfg var/arouteserver.yml -i $LOCAL_FILE.json -o $LOCAL_FILE.yml --vlan-id 4 46

    def test_skip_routeserver_06(self):
        """Clients from Euro-IX: route server classification, 0.6"""
        clients = self._result_match_file("skip_routeserver_06", ixp_id=46, vlan_id=4)["clients"]

        # Be sure the route server IPs are not taken into account.
        for rs_ip in (
            "195.140.192.1",
            "2001:7f8:1d:4::1"
        ):
            assert rs_ip not in [client["ip"] for client in clients]

        # Just to be sure the conversion worked, check some other IPs
        # which are expected to be imported as client.
        for member_ip in (
            "195.140.192.38",
            "2001:7f8:1d:4::8653:1"
        ):
            assert member_ip in [client["ip"] for client in clients]

    def test_skip_routeserver_07(self):
        """Clients from Euro-IX: route server classification, 0.7"""
        clients = self._result_match_file("skip_routeserver_07", ixp_id=1, vlan_id=1)["clients"]

        # Be sure the route server IPs are not taken into account.
        for rs_ip in (
            "206.53.201.2",
            "2001:504:60::2",
            "206.53.201.3",
            "2001:504:60::3"
        ):
            assert rs_ip not in [client["ip"] for client in clients]

        # Just to be sure the conversion worked, check some other IPs
        # which are expected to be imported as client.
        for member_ip in (
            "206.53.201.22",
            "206.53.201.21",
            "2001:504:60::672f"
        ):
            assert member_ip in [client["ip"] for client in clients]

    def test_skip_routeserver_10(self):
        """Clients from Euro-IX: route server classification, 1.0"""
        clients = self._result_match_file("skip_routeserver_10", ixp_id=1, vlan_id=1)["clients"]

        # Be sure the route server IPs are not taken into account.
        for rs_ip in (
            "206.83.43.1",
            "2001:504:9b::1"
        ):
            assert rs_ip not in [client["ip"] for client in clients]

        # Just to be sure the conversion worked, check some other IPs
        # which are expected to be imported as client.
        for member_ip in (
            "206.83.43.9",
            "2001:504:9b::9"
        ):
            assert member_ip in [client["ip"] for client in clients]

    def test_merge_clients_1(self):
        """Clients from Euro-IX: merge local custom clients, add missing client"""
        self._run("official_more_complex_example", ixp_id=42, vlan_id=0)
        clients = {"clients": self.clients}
        merge_clients(clients, open("tests/static/data/custom_clients_1.yml", "r"))

        assert "192.0.2.1" not in [client["ip"] for client in clients["clients"]]
        assert "192.0.2.2" not in [client["ip"] for client in clients["clients"]]
        assert "192.0.2.3" in [client["ip"] for client in clients["clients"]]

    def test_merge_clients_2(self):
        """Clients from Euro-IX: merge local custom clients, add/change settings"""
        self._run("official_more_complex_example", ixp_id=42, vlan_id=0)
        clients = {"clients": self.clients}

        # Test before merging.

        ip = "195.69.146.250"
        client = [client for client in clients["clients"] if client["ip"] == ip][0]
        assert client.get("password", None) is None

        ip = "2001:7f8:1::a500:2906:2"
        client = [client for client in clients["clients"] if client["ip"] == ip][0]
        assert client["cfg"]["filtering"]["irrdb"]["as_sets"] == ["AS-NFLX-V6"]

        ip = "195.69.147.250"
        client = [client for client in clients["clients"] if client["ip"] == ip][0]
        assert client["cfg"]["filtering"]["irrdb"]["as_sets"] == ["AS-NFLX-V4"]
        assert client["cfg"]["filtering"]["max_prefix"]["limit_ipv4"] == 42

        ip = "2001:7f8:1::a500:2906:1"
        client = [client for client in clients["clients"] if client["ip"] == ip][0]
        assert client.get("password", None) is None

        merge_clients(clients, open("tests/static/data/custom_clients_2.yml", "r"))

        # Test after merging.

        ip = "195.69.146.250"
        client = [client for client in clients["clients"] if client["ip"] == ip][0]
        assert client["password"] == "bgp_secret"

        # In custom_clients_2.yml, the client is reported with
        # an "exploded" IPv6 address, with zeroes, so a different
        # representation of the IP found in the Euro-IX JSON file.
        # This test aims to verify that during the merge IP addresses
        # are matched correctly, regardless of their textual
        # representation.
        ip = "2001:7f8:1::a500:2906:2"
        client = [client for client in clients["clients"] if client["ip"] == ip][0]
        assert client["password"] == "bgp_secret_3"

        ip = "195.69.147.250"
        client = [client for client in clients["clients"] if client["ip"] == ip][0]
        assert client["cfg"]["filtering"]["irrdb"]["as_sets"] == ["AS-TWO"]
        assert client["cfg"]["filtering"]["max_prefix"]["limit_ipv4"] == 42

        # In custom_clients_2.yml, the client is reported with
        # an uppercase IPv6 address, while the one that comes
        # from the Euro-IX JSON file is lower-case.
        # This test aims to verify that during the merge IP addresses
        # are matched correctly, regardless of their textual
        # representation.
        ip = "2001:7f8:1::a500:2906:1"
        client = [client for client in clients["clients"] if client["ip"] == ip][0]
        assert client["password"] == "bgp_secret_2"

        assert "192.0.2.3" in [client["ip"] for client in clients["clients"]]

        # Client that is added via the custom YML file.
        # The IP on that file is represented using the exploded
        # form. This verifies that the client is added correctly
        # using the normalised representation.
        ip = "2001:7f8:1::a500:2906:3"
        client = [client for client in clients["clients"] if client["ip"] == ip][0]
        assert client["asn"] == 4444

    def test_merge_clients_3(self):
        """Clients from Euro-IX: merge local custom clients, broken custom file 1"""
        self._run("official_more_complex_example", ixp_id=42, vlan_id=0)
        clients = {"clients": self.clients}

        with self.assertRaisesRegex(
            Exception,
            "Error while processing the client n. 1 from "
            "the set of clients to be merged: 'ip' not found"
        ):
            merge_clients(clients, open("tests/static/data/custom_clients_3.yml", "r"))

    def test_merge_clients_4(self):
        """Clients from Euro-IX: merge local custom clients, broken custom file 2"""
        self._run("official_more_complex_example", ixp_id=42, vlan_id=0)
        clients = {"clients": self.clients}

        with self.assertRaisesRegex(
            Exception,
            "Validation of the final clients file failed: "
            "check the logs for more details."
        ):
            merge_clients(clients, open("tests/static/data/custom_clients_4.yml", "r"))

    def test_merge_clients_5(self):
        """Clients from Euro-IX: merge local custom clients, broken custom file 3"""
        self._run("official_more_complex_example", ixp_id=42, vlan_id=0)
        clients = {"clients": self.clients}

        with self.assertRaisesRegex(
            Exception,
            "Error while processing the client n. 1 from "
            "the set of clients to be merged: "
            "client 2001:7f8:1::a500:2906:2 already exists in the "
            "original list of clients, but it's also reported in "
            "the set of clients to be merged with the 'add_if_missing' "
            "attribute set."
        ):
            merge_clients(clients, open("tests/static/data/custom_clients_5.yml", "r"))

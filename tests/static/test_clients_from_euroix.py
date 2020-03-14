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

import json
import os
import six
import unittest
import yaml

from pierky.arouteserver.euro_ix import EuroIXMemberList

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

        with six.assertRaisesRegex(self, Exception, "IXP ID 1 not found"):
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

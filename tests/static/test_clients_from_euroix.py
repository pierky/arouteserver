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
import os
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
        euro_ix = EuroIXMemberList(data)
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
            expected_result = yaml.load(f.read())

        self.assertEqual(res, expected_result)

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

        with self.assertRaisesRegexp(Exception, "IXP ID 1 not found"):
            self._run("official_more_complex_example", ixp_id=1)

        self._run("official_more_complex_example", ixp_id=42, vlan_id=1)
        self.assertEqual(len(self.clients), 0)

    def test_routeserver_only(self):
        """Clients from Euro-IX: --routeserver-only filter"""
        self._result_match_file("routeserver_only",
            ixp_id=42, routeserver_only=True)
        self._result_match_file("routeserver_only", "routeserver_only_no_flag",
            ixp_id=42)


# Copyright (C) 2017-2023 Pier Carlo Chiodi
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
import shutil
import tempfile
try:
    import mock
except ImportError:
    import unittest.mock as mock

from pierky.arouteserver.euro_ix import EuroIXMemberList
from pierky.arouteserver.commands import IXFMemberListFromClientsCommand
from pierky.arouteserver.tests.base import ARouteServerTestCase

class TestIXFMemberListFromClientsCommand(ARouteServerTestCase):

    NEED_TO_CAPTURE_LOG = True

    def _setUp(self, *patches):
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")

    def tearDown(self):
        mock.patch.stopall()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write_file(self, name, buff):
        path = os.path.join(self.temp_dir, name)
        with open(path, "w") as f:
            f.write(buff)
        return path

    def _test(self, clients_content, exp_res=None):
        cls = IXFMemberListFromClientsCommand

        dic = cls.build_json(
            self.write_file("clients.yml", clients_content),
            1, "Test IX", 1, 1
        )

        if exp_res:
            member_list = dic["member_list"]
            self.assertEqual(member_list, exp_res)

        # Test if the file generated can be read by ARouteServer itself
        with open(self.write_file("ixf.json", json.dumps(dic)), "rb") as f:
            clients_from_ixf_member_list = EuroIXMemberList(f, None, None)

        clients_from_ixf_member_list.get_clients(1, 1)

        return dic

    def test_1(self):
        """IX-F Member Export from clients command: simple"""
        self._test(
            "\n".join([
                "clients:",
                "  - asn: 1",
                "    ip: 192.0.2.1"
            ]),
            [
                { "asnum": 1,
                  "connection_list": [
                      { "ixp_id": 1, "vlan_list": [
                            { "vlan_id": 1,
                              "ipv4": {
                                  "address": "192.0.2.1",
                                  "routeserver": True
                              }
                            }
                        ] }
                    ] }
            ] )

    def test_2(self):
        """IX-F Member Export from clients command: with description"""
        self._test(
            "\n".join([
                "clients:",
                "  - asn: 1",
                "    ip: 192.0.2.1",
                "    description: Test"
            ]),
            [
                { "asnum": 1, "name": "Test",
                  "connection_list": [
                      { "ixp_id": 1, "vlan_list": [
                            { "vlan_id": 1,
                              "ipv4": {
                                  "address": "192.0.2.1",
                                  "routeserver": True
                              }
                            }
                        ] }
                    ] }
            ] )

    def test_3(self):
        """IX-F Member Export from clients command: with AS-SET"""
        self._test(
            "\n".join([
                "clients:",
                "  - asn: 1",
                "    ip: 192.0.2.1",
                "    cfg:",
                "      filtering:",
                "        irrdb:",
                "          as_sets:",
                "            - AS-ONE"
            ]),
            [
                { "asnum": 1,
                  "connection_list": [
                      { "ixp_id": 1, "vlan_list": [
                            { "vlan_id": 1,
                              "ipv4": { "address": "192.0.2.1",
                                        "as_macro": "AS-ONE",
                                        "routeserver": True }
                            }
                        ] }
                    ] }
            ] )

    def test_4(self):
        """IX-F Member Export from clients command: with 2 AS-SETs"""
        self._test(
            "\n".join([
                "clients:",
                "  - asn: 1",
                "    ip: 192.0.2.1",
                "    cfg:",
                "      filtering:",
                "        irrdb:",
                "          as_sets:",
                "            - AS-ONE",
                "            - AS-TWO"
            ]),
            [
                { "asnum": 1,
                  "connection_list": [
                      { "ixp_id": 1, "vlan_list": [
                            { "vlan_id": 1,
                              "ipv4": { "address": "192.0.2.1",
                                        "as_macro": "AS-ONE",
                                        "routeserver": True }
                            }
                        ] }
                    ] }
            ] )

        found = False
        for msg in self.logger_handler.warnings:
            if "only the first one (AS-ONE) will be exported" in msg:
                found = True
        if not found:
            self.fail("More than one AS-SET warning expected.")

    def test_5(self):
        """IX-F Member Export from clients command: AS-SET from asns"""
        self._test(
            "\n".join([
                "asns:",
                "  AS1:",
                "    as_sets:",
                "      - AS-ONE",
                "clients:",
                "  - asn: 1",
                "    ip: 192.0.2.1"
            ]),
            [
                { "asnum": 1,
                  "connection_list": [
                      { "ixp_id": 1, "vlan_list": [
                            { "vlan_id": 1,
                              "ipv4": { "address": "192.0.2.1",
                                        "as_macro": "AS-ONE",
                                        "routeserver": True }
                            }
                        ] }
                    ] }
            ] )

    def test_6(self):
        """IX-F Member Export from clients command: more than one IP"""
        self._test(
            "\n".join([
                "asns:",
                "  AS1:",
                "    as_sets:",
                "      - AS-ONE",
                "clients:",
                "  - asn: 1",
                "    description: NetOne",
                "    ip:",
                "      - 192.0.2.1",
                "      - 192.0.2.2",
                "      - 2001:db8::1",
                "      - 2001:db8::2",
                "    cfg:",
                "      filtering:",
                "        max_prefix:",
                "          limit_ipv4: 4",
                "          limit_ipv6: 6"
            ]),
            [
                { "asnum": 1, "name": "NetOne",
                  "connection_list": [
                      { "ixp_id": 1, "vlan_list": [
                            { "vlan_id": 1,
                              "ipv4": { "address": "192.0.2.1",
                                        "as_macro": "AS-ONE", "max_prefix": 4,
                                        "routeserver": True }
                            },
                            { "vlan_id": 1,
                              "ipv4": { "address": "192.0.2.2",
                                        "as_macro": "AS-ONE", "max_prefix": 4,
                                        "routeserver": True }
                            },
                            { "vlan_id": 1,
                              "ipv6": { "address": "2001:db8::1",
                                        "as_macro": "AS-ONE", "max_prefix": 6,
                                        "routeserver": True }
                            },
                            { "vlan_id": 1,
                              "ipv6": { "address": "2001:db8::2",
                                        "as_macro": "AS-ONE", "max_prefix": 6,
                                        "routeserver": True }
                            }
                        ] }
                    ] }
            ] )

    def test_real_clients_ams_ix(self):
        """IX-F Member Export from clients command: ams-ix.yml"""
        with open("tests/real/clients/ams-ix.yml", "r") as f:
            self._test(f.read())

    def test_real_clients_bcix(self):
        """IX-F Member Export from clients command: bcix.yml"""
        with open("tests/real/clients/bcix.yml", "r") as f:
            self._test(f.read())

    def test_real_clients_gr_ix(self):
        """IX-F Member Export from clients command: gr_ix.yml"""
        with open("tests/real/clients/gr-ix.yml", "r") as f:
            self._test(f.read())

    def test_real_clients_inex(self):
        """IX-F Member Export from clients command: inex.yml"""
        with open("tests/real/clients/inex.yml", "r") as f:
            self._test(f.read())

    def test_real_clients_lonap(self):
        """IX-F Member Export from clients command: lonap.yml"""
        with open("tests/real/clients/lonap.yml", "r") as f:
            self._test(f.read())

    def test_real_clients_six(self):
        """IX-F Member Export from clients command: six.yml"""
        with open("tests/real/clients/six.yml", "r") as f:
            self._test(f.read())

    def test_real_clients_sthix(self):
        """IX-F Member Export from clients command: sthix.yml"""
        with open("tests/real/clients/sthix.yml", "r") as f:
            self._test(f.read())

    def test_real_clients_swissix(self):
        """IX-F Member Export from clients command: swissix.yml"""
        with open("tests/real/clients/swissix.yml", "r") as f:
            self._test(f.read())

# Copyright (C) 2017-2022 Pier Carlo Chiodi
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

import copy
import os
import shutil
import tempfile
import unittest
import yaml

from pierky.arouteserver.builder import IRRASSetBuilder
from pierky.arouteserver.tests.mocked_env import MockedEnv

class TestIRRASSetCommand(unittest.TestCase):

    GENERAL_SIMPLE = {
        "cfg": {
            "rs_as": 999,
            "router_id": "192.0.2.2",
            "filtering": {
                "irrdb": {
                    "peering_db": True
                }
            }
        }
    }
    CLIENTS_SIMPLE = {
        "clients": [
            { "asn": 1, "ip": "192.0.2.11" },
            { "asn": 2, "ip": ["192.0.2.21", "2001:db8::2:1"] }
        ]
    }

    def setup_builder(self, general, clients, ip_ver=4):
        self.builder = IRRASSetBuilder(
            template_dir="templates/irr-as-set/",
            template_name="plain_rpsl.j2",
            cfg_general=self.write_file("general.yml", general),
            cfg_clients=self.write_file("clients.yml", clients),
            cfg_bogons="config.d/bogons.yml",
            cache_dir=self.temp_dir,
            cache_expiry=120,
            ip_ver=ip_ver
        )

    def setUp(self, *patches):
        MockedEnv(base_dir=os.path.dirname(__file__), default=False, irr=True, peering_db=True)
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")

    def tearDown(self):
        MockedEnv.stopall()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write_file(self, name, dic):
        path = os.path.join(self.temp_dir, name)
        with open(path, "w") as f:
            yaml.dump(dic, f, default_flow_style=False)
        return path

    def test_010_as1_as2(self, *patches):
        """IRR AS-SET command: AS1 with AS-AS1 and AS2"""
        self.setup_builder(self.GENERAL_SIMPLE, self.CLIENTS_SIMPLE)
        self.builder.render_template()

        # AS1 is present in PeeringDB and has AS-AS1 listed
        # as its IRR record.
        # AS2 is also present in PeeringDB but without the
        # IRR record.

        self.assertEqual(
            sorted(self.builder.data["as_sets_rpsl_objects"]),
            sorted(["AS1", "AS-AS1", "AS2"])
        )

    def test_010_as_one_as_two(self, *patches):
        """IRR AS-SET command: explicit AS-SETs from config, no PeeringDB record"""
        clients = copy.deepcopy(self.CLIENTS_SIMPLE)
        clients["clients"][0]["cfg"] = {"filtering": {"irrdb": {"as_sets": ["AS-ONE"]}}}
        clients["clients"][1]["cfg"] = {"filtering": {"irrdb": {"as_sets": ["AS-TWO"]}}}

        self.setup_builder(self.GENERAL_SIMPLE, clients)
        self.builder.render_template()

        # AS1 has its own AS-SET configured at client level;
        # the record from PeeringDB is ignored.

        self.assertEqual(
            sorted(self.builder.data["as_sets_rpsl_objects"]),
            sorted(["AS1", "AS-ONE", "AS2", "AS-TWO"])
        )

    def test_010_white_list(self, *patches):
        """IRR AS-SET command: whitelist and PeeringDB"""
        clients = copy.deepcopy(self.CLIENTS_SIMPLE)
        clients["clients"][0]["cfg"] = {"filtering": {"irrdb": {"white_list_asn": [11]}}}

        clients["clients"][1]["cfg"] = {"filtering": {"irrdb": {"white_list_asn": [21]}}}

        self.setup_builder(self.GENERAL_SIMPLE, clients)
        self.builder.render_template()

        # AS1 is present in PeeringDB and has AS-AS1 listed
        # as its IRR record. The PeeringDB AS-SET is used and
        # also the white-listed ASN added.

        self.assertEqual(
            sorted(self.builder.data["as_sets_rpsl_objects"]),
            sorted(["AS1", "AS-AS1", "AS11", "AS2", "AS21"])
        )

    def test_010_asns(self, *patches):
        """IRR AS-SET command: AS-SET from asns"""
        clients = copy.deepcopy(self.CLIENTS_SIMPLE)
        clients["asns"] = {
            "AS1": {
                "as_sets": ["AS-ONE"]
            },
            "AS2": {
                "as_sets": ["AS-TWO"]
            }
        }

        self.setup_builder(self.GENERAL_SIMPLE, clients)
        self.builder.render_template()

        # AS1 is present in PeeringDB, but the PeeringDB
        # record is not used because the AS-SET from the
        # 'asns' has higher priority.

        self.assertEqual(
            sorted(self.builder.data["as_sets_rpsl_objects"]),
            sorted(["AS1", "AS-ONE", "AS2", "AS-TWO"])
        )

    def test_010_ipv6(self, *patches):
        """IRR AS-SET command: IPv6 clients only"""
        clients = copy.deepcopy(self.CLIENTS_SIMPLE)

        self.setup_builder(self.GENERAL_SIMPLE, clients, ip_ver=6)
        self.builder.render_template()

        # AS1 is not included since it has no v6 clients.

        self.assertEqual(
            sorted(self.builder.data["as_sets_rpsl_objects"]),
            sorted(["AS2"])
        )

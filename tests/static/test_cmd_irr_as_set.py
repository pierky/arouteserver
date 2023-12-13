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

    def setup_builder(self, general, clients, ip_ver=4, template_path=None,
                      include_members=None, exclude_members=None):
        if template_path:
            template_dir = os.path.dirname(template_path)
            template_name = os.path.basename(template_path)
        else:
            template_dir = "templates/irr-as-set/"
            template_name = "plain_rpsl.j2"

        self.builder = IRRASSetBuilder(
            template_dir=template_dir,
            template_name=template_name,
            cfg_general=self.write_file("general.yml", general),
            cfg_clients=self.write_file("clients.yml", clients),
            cfg_bogons="config.d/bogons.yml",
            cache_dir=self.temp_dir,
            cache_expiry=120,
            ip_ver=ip_ver,
            include_members=include_members,
            exclude_members=exclude_members
        )

    def setUp(self, *patches):
        MockedEnv(base_dir=os.path.dirname(__file__), default=False, irr=True, peering_db=True)
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")

    def tearDown(self):
        MockedEnv.stopall()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write_file(self, name, content):
        path = os.path.join(self.temp_dir, name)
        with open(path, "w") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                yaml.dump(content, f, default_flow_style=False)
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

    def test_010_get_as_set_info_1(self):
        """IRR AS-SET command: normalise ipv4:RADB::AS-ONE"""
        self.assertEqual(
            IRRASSetBuilder._get_as_set_info("ipv4:RADB::AS-ONE"),
            ("RADB", "AS-ONE")
        )

    def test_010_get_as_set_info_2(self):
        """IRR AS-SET command: normalise RADB::AS-ONE"""
        self.assertEqual(
            IRRASSetBuilder._get_as_set_info("RADB::AS-ONE"),
            ("RADB", "AS-ONE")
        )

    def test_010_get_as_set_info_3(self):
        """IRR AS-SET command: normalise AS-ONE@RADB"""
        self.assertEqual(
            IRRASSetBuilder._get_as_set_info("AS-ONE@RADB"),
            ("RADB", "AS-ONE")
        )

    def test_010_get_as_set_info_4(self):
        """IRR AS-SET command: normalise RADB:AS-ONE"""
        self.assertEqual(
            IRRASSetBuilder._get_as_set_info("RADB:AS-ONE"),
            ("RADB", "AS-ONE")
        )

    def test_010_get_as_set_info_5(self):
        """IRR AS-SET command: normalise AS123:AS-ONE"""
        self.assertEqual(
            IRRASSetBuilder._get_as_set_info("AS123:AS-ONE"),
            (None, "AS123:AS-ONE")
        )

    def test_010_get_as_set_info_6(self):
        """IRR AS-SET command: normalise RADB::AS123:AS-ONE"""
        self.assertEqual(
            IRRASSetBuilder._get_as_set_info("RADB::AS123:AS-ONE"),
            ("RADB", "AS123:AS-ONE")
        )

    def test_010_get_as_set_info_7(self):
        """IRR AS-SET command: normalise RADB:AS123:AS-ONE"""
        self.assertEqual(
            IRRASSetBuilder._get_as_set_info("RADB:AS123:AS-ONE"),
            ("RADB", "AS123:AS-ONE")
        )

    def test_010_get_as_set_info_no_source(self):
        """IRR AS-SET command: normalise AS-ONE"""
        self.assertEqual(
            IRRASSetBuilder._get_as_set_info("AS-ONE"),
            (None, "AS-ONE")
        )

    def test_010_get_valid_as_sets(self):
        """IRR AS-SET command: filter AS-SETs on the basis of source"""
        TEMPLATE = "\n".join([
            "aa: 1",
            "bb: 2",
            "source: RADB"
        ])

        self.setup_builder(self.GENERAL_SIMPLE, self.CLIENTS_SIMPLE,
                           template_path=self.write_file("template.txt", TEMPLATE))
        self.assertEqual(
            self.builder._get_valid_as_sets([
                "AS-ONE",
                "RADB::AS-TWO",
                "ARIN::AS-THREE",
                "AS-FOUR@RADB",
                "APNIC:AS-FIVE",
                "AS123:AS-FOO",
                "RADB::AS456:AS-FOO",
                "ARIN::AS789:AS-FOO"
            ]),
            ["AS-ONE", "AS-TWO", "AS-FOUR", "AS123:AS-FOO", "AS456:AS-FOO"]
        )

    def test_010_get_valid_as_sets_include(self):
        """IRR AS-SET command: include-members"""

        # Same as test_010_as1_as2, but with include/exclude members.

        self.setup_builder(self.GENERAL_SIMPLE, self.CLIENTS_SIMPLE,
                           include_members="ARIN::AS-THREE,APNIC:AS-FIVE",
                           exclude_members="AS-AS1")
        self.builder.render_template()

        self.assertEqual(
            sorted(self.builder.data["as_sets_rpsl_objects"]),
            sorted(["AS1", "AS2", "ARIN::AS-THREE", "APNIC:AS-FIVE"])
        )

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

import os

from pierky.arouteserver.tests.base import ARouteServerTestCase
from pierky.arouteserver.config.general import ConfigParserGeneral


class TestYAMLInclude(ARouteServerTestCase):

    SHORT_DESCR = "YAML !include"

    def test_include1(self):
        """{}: general config, 1 !include statement"""

        cfg = ConfigParserGeneral()
        cfg.file_dir = os.path.dirname(__file__)
        cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  !include yaml_include1.yml\n"
        )
        cfg.parse()
        self.assertEqual(cfg["blackhole_filtering"]["policy_ipv6"], "propagate-unchanged")

    def test_include2(self):
        """{}: general config, 2 !include statements"""

        cfg = ConfigParserGeneral()
        cfg.file_dir = os.path.dirname(__file__)
        cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  !include yaml_include1.yml\n"
            "  !include yaml_include2.yml\n"
        )
        cfg.parse()
        self.assertEqual(cfg["blackhole_filtering"]["policy_ipv6"], "propagate-unchanged")
        self.assertEqual(cfg["filtering"]["next_hop"]["policy"], "same-as")

    def test_include2_2levels(self):
        """{}: general config, 3 !include statements, 2 levels"""

        cfg = ConfigParserGeneral()
        cfg.file_dir = os.path.dirname(__file__)
        cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  !include yaml_include1.yml\n"
            "  !include yaml_include2.yml\n"
            "  !include yaml_include3.yml\n"
        )
        cfg.parse()
        self.assertEqual(cfg["blackhole_filtering"]["policy_ipv6"], "propagate-unchanged")
        self.assertEqual(cfg["filtering"]["next_hop"]["policy"], "same-as")
        self.assertEqual(cfg["filtering"]["ipv4_pref_len"]["min"], 1)
        self.assertEqual(cfg["filtering"]["ipv4_pref_len"]["max"], 2)
        self.assertEqual(cfg["filtering"]["ipv6_pref_len"]["min"], 1)
        self.assertEqual(cfg["filtering"]["ipv6_pref_len"]["max"], 2)

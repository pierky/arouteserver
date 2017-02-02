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

import unittest

import yaml

from .cfg_base import TestConfigParserBase 
from pierky.arouteserver.config.asns import ConfigParserASNS


class TestConfigParserASNs(TestConfigParserBase):

    FILE_PATH = "config.d/clients.yml"
    CONFIG_PARSER_CLASS = ConfigParserASNS
    SHORT_DESCR = "ASNs config parser"

    def test_valid_cfg(self):
        """{}: valid configuration"""
        self._contains_err()
        self.assertEqual(self.cfg["AS10745"]["as_sets"], None)
        self.assertEqual(self.cfg["AS3333"]["as_sets"], None)

    def test_invalid_as(self):
        """{}: invalid AS"""
        cfg = "\n".join([
            "asns:",
            "  as123:"
        ])
        self.load_config(yaml=cfg)
        self._contains_err("Invalid ASN format in 'asns' section for 'as123':")

        cfg = "\n".join([
            "asns:",
            "  AS_123:"
        ])
        self.load_config(yaml=cfg)
        self._contains_err("Invalid ASN format in 'asns' section for 'AS_123':")

        cfg = "\n".join([
            "asns:",
            "  AS:"
        ])
        self.load_config(yaml=cfg)
        self._contains_err("Invalid ASN format in 'asns' section for 'AS':")

    def test_valid_asset(self):
        """{}: valid AS-SET"""
        cfg = "\n".join([
            "asns:",
            "  AS123:",
            "    as_sets:",
            "      - 'AS-AS123'"  
        ])
        self.load_config(yaml=cfg)
        self._contains_err()

        cfg = "\n".join([
            "asns:",
            "  AS123:",
            "    as_sets:",
            "      - 'AS-AS123'",
            "      - 'AS-AS456'"
        ])
        self.load_config(yaml=cfg)
        self._contains_err()
        self.assertEqual(self.cfg["AS123"]["as_sets"][0], "AS-AS123")

    def test_invalid_asset(self):
        """{}: invalid AS-SET"""
        cfg = "\n".join([
            "asns:",
            "  AS123:",
            "    as_sets:",
            "      a: 'AS-AS123'"  
        ])
        self.load_config(yaml=cfg)
        self._contains_err("Error parsing 'as_sets' at 'asns' level - Invalid format: must be a list.")

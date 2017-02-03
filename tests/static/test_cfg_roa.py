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

from .cfg_base import TestConfigParserBase 
from pierky.arouteserver.config.roa import ConfigParserROAEntries


class TestConfigParserROA(TestConfigParserBase):

    FILE_PATH = "tests/static/test_cfg_roa_entries.yml"
    CONFIG_PARSER_CLASS = ConfigParserROAEntries
    SHORT_DESCR = "ROAs entries config parser"

    def test_valid_cfg(self):
        """{}: valid configuration"""
        self._contains_err()

    def test_unknown_statement(self):
        """{}: unknown statement"""
        self.cfg[0]["test"] = 1
        self._contains_err("Error in ROAs definition: Unknown statement 'test' in ROA entry definition.")

    def test_valid_roas(self):
        """{}: valid ROA entries"""
        roa = self.cfg[0]
        self.assertEqual(roa["asn"], 1)
        self.assertEqual(roa["prefix"]["prefix"], "10.0.1.0")
        self.assertEqual(roa["prefix"]["length"], 24)
        self.assertEqual(roa["prefix"]["exact"], True)

        roa = self.cfg[1]
        self.assertEqual(roa["asn"], 2)
        self.assertEqual(roa["prefix"]["prefix"], "10.1.0.0")
        self.assertEqual(roa["prefix"]["length"], 16)
        self.assertEqual(roa["prefix"]["le"], 24)
        self.assertEqual(roa["prefix"]["exact"], False)

        roa = self.cfg[2]
        self.assertEqual(roa["asn"], 3)
        self.assertEqual(roa["prefix"]["prefix"], "10.2.0.0")
        self.assertEqual(roa["prefix"]["length"], 24)
        self.assertEqual(roa["prefix"]["exact"], True)

    def test_invalid_ge(self):
        """{}: invalid ge"""
	cfg = [
            "roas:",
	    "- prefix:",
            "    prefix: 10.0.1.0",
            "    length: 24",
            "    ge: 25",
            "  asn: 1"
        ]
        self.cfg._load_from_yaml("\n".join(cfg))
        self._contains_err("Error in ROAs definition: ROA prefix 'ge' must be equal to the prefix length: 25 != 24 for prefix 10.0.1.0.")

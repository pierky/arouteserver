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
from pierky.arouteserver.config.bogons import ConfigParserBogons


class TestConfigParserBogons(TestConfigParserBase):

    FILE_PATH = "config.d/bogons.yml"
    CONFIG_PARSER_CLASS = ConfigParserBogons

    def test_valid_cfg(self):
        """Bogons config parser: valid configuration"""
        self._contains_err()

    def test_unknown_statement(self):
        """Bogons config parser: unknown statement"""
        self.cfg[0]["test"] = 1
        self._contains_err("Error in bogon definition: Unknown statement 'test' in prefix list entry definition.")

    def test_missing_statement(self):
        """Bogons config parser: missing statement"""
        del self.cfg[0]["prefix"]
        self._contains_err("Error in bogon definition: Missing 'prefix' in prefix list entry.")
        self.cfg[0]["prefix"] = "192.168.0.0"
        self._contains_err()

    def test_invalid_ipv4_id(self):
        """Bogons config parser: invalid IPv4 prefix ID"""
        self.cfg[0]["prefix"] = "1000.0.0.1"
        self._contains_err("Error in bogon definition: Invalid prefix ID: 1000.0.0.1.")

    def test_invalid_len_ipv4(self):
        """Bogons config parser: invalid IPv4 prefix len"""
        self.cfg[0]["prefix"] = "192.0.2.0"
        for l in (-1, 33):
            self.cfg[0]["length"] = l
            self._contains_err("Invalid prefix length: {}".format(l))

    def test_invalid_ipv6_id(self):
        """Bogons config parser: invalid IPv6 prefix ID"""
        self.cfg[0]["prefix"] = "fe80::1Z"
        self._contains_err("Invalid prefix ID: fe80::1Z")

    def test_invalid_len_ipv6(self):
        """Bogons config parser: invalid IPv6 prefix len"""
        self.cfg[0]["prefix"] = "fe80::1"
        for l in (-1, 129):
            self.cfg[0]["length"] = l
            self._contains_err("Invalid prefix length: {}".format(l))

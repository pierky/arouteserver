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

from pierky.arouteserver.config.validators import ValidatorPrefixListEntry
from pierky.arouteserver.errors import ConfigError


class TestPrefixList(unittest.TestCase):

    def _exp_err(self, exp_err=None):
        if not exp_err:
            self._exp_ok()
            return
        try:
            ValidatorPrefixListEntry().validate(self.v)
        except ConfigError as e:
            if not exp_err in str(e):
                self.fail("Expected '{}', received '{}'".format(exp_err, str(e)))

    def _exp_ok(self):
        try:
            ValidatorPrefixListEntry().validate(self.v)
        except ConfigError as e:
            self.fail("Expected success, received '{}'".format(str(e)))

    def _match(self, prefix, len, exact, ge, le, comment):
        ValidatorPrefixListEntry().validate(self.v)
        self.assertEqual(self.v["prefix"], prefix)
        self.assertEqual(self.v["length"], len)
        self.assertEqual(self.v["exact"], exact)
        self.assertEqual(self.v["le"], le)
        self.assertEqual(self.v["ge"], ge)
        self.assertEqual(self.v["comment"], comment)

    def test_bad_prefixes(self):
        """Prefix list parser: bad prefix list entries"""
        self.v = {
            "a": 1
        }
        self._exp_err("Unknown statement 'a' in prefix list entry definition")

        self.v = {
            "prefix": "192.168.0.0"
        }
        self._exp_err("Missing 'length' in prefix list entry")

        self.v["length"] = 33
        self._exp_err("Invalid prefix length: 33")

        self.v = {
            "prefix": "192.168.0.0/24",
            "length": 24
        }
        self._exp_err("Invalid prefix ID: 192.168.0.0/24")

        self.v = {
            "prefix": "2001:db8::",
            "length": -1
        }
        self._exp_err("Invalid prefix length: -1")
        self.v["length"] = 129
        self._exp_err("Invalid prefix length: 129")

    def test_bad_prefix_le_ge(self):
        """Prefix list parser: bad 'le' and 'ge'"""
        self.v = {
            "prefix": "192.168.0.0",
            "length": 16
        }
        self.v["ge"] = 15
        self._exp_err("'ge' (15) must be greater than or equal to the prefix-len (16)")

        self.v["ge"] = 24
        self.v["le"] = 33
        self._exp_err("'le' (33) must be less than or equal to the max prefix-len (32)")

        self.v["ge"] = 30
        self.v["le"] = 24
        self._exp_err("'ge' must be less than or equal to 'le'")

        self.v["ge"] = 24
        self.v["le"] = 30
        self.v["exact"] = True
        self._exp_err("Can't set 'ge' and 'le' when 'exact' is True")

    def test_valid_prefixes(self):
        """Prefix list parser: valid prefix list entries"""

        self.v = {
            "prefix": "192.168.0.0",
            "length": 16
        }
        self._match("192.168.0.0", 16, False, None, None, None)

        self.v["comment"] = "test"
        self._match("192.168.0.0", 16, False, None, None, "test")

        self.v["exact"] = True
        self._match("192.168.0.0", 16, True, None, None, "test")
        
        self.v["exact"] = False

        self.v["ge"] = "24"
        self._match("192.168.0.0", 16, False, 24, None, "test")

        self.v["le"] = "24"
        self._match("192.168.0.0", 16, False, 24, 24, "test")

        self.v["le"] = "30"
        self._match("192.168.0.0", 16, False, 24, 30, "test")

        self.v["ge"] = 16
        self.v["le"] = 16
        self._match("192.168.0.0", 16, False, 16, 16, "test")

        self.v["ge"] = 32
        self.v["le"] = 32
        self._match("192.168.0.0", 16, False, 32, 32, "test")

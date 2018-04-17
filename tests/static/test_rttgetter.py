# Copyright (C) 2017-2018 Pier Carlo Chiodi
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

import six
import unittest

from pierky.arouteserver.enrichers.rtt import RTTGetter_WorkerThread


class TestRTTGetterParser(unittest.TestCase):

    def _parse(self, raw, exp_result=None, exp_failure=None):
        if exp_failure:
            with six.assertRaisesRegex(self, Exception, exp_failure):
                res = RTTGetter_WorkerThread._parse_result(raw)
        else:
            res = RTTGetter_WorkerThread._parse_result(raw)
            if exp_result is None:
                self.assertIs(res, None)
            else:
                self.assertEqual(res, exp_result)

    def test_None(self):
        """RTT getter parser: None"""
        self._parse("None", None)

    def test_none(self):
        """RTT getter parser: none"""
        self._parse("none", None)

    def test_empty(self):
        """RTT getter parser: empty"""
        self._parse("", exp_failure="no value returned")

    def test_blanks_only(self):
        """RTT getter parser: blanks only"""
        self._parse("   ", exp_failure="empty value returned")

    def test_new_line_only(self):
        """RTT getter parser: new line only"""
        self._parse("\n", exp_failure="empty value returned")

    def test_1(self):
        """RTT getter parser: 1"""
        self._parse("1", 1)

    def test_0(self):
        """RTT getter parser: 0"""
        self._parse("0", 0)

    def test_0_1(self):
        """RTT getter parser: 0.1"""
        self._parse("0.1", 0.1)

    def test_1_0(self):
        """RTT getter parser: 1.0"""
        self._parse("1.0", 1)

    def test_123_456(self):
        """RTT getter parser: 123.456"""
        self._parse("123.456", 123.456)

    def test_123_456_789(self):
        """RTT getter parser: 123.456.789"""
        self._parse("123.456.789", exp_failure="invalid value")

    def test_None_new_line_1(self):
        """RTT getter parser: None\\n1"""
        self._parse("None\n1", None)

    def test_123_comma_456(self):
        """RTT getter parser: 123,456"""
        self._parse("123,456", exp_failure="invalid value")


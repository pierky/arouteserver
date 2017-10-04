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

import os
try:
    import mock
except ImportError:
    import unittest.mock as mock
import unittest

from pierky.arouteserver.peering_db import PeeringDBNet
from pierky.arouteserver.errors import PeeringDBNoInfoError 
from pierky.arouteserver.tests.mock_peeringdb import mock_peering_db


class TestPeeringDBInfo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        mock_peering_db(os.path.dirname(__file__) + "/peeringdb_data")

    @classmethod
    def tearDownClass(cls):
        mock.patch.stopall()

    def test_net1(self):
        """PeeringDB network: get data"""
        net = PeeringDBNet(1)
        net.load_data()
        self.assertEqual(net.info_prefixes4, 20)
        self.assertEqual(net.info_prefixes6, 10)

    def test_no_data(self):
        """PeeringDB network: missing data"""
        net = PeeringDBNet(2)
        with self.assertRaises(PeeringDBNoInfoError):
            net.load_data()

    def test_parse_as_sets(self):
        """PeeringDB: AS-SETs parsing"""
        net = PeeringDBNet(1)
        net.load_data()
        self.assertEqual(net.parse_as_sets("AS-1"), ["AS-1"])
        self.assertEqual(net.parse_as_sets("AS-1, AS-2, AA:BB"), ["AS-1", "AS-2"])
        self.assertEqual(net.parse_as_sets("AS-1 / AS-2\nAS-3"), ["AS-1", "AS-2", "AS-3"])
        self.assertEqual(net.parse_as_sets("AS-"), [])
        self.assertEqual(net.parse_as_sets("AS-A_BB, as-b"), ["AS-A_BB", "AS-B"])
        self.assertEqual(net.parse_as_sets("AA-B"), [])
        self.assertEqual(net.parse_as_sets("AA:AS-BB"), [])
        self.assertEqual(net.parse_as_sets("AS:AS-BB"), [])
        self.assertEqual(net.parse_as_sets("AS1:AS-BB"), ["AS1:AS-BB"])
        self.assertEqual(net.parse_as_sets("AS1"), [])
        self.assertEqual(net.parse_as_sets("RIPE:AS-B"), [])
        self.assertEqual(net.parse_as_sets("RIPE::AS-B"), ["AS-B"])
        self.assertEqual(net.parse_as_sets("RIPE: AS-B"), ["AS-B"])
        self.assertEqual(net.parse_as_sets("RIPE: AS1:AS-B:AS2, ARIN: AS1:AS-1-CUST"), ["AS1:AS-B:AS2", "AS1:AS-1-CUST"])
        self.assertEqual(net.parse_as_sets("ipv4:AS-B"), ["AS-B"])
        self.assertEqual(net.parse_as_sets("ripe: AS-A, RaDB: AS-ONE"), ["AS-A", "AS-ONE"])

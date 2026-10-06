# Copyright (C) 2017-2026 Pier Carlo Chiodi
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
import unittest

from pierky.arouteserver.tests.mocked_env import MockedEnv
from pierky.arouteserver.peering_db import PeeringDBNet
from pierky.arouteserver.errors import PeeringDBNoInfoError 


class TestPeeringDBInfo(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        MockedEnv(default=False, peering_db=True,
                  base_dir=os.path.dirname(__file__))

    @classmethod
    def tearDownClass(cls):
        MockedEnv.stopall()

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

    def test_rtbh_community(self):
        """PeeringDB network: RTBH community"""
        # Attribute not set: PeeringDB omits it.
        net = PeeringDBNet(1)
        net.load_data()
        self.assertIsNone(net.rtbh_community)

        net = PeeringDBNet(4)
        net.load_data()
        self.assertEqual(net.rtbh_community, {"std": "65000:666", "lrg": None})

        net = PeeringDBNet(5)
        net.load_data()
        self.assertEqual(net.rtbh_community, {"std": None, "lrg": "5:666:0"})

        # Lists are not accepted.
        net = PeeringDBNet(6)
        net.load_data()
        self.assertIsNone(net.rtbh_community)

    def test_parse_rtbh_community(self):
        """PeeringDB: RTBH community parsing"""
        net = PeeringDBNet(1)
        self.assertEqual(net.parse_rtbh_community("65535:666"), {"std": "65535:666", "lrg": None})
        self.assertEqual(net.parse_rtbh_community(" 0:0 "), {"std": "0:0", "lrg": None})
        self.assertEqual(net.parse_rtbh_community("4294967295:0:4294967295"), {"std": None, "lrg": "4294967295:0:4294967295"})
        self.assertEqual(net.parse_rtbh_community("0065000:00:0666"), {"std": None, "lrg": "65000:0:666"})
        for v in (None, "", "   ", 666, "666", "65536:666", "1:-1", "a:b",
                  "4294967296:0:0", "1:2:3:4", "rt:1:666", "1:666,2:666",
                  "1:666 2:666", "rs_as:666", "peer_as:666", "1:dyn_val"):
            self.assertIsNone(net.parse_rtbh_community(v), v)

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
        self.assertEqual(net.parse_as_sets("AS1"), ["AS1"])
        self.assertEqual(net.parse_as_sets("RIPE:AS-B"), ["RIPE::AS-B"])
        self.assertEqual(net.parse_as_sets("UNKNOWNSOURCE:AS-B"), [])
        self.assertEqual(net.parse_as_sets("UNKNOWNSOURCE::AS-B"), ["UNKNOWNSOURCE::AS-B"])
        self.assertEqual(net.parse_as_sets("RIPE::AS-B"), ["RIPE::AS-B"])
        self.assertEqual(net.parse_as_sets("RIPE: AS-B"), ["AS-B"])
        self.assertEqual(net.parse_as_sets("RIPE: AS1:AS-B:AS2, ARIN: AS1:AS-1-CUST"), ["AS1:AS-B:AS2", "AS1:AS-1-CUST"])
        self.assertEqual(net.parse_as_sets("ipv4:AS-B"), ["AS-B"])
        self.assertEqual(net.parse_as_sets("ipv4:RIPE::AS-B"), ["RIPE::AS-B"])
        self.assertEqual(net.parse_as_sets("ripe: AS-A, RaDB: AS-ONE"), ["AS-A", "AS-ONE"])
        self.assertEqual(net.parse_as_sets("AS-ONE@RIPE"), ["RIPE::AS-ONE"])
        self.assertEqual(net.parse_as_sets("RIPE::AS-ONE@RIPE"), [])
        self.assertEqual(net.parse_as_sets("RIPE:AS-ONE@RIPE"), [])
        self.assertEqual(net.parse_as_sets("RIPE: AS-ONE@RIPE"), ["RIPE::AS-ONE"])
        self.assertEqual(net.parse_as_sets("AS-ONE@TWO@RIPE"), [])

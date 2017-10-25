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


from pierky.arouteserver.enrichers.pdb_max_prefix import PeeringDBConfigEnricher_MaxPrefix_WorkerThread


class TestPDB_Max_Prefix(unittest.TestCase):

    @staticmethod
    def _calc_limit(incr_abs, incr_rel, pdb_value):
        client = {"cfg": {"filtering": {"max_prefix": {"peering_db": {
            "increment": {
                "absolute": incr_abs,
                "relative": incr_rel
            }
        }}}}}
        PeeringDBConfigEnricher_MaxPrefix_WorkerThread._set_client_max_prefix_from_pdb(
            client, 4, pdb_value
        )
        return client["cfg"]["filtering"]["max_prefix"]["limit_ipv4"]

    def test_010_as_set_bundle1(self):
        """Max-prefix from PeeringDB: increment"""
        self.assertEqual(self._calc_limit(100, 15, 9), 125)    # 125.35
        self.assertEqual(self._calc_limit(100, 15, 10), 126)    # 126.5
        self.assertEqual(self._calc_limit(100, 15, 11), 128)    # 127.65
        self.assertEqual(self._calc_limit(100, 15, 100), 230)
        self.assertEqual(self._calc_limit(0, 0, 100), 100)
        self.assertEqual(self._calc_limit(0, 15, 100), 115)
        self.assertEqual(self._calc_limit(20, 0, 100), 120)

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

from base import MaxPrefixScenario
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv6

class MaxPrefixScenario_BIRDIPv6(MaxPrefixScenario):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, max-prefix, IPv6"
    RS_INSTANCE_CLASS = BIRDInstanceIPv6
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6
    IP_VER = 6

    DATA = {
        "rs_IPAddress":     "2001:db8:1:1::2",

        "AS1_1_IPAddress":  "2001:db8:1:1::11",

        "AS1_pref1":        "2a01:0:1::/48",
        "AS1_pref2":        "2a01:0:2::/48",
        "AS1_pref3":        "2a01:0:3::/48",
        "AS1_pref4":        "2a01:0:4::/48",
        "AS1_pref5":        "2a01:0:5::/48",

        "AS2_1_IPAddress":  "2001:db8:1:1::21",
        "AS2_pref1":        "2a02:0:1::/48",
        "AS2_pref2":        "2a02:0:2::/48",
        "AS2_pref3":        "2a02:0:3::/48",
        "AS2_pref4":        "2a02:0:4::/48",
        "AS2_pref5":        "2a02:0:5::/48",

        "AS3_1_IPAddress":  "2001:db8:1:1::31",
        "AS3_pref1":        "2a03:0:1::/48",
        "AS3_pref2":        "2a03:0:2::/48",
        "AS3_pref3":        "2a03:0:3::/48",
        "AS3_pref4":        "2a03:0:4::/48",
        "AS3_pref5":        "2a03:0:5::/48",
    }

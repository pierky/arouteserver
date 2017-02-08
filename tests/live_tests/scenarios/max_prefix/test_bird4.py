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
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4

class MaxPrefixScenario_BIRDIPv4(MaxPrefixScenario):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, max-prefix, IPv4"
    RS_INSTANCE_CLASS = BIRDInstanceIPv4
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

    DATA = {
        "rs_IPAddress":     "99.0.2.2",

        "AS1_1_IPAddress":  "99.0.2.11",

        "AS1_pref1":        "1.0.1.0/24",
        "AS1_pref2":        "1.0.2.0/24",
        "AS1_pref3":        "1.0.3.0/24",
        "AS1_pref4":        "1.0.4.0/24",
        "AS1_pref5":        "1.0.5.0/24",

        "AS2_1_IPAddress":  "99.0.2.21",
        "AS2_pref1":        "2.0.1.0/24",
        "AS2_pref2":        "2.0.2.0/24",
        "AS2_pref3":        "2.0.3.0/24",
        "AS2_pref4":        "2.0.4.0/24",
        "AS2_pref5":        "2.0.5.0/24",

        "AS3_1_IPAddress":  "99.0.2.31",
        "AS3_pref1":        "3.0.1.0/24",
        "AS3_pref2":        "3.0.2.0/24",
        "AS3_pref3":        "3.0.3.0/24",
        "AS3_pref4":        "3.0.4.0/24",
        "AS3_pref5":        "3.0.5.0/24",
    }

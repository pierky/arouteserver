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

from base import TagASSetScenario
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4

class TagASSetScenario_BIRDIPv4(TagASSetScenario):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, tag prefix/origin in AS-SET, IPv4"
    RS_INSTANCE_CLASS = BIRDInstanceIPv4
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

    DATA = {
        "rs_IPAddress":                     "99.0.2.2",
        "AS1_1_IPAddress":                  "99.0.2.11",
        "AS2_1_IPAddress":                  "99.0.2.21",
        "AS4_1_IPAddress":                  "99.0.2.41",
        "AS5_1_IPAddress":                  "99.0.2.51",

        "AS1_allowed_prefixes":             "1.0.0.0/16",

        "AS2_allowed_prefixes":             "2.0.0.0/16",
        "AS2_pref_ok_origin_ok1":           "2.0.1.0/24",
        "AS2_pref_ko_origin_ok1":           "2.1.0.0/24",
        "AS3_pref_ok_origin_ko1":           "2.0.2.0/24",
        "AS3_pref_ko_origin_ko1":           "3.0.1.0/24",

        "AS4_allowed_prefixes":             "4.0.0.0/16",
        "AS4_pref_ok_origin_ok1":           "4.0.1.0/24",
        "AS4_pref_ko_origin_ok1":           "4.1.0.0/24",
        "AS3_pref_ok_origin_ko2":           "4.0.2.0/24",

        "AS5_allowed_prefixes":             "5.0.0.0/16",
        "AS5_pref_ok_origin_ok1":           "5.0.1.0/24",
        "AS5_pref_ko_origin_ok1":           "5.1.0.0/24",
        "AS3_pref_ok_origin_ko3":           "5.0.2.0/24",
    }

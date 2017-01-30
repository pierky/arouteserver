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

from .base import TagASSetScenario
from ...bird import BIRDInstanceIPv6

class TagASSetScenario_BIRDIPv6(TagASSetScenario):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, tag prefix/origin in AS-SET, IPv6"
    RS_INSTANCE_CLASS = BIRDInstanceIPv6
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6
    IP_VER = 6

    DATA = {
        "rs_IPAddress":                     "2001:db8:1:1::2",
        "AS1_1_IPAddress":                  "2001:db8:1:1::11",
        "AS2_1_IPAddress":                  "2001:db8:1:1::21",
        "AS4_1_IPAddress":                  "2001:db8:1:1::41",
        "AS5_1_IPAddress":                  "2001:db8:1:1::51",

        "AS1_allowed_prefixes":             "2a01:0::/32",

        "AS2_allowed_prefixes":             "2a02:0::/32",
        "AS2_pref_ok_origin_ok1":           "2a02:0:1::/48",
        "AS2_pref_ko_origin_ok1":           "2a02:1:0::/48",
        "AS3_pref_ok_origin_ko1":           "2a02:0:2::/48",
        "AS3_pref_ko_origin_ko1":           "2a03:0:1::/48",

        "AS4_allowed_prefixes":             "2a04:0::/32",
        "AS4_pref_ok_origin_ok1":           "2a04:0:1::/48",
        "AS4_pref_ko_origin_ok1":           "2a04:1:0::/48",
        "AS3_pref_ok_origin_ko2":           "2a04:0:2::/48",

        "AS5_allowed_prefixes":             "2a05:0::/32",
        "AS5_pref_ok_origin_ok1":           "2a05:0:1::/48",
        "AS5_pref_ko_origin_ok1":           "2a05:1:0::/48",
        "AS3_pref_ok_origin_ko3":           "2a05:0:2::/48",
    }

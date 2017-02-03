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

from .base import BasicScenario
from ...bird import BIRDInstanceIPv6

class BasicScenario_BIRDIPv6(BasicScenario):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, global scenario, IPv6"
    RS_INSTANCE_CLASS = BIRDInstanceIPv6
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6
    IP_VER = 6

    DATA = {
        "rs_IPAddress":             "2001:db8:1:1::2",
        "blackhole_IP":             "2001:db8:1:1::66",

        "AS3_1_IPAddress":          "2001:db8:1:1::31",
        "AS1_1_IPAddress":          "2001:db8:1:1::11",
        "AS1_2_IPAddress":          "2001:db8:1:1::12",
        "AS2_1_IPAddress":          "2001:db8:1:1::21",
        "AS101_IPAddress":          "2001:db8:1:1::101",

        "AS1_allowed_prefixes":     "2a01:0::/32",
        "AS1_good1":                "2a01:0:1::/48",
        "AS1_good2":                "2a01:0:2::/48",
        "AS1_good3":                "2a01:0:3::/48",

        "bogon1":                   "2001::/48",
        "local1":                   "2001:db8:1::/48",
        "pref_len1":                "2a99::/16",
        "peer_as1":                 "2a99::/32",
        "invalid_asn1":             "2a99:1::/48",
        "aspath_len1":              "2a99:2::/48",

        "AS2_allowed_prefixes":     "2a02:0::/32",
        "AS2_good1":                "2a02:0:1::/48",
        "AS2_good2":                "2a02:0:2::/48",
        "AS2_blackhole1":           "2a02:0:3::1/128",
        "AS2_blackhole2":           "2a02:0:3::2/128",
        "AS2_blackhole3":           "2a02:0:3::3/128",

        "AS3_blacklist1":           "2a03:0:1::/48",
        "AS3_cc_AS1only":           "2a03:0:2::/48",
	"AS3_cc_not_AS1":           "2a03:0:3::/48",
	"AS3_cc_none":              "2a03:0:4::/48",
        "AS3_prepend1any":          "2a03:0:5::/48",
        "AS3_prepend2any":          "2a03:0:6::/48",
        "AS3_prepend3any":          "2a03:0:7::/48",

        "AS101_allowed_prefixes":   "3101:0::/32",
        "AS101_good1":              "3101:0:1::/48",
        "AS101_bad_std_comm":       "3101:0:2::/48",
        "AS101_bad_lrg_comm":       "3101:0:3::/48",
        "AS101_other_s_comm":       "3101:0:4::/48",
        "AS101_other_l_comm":       "3101:0:5::/48",
        "AS101_bad_good_comms":     "3101:0:6::/48",
        "AS101_no_rset":            "3101:1::/48",
        "AS101_transitfree_1":      "3101:0:7::/48",

        "AS101_roa_valid1":         "3101:0:8::/48",
        "AS101_roa_invalid1":       "3101:0:9::/48",
        "AS101_roa_badlen":         "3101:0:8000::/48",
        "AS101_roa_blackhole":      "3101:0:8000::1/128",

        "AS102_no_asset":           "3102:0:1::/48",
    }

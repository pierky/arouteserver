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

from base import BasicScenario
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4

class BasicScenario_BIRDIPv4(BasicScenario):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, global scenario, IPv4"
    RS_INSTANCE_CLASS = BIRDInstanceIPv4
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

    DATA = {
        "rs_IPAddress":             "99.0.2.2",
        "blackhole_IP":             "192.0.2.66",

        "AS3_1_IPAddress":          "99.0.2.31",
        "AS1_1_IPAddress":          "99.0.2.11",
        "AS1_2_IPAddress":          "99.0.2.12",
        "AS2_1_IPAddress":          "99.0.2.21",
        "AS101_IPAddress":          "99.0.2.101",

        "AS1_allowed_prefixes":     "1.0.0.0/8",
        "AS1_good1":                "1.0.1.0/24",
        "AS1_good2":                "1.0.2.0/24",
        "AS1_good3":                "1.0.3.0/24",

        "bogon1":                   "10.0.0.0/24",
        "local1":                   "99.0.2.0/24",
        "pref_len1":                "128.0.0.0/7",
        "peer_as1":                 "128.0.0.0/8",
        "invalid_asn1":             "128.0.0.0/9",
        "aspath_len1":              "128.0.0.0/10",

        "AS2_allowed_prefixes":     "2.0.0.0/16",
        "AS2_good1":                "2.0.1.0/24",
        "AS2_good2":                "2.0.2.0/24",
        "AS2_blackhole1":           "2.0.3.1/32",
        "AS2_blackhole2":           "2.0.3.2/32",
        "AS2_blackhole3":           "2.0.3.3/32",

        "AS3_blacklist1":           "3.0.1.0/24",
	"AS3_cc_AS1only":           "3.0.2.0/24",
	"AS3_cc_not_AS1":           "3.0.3.0/24",
	"AS3_cc_none":              "3.0.4.0/24",
        "AS3_prepend1any":          "3.0.5.0/24",
        "AS3_prepend2any":          "3.0.6.0/24",
        "AS3_prepend3any":          "3.0.7.0/24",
        "AS3_prepend1_AS1":         "3.0.8.0/24",
        "AS3_prepend2_AS2":         "3.0.9.0/24",
        "AS3_prep3AS1_1any":        "3.0.10.0/24",

        "AS101_allowed_prefixes":   "101.0.0.0/16",
        "AS101_good1":              "101.0.1.0/24",
        "AS101_bad_std_comm":       "101.0.2.0/24",
        "AS101_bad_lrg_comm":       "101.0.3.0/24",
        "AS101_other_s_comm":       "101.0.4.0/24",
        "AS101_other_l_comm":       "101.0.5.0/24",
        "AS101_bad_good_comms":     "101.0.6.0/24",
        "AS101_no_rset":            "101.1.0.0/24",
        "AS101_transitfree_1":      "101.0.7.0/24",

        "AS101_roa_valid1":         "101.0.8.0/24",
        "AS101_roa_invalid1":       "101.0.9.0/24",
        "AS101_roa_badlen":         "101.0.128.0/24",
        "AS101_roa_blackhole":      "101.0.128.1/32",

        "AS102_no_asset":           "102.0.1.0/24",
    }

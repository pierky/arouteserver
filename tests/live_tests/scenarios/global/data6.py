# Copyright (C) 2017-2020 Pier Carlo Chiodi
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

class BasicScenario_Data6(object):

    DATA = {
        "rs_IPAddress":             "2001:db8:1:1::2",
        "blackhole_IP":             "2001:db8:1:1::66",

        "AS1_1_IPAddress":          "2001:db8:1:1::11",
        "AS1_2_IPAddress":          "2001:db8:1:1::12",
        "AS2_1_IPAddress":          "2001:db8:1:1::21",
        "AS3_1_IPAddress":          "2001:db8:1:1::31",
        "AS4_1_IPAddress":          "2001:db8:1:1::41",
        "AS101_IPAddress":          "2001:db8:1:1::101",
        "AS222_IPAddress":          "2001:db8:1:1::222",
        "RoutesCollector_IPAddress":"2001:db8:1:1::999",

        "AS1_allowed_prefixes":     "2a01::/32",
        "AS1_good1":                "2a01:0:1::/48",
        "AS1_good2":                "2a01:0:2::/48",
        "AS1_good3":                "2a01:0:3::/48",

        "bogon1":                   "2001::/48",
        "local1":                   "2001:db8:1::/48",
        "pref_len1":                "2a99::/16",
        "peer_as1":                 "2a99::/32",
        "invalid_asn1":             "2a99:1::/48",
        "aspath_len1":              "2a99:2::/48",

        "AS1_whitel_1":             "2a11:1:1::/48",
        "AS1_whitel_2":             "2a11:1:2::/48",
        "AS1_whitel_3":             "2a11:2:1::/48",
        "AS1_whitel_4":             "2a11:3::/32",
        "AS1_whitel_5":             "2a11:4:1::/48",
        "AS1_whitel_6":             "2a11:3:1::/48",

        "AS2_allowed_prefixes":     "2a02::/32",
        "AS2_good1":                "2a02:0:1::/48",
        "AS2_good2":                "2a02:0:2::/48",
        "AS2_blackhole1":           "2a02:0:3::1/128",
        "AS2_blackhole2":           "2a02:0:3::2/128",
        "AS2_blackhole3":           "2a02:0:3::3/128",
        "AS2_nonclient_nexthop1":   "2a02:0:4::/48",
        "AS2_nonclient_nexthop1_nh":"2001:db8:1:1::22",
        "AS2_nonclient_nexthop2":   "2a02:0:5::/48",
        "AS2_nonclient_nexthop2_nh":"2001:db8:1:1::23",

        "AS3_blacklist1":           "2a03:0:1::/48",
        "AS3_cc_AS1only":           "2a03:0:2::/48",
        "AS3_cc_not_AS1":           "2a03:0:3::/48",
        "AS3_cc_none":              "2a03:0:4::/48",
        "AS3_prepend1any":          "2a03:0:5::/48",
        "AS3_prepend2any":          "2a03:0:6::/48",
        "AS3_prepend3any":          "2a03:0:7::/48",
        "AS3_prepend1_AS1":         "2a03:0:8::/48",
        "AS3_prepend2_AS2":         "2a03:0:9::/48",
        "AS3_prep3AS1_1any":        "2a03:0:a::/48",
        "AS3_noexport_any":         "2a03:0:b::/48",
        "AS3_noexport_AS1":         "2a03:0:c::/48",
        "AS3_rfc1997_noexp":        "2a03:0:d::/48",
        "AS3_transitfree_2":        "2a03:0:e::/48",

        "AS4_rtt_1":                "2a04:0:1::/48",
        "AS4_rtt_2":                "2a04:0:2::/48",
        "AS4_rtt_3":                "2a04:0:3::/48",
        "AS4_rtt_4":                "2a04:0:4::/48",
        "AS4_rtt_5":                "2a04:0:5::/48",
        "AS4_rtt_6":                "2a04:0:6::/48",
        "AS4_rtt_7":                "2a04:0:7::1/128",
        "AS4_rtt_8":                "2a04:0:8::/48",
        "AS4_rtt_9":                "2a04:0:9::/48",
        "AS4_rtt_10":               "2a04:0:a::/48",

        "AS101_allowed_prefixes":   "3101::/32",
        "AS101_good1":              "3101:0:1::/48",
        "AS101_bad_std_comm":       "3101:0:2::/48",
        "AS101_bad_lrg_comm":       "3101:0:3::/48",
        "AS101_other_s_comm":       "3101:0:4::/48",
        "AS101_other_l_comm":       "3101:0:5::/48",
        "AS101_bad_good_comms":     "3101:0:6::/48",
        "AS101_no_rset":            "3101:1::/48",
        "AS101_transitfree_1":      "3101:0:7::/48",
        "AS101_neverviars_1":       "3101:0:10::/48",
        "AS101_neverviars_2":       "3101:0:11::/48",

        "AS101_roa_valid1":         "3101:0:8::/48",
        "AS101_roa_invalid1":       "3101:0:9::/48",
        "AS101_roa_badlen":         "3101:0:8000::/48",
        "AS101_roa_blackhole":      "3101:0:8000::1/128",

        "AS101_roa_routeobj_1":     "3101:2::/33",
        "AS101_roa_routeobj_2":     "3101:2:4000::/34",
        "AS101_roa_routeobj_3":     "3101:2:8000::/48",
        "AS101_roa_routeobj_4":     "3101:3:1::/48",

        "AS102_no_asset":           "3102:0:1::/48",
        "AS101_no_ipv6_gl_uni":     "8000:1::/32",

        "AS103_allowed_prefixes":   "3103::/32",
        "AS103_gshut_1":            "3103:0:1::/48",
        "AS103_gshut_2":            "3103:0:2::/48",

        "AS104_arin_1":             "3104:0:1::/48",
        "AS104_nicbr_1":            "3104:1:1::/48",

        "AS222_allowed_prefixes":   "3222::/32",
        "AS222_aggregate1":         "3222:0:1::/48",
        "AS222_aggregate2":         "3222:0:2::/48",
        "AS222_aggregate3":         "3222:0:3::/48",

        "Default_route":            "::/0",
    }

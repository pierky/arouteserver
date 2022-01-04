# Copyright (C) 2017-2022 Pier Carlo Chiodi
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

class TagASSetScenario_Data4(object):

    DATA = {
        "rs_IPAddress":                     "192.0.2.2",
        "AS1_1_IPAddress":                  "192.0.2.11",
        "AS2_1_IPAddress":                  "192.0.2.21",
        "AS4_1_IPAddress":                  "192.0.2.41",
        "AS5_1_IPAddress":                  "192.0.2.51",
        "AS6_1_IPAddress":                  "192.0.2.61",

        "AS1_allowed_prefixes":             "1.0.0.0/16",

        "AS2_allowed_prefixes":             "2.0.0.0/16",
        "AS2_pref_ok_origin_ok1":           "2.0.1.0/24",
        "AS2_pref_ko_origin_ok1":           "2.1.0.0/24",
        "AS3_pref_ok_origin_ko1":           "2.0.2.0/24",
        "AS3_pref_ko_origin_ko1":           "3.0.1.0/24",
        "AS2_pref_wl_origin_ok":            "2.2.1.0/24",
        "AS2_pref_wl_origin_ko":            "2.2.2.0/24",
        "AS2_pref_wl_origin_wl":            "2.2.3.0/24",
        "AS2_pref_ko_origin_wl":            "2.3.1.0/24",
        "AS2_pref_ok_origin_wl":            "2.0.3.0/24",
        "AS2_roa2":                         "2.5.0.0/16",
        "AS2_arin1":                        "2.6.0.0/16",
        "AS2_roa3_arin2":                   "2.7.0.0/16",
        "AS2_ok_ok_roa3":                   "2.0.4.0/24",
        "AS2_ok_ok_arin3":                  "2.0.5.0/24",

        "AS4_allowed_prefixes":             "4.0.0.0/16",
        "AS4_pref_ok_origin_ok1":           "4.0.1.0/24",
        "AS4_pref_ko_origin_ok1":           "4.1.0.0/24",
        "AS3_pref_ok_origin_ko2":           "4.0.2.0/24",
        "AS4_pref_wl_origin_ok":            "4.2.1.0/24",
        "AS4_pref_wl_origin_ko":            "4.2.2.0/24",
        "AS4_pref_wl_origin_wl":            "4.2.3.0/24",
        "AS4_pref_ko_origin_wl":            "4.3.1.0/24",
        "AS4_pref_ok_origin_wl":            "4.0.3.0/24",
        "AS4_routewl_1":                    "4.4.0.0/16",
        "AS4_routewl_2":                    "4.4.1.0/24",
        "AS4_routewl_3":                    "4.5.1.0/24",
        "AS4_routewl_4":                    "4.5.2.0/24",
        "AS4_routewl_5":                    "4.6.1.0/24",

        "AS5_allowed_prefixes":             "5.0.0.0/16",
        "AS5_pref_ok_origin_ok1":           "5.0.1.0/24",
        "AS5_pref_ko_origin_ok1":           "5.1.0.0/24",
        "AS3_pref_ok_origin_ko3":           "5.0.2.0/24",
        "AS5_pref_wl_origin_ok":            "5.2.1.0/24",
        "AS5_pref_wl_origin_ko":            "5.2.2.0/24",
        "AS5_pref_wl_origin_wl":            "5.2.3.0/24",
        "AS5_pref_ko_origin_wl":            "5.3.1.0/24",
        "AS5_pref_ok_origin_wl":            "5.0.3.0/24",

        "AS6_allowed_prefixes":             "6.0.0.0/16",
        "AS2_roa1":                         "2.4.0.0/16",
        "AS3_roa2":                         "3.1.0.0/16",
        "AS3_arin1":                        "3.2.1.0/24",
        "AS3_roa3_arin2":                   "3.3.0.0/16",
        "AS6_ok_ok_roa6_arin6":             "6.0.1.0/24"
    }

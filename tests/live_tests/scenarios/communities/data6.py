# Copyright (C) 2017-2025 Pier Carlo Chiodi
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

class BGPCommunitiesScenario_Data6(object):

    DATA = {
        "rs_IPAddress":             "2001:db8:1:1::2",
        "AS1_IPAddress":            "2001:db8:1:1::11",
        "AS2_IPAddress":            "2001:db8:1:1::22",
        "AS131073_IPAddress":       "2001:db8:1:1::33",

        "AS1_good1":                "2a01:1::/32",

        "AS2_only_to_AS1_s":        "2a00:1::/32",
        "AS2_only_to_AS1_e":        "2a00:2::/32",
        "AS2_only_to_AS1_l":        "2a00:3::/32",
        "AS2_only_to_AS131073_e":   "2a00:4::/32",
        "AS2_only_to_AS131073_l":   "2a00:5::/32",
        "AS2_bad_cust_comm1":       "2a00:6::/32",
    }

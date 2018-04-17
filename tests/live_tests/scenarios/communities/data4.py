# Copyright (C) 2017-2018 Pier Carlo Chiodi
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

class BGPCommunitiesScenario_Data4(object):

    DATA = {
        "rs_IPAddress":             "192.0.2.2",
        "AS1_IPAddress":            "192.0.2.11",
        "AS2_IPAddress":            "192.0.2.22",
        "AS131073_IPAddress":       "192.0.2.33",

        "AS1_good1":                "1.0.1.0/24",

        "AS2_only_to_AS1_s":        "2.0.1.0/24",
        "AS2_only_to_AS1_e":        "2.0.2.0/24",
        "AS2_only_to_AS1_l":        "2.0.3.0/24",
        "AS2_only_to_AS131073_e":   "2.0.4.0/24",
        "AS2_only_to_AS131073_l":   "2.0.5.0/24",
        "AS2_bad_cust_comm1":       "2.0.6.0/24",
    }

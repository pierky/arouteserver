# Copyright (C) 2017-2023 Pier Carlo Chiodi
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
DATA_6 = {
    "rs_IPAddress":             "2001:db8:1:1::2",
    "AS1_IPAddress":            "2001:db8:1:1::11",
    "AS2_IPAddress":            "2001:db8:1:1::22",
    "AS3_IPAddress":            "2001:db8:1:1::33",
    "AS4_IPAddress":            "2001:db8:1:1::44",

    "AS2_invalid1":             "3002:0:9::/48",
    "AS2_badlen":               "3002:0:8000::/35",
    "AS2_valid1":               "3002:0:8::/48",
    "AS2_valid2":               "3002:0:8000::/34",
    "AS2_unknown1":             "3002:3002::/32",

    "AS3_invalid1":             "3003:0:9::/48",
    "AS3_badlen":               "3003:0:8000::/35",
    "AS3_valid1":               "3003:0:8::/48",
    "AS3_valid2":               "3003:0:8000::/34",
    "AS3_unknown1":             "3003:3003::/32",
}

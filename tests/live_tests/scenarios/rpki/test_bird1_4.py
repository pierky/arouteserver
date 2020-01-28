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

from .base import RPKIINVALIDScenario
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4

class RPKIINVALIDRoutesScenario_BIRDIPv4(RPKIINVALIDScenario):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, RPKI INVALID tagging, IPv4"
    RS_INSTANCE_CLASS = BIRDInstanceIPv4
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

    DATA = {
        "rs_IPAddress":             "192.0.2.2",
        "AS1_IPAddress":            "192.0.2.11",
        "AS2_IPAddress":            "192.0.2.22",
        "AS3_IPAddress":            "192.0.2.33",
        "AS4_IPAddress":            "192.0.2.44",

        "AS2_invalid1":             "2.0.9.0/24",
        "AS2_badlen":               "2.0.128.0/24",
        "AS2_valid1":               "2.0.8.0/24",
        "AS2_valid2":               "2.0.128.0/21",
        "AS2_unknown1":             "2.2.0.0/16",

        "AS3_invalid1":             "3.0.9.0/24",
        "AS3_badlen":               "3.0.128.0/24",
        "AS3_valid1":               "3.0.8.0/24",
        "AS3_valid2":               "3.0.128.0/21",
        "AS3_unknown1":             "3.3.0.0/16",
    }

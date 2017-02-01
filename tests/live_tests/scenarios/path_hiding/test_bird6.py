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

from .base import PathHidingScenario_MitigationOn, \
                  PathHidingScenario_MitigationOff
from ...bird import BIRDInstanceIPv6

class PathHidingScenario_BIRDIPv6(object):
    __test__ = False

    RS_INSTANCE_CLASS = BIRDInstanceIPv6
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6
    IP_VER = 6

    DATA = {
        "rs_IPAddress":                   "2001:db8:1:1::2",
        "AS1_IPAddress":                  "2001:db8:1:1::11",
        "AS2_IPAddress":                  "2001:db8:1:1::21",
        "AS3_IPAddress":                  "2001:db8:1:1::31",
        "AS4_IPAddress":                  "2001:db8:1:1::41",
        "AS101_IPAddress":                "2001:db8:1:1::101",

        "AS101_pref_ok1":                 "2a01:1:1::/48",
    }

class PathHidingScenario_MitigationOn_BIRDIPv6(PathHidingScenario_BIRDIPv6,
                                               PathHidingScenario_MitigationOn):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, path hiding, mitigation on, IPv6"

class PathHidingScenario_MitigationOff_BIRDIPv6(PathHidingScenario_BIRDIPv6,
                                                PathHidingScenario_MitigationOff):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, path hiding, mitigation off, IPv6"


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

from base import PathHidingScenario_MitigationOn, \
                 PathHidingScenario_MitigationOff
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4

class PathHidingScenario_BIRDIPv4(object):
    __test__ = False

    RS_INSTANCE_CLASS = BIRDInstanceIPv4
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

    DATA = {
        "rs_IPAddress":                   "99.0.2.2",
        "AS1_IPAddress":                  "99.0.2.11",
        "AS2_IPAddress":                  "99.0.2.21",
        "AS3_IPAddress":                  "99.0.2.31",
        "AS4_IPAddress":                  "99.0.2.41",
        "AS101_IPAddress":                "99.0.2.101",

        "AS101_pref_ok1":                 "101.0.1.0/24",
    }

class PathHidingScenario_MitigationOn_BIRDIPv4(PathHidingScenario_BIRDIPv4,
                                               PathHidingScenario_MitigationOn):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, path hiding, mitigation on, IPv4"

class PathHidingScenario_MitigationOff_BIRDIPv4(PathHidingScenario_BIRDIPv4,
                                                PathHidingScenario_MitigationOff):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, path hiding, mitigation off, IPv4"


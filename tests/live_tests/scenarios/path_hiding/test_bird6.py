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
                 PathHidingScenario_MitigationOff, \
                 PathHidingScenarioBIRD
from data6 import PathHidingScenario_Data6
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv6

class PathHidingScenario_MitigationOn_BIRDIPv6(PathHidingScenario_Data6,
                                               PathHidingScenario_MitigationOn,
                                               PathHidingScenarioBIRD):
    __test__ = True

    RS_INSTANCE_CLASS = BIRDInstanceIPv6
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6
    IP_VER = 6

    SHORT_DESCR = "Live test, BIRD, path hiding, mitigation on, IPv6"

class PathHidingScenario_MitigationOff_BIRDIPv6(PathHidingScenario_Data6,
                                                PathHidingScenario_MitigationOff,
                                                PathHidingScenarioBIRD):
    __test__ = True

    RS_INSTANCE_CLASS = BIRDInstanceIPv6
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6
    IP_VER = 6

    SHORT_DESCR = "Live test, BIRD, path hiding, mitigation off, IPv6"


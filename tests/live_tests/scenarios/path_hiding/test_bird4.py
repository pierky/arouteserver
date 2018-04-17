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

from .base import PathHidingScenario_MitigationOn, \
                 PathHidingScenario_MitigationOff, \
                 PathHidingScenarioBIRD
from .data4 import PathHidingScenario_Data4
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4

class PathHidingScenario_MitigationOn_BIRDIPv4(PathHidingScenario_Data4,
                                               PathHidingScenario_MitigationOn,
                                               PathHidingScenarioBIRD):
    __test__ = True

    RS_INSTANCE_CLASS = BIRDInstanceIPv4
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

    SHORT_DESCR = "Live test, BIRD, path hiding, mitigation on, IPv4"

class PathHidingScenario_MitigationOff_BIRDIPv4(PathHidingScenario_Data4,
                                                PathHidingScenario_MitigationOff,
                                                PathHidingScenarioBIRD):
    __test__ = True

    RS_INSTANCE_CLASS = BIRDInstanceIPv4
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

    SHORT_DESCR = "Live test, BIRD, path hiding, mitigation off, IPv4"


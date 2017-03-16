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

import os
import unittest

from base import PathHidingScenario_MitigationOn, \
                 PathHidingScenario_MitigationOff, \
                 PathHidingScenarioOpenBGPD
from data4 import PathHidingScenario_Data4
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance

@unittest.skipIf("TRAVIS" in os.environ, "not supported on Travis CI")
class PathHidingScenario_MitigationOn_BIRDIPv4(PathHidingScenario_Data4,
                                               PathHidingScenario_MitigationOn,
                                               PathHidingScenarioOpenBGPD):
    __test__ = True
    SKIP_ON_TRAVIS = True

    RS_INSTANCE_CLASS = OpenBGPDInstance
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4

    SHORT_DESCR = "Live test, OpenBGPD, path hiding, mitigation on, IPv4"

@unittest.skipIf("TRAVIS" in os.environ, "not supported on Travis CI")
class PathHidingScenario_MitigationOff_BIRDIPv4(PathHidingScenario_Data4,
                                                PathHidingScenario_MitigationOff,
                                                PathHidingScenarioOpenBGPD):
    __test__ = True
    SKIP_ON_TRAVIS = True

    RS_INSTANCE_CLASS = OpenBGPDInstance
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4

    SHORT_DESCR = "Live test, OpenBGPD, path hiding, mitigation off, IPv4"


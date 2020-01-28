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

import os
import unittest

from .base import GShutScenarioOpenBGPDLatest
from .data6 import GShutScenario_Data6
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv6
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDLatestInstance

class GShutScenario_OpenBGPDIPv6(GShutScenario_Data6, GShutScenarioOpenBGPDLatest):

    __test__ = True
    SKIP_ON_TRAVIS = True

    SHORT_DESCR = "Live test, OpenBGPD {}, gshut, IPv6".format(
        OpenBGPDLatestInstance.BGP_SPEAKER_VERSION
    )
    RS_INSTANCE_CLASS = OpenBGPDLatestInstance
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6

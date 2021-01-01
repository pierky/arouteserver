# Copyright (C) 2017-2021 Pier Carlo Chiodi
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

from .base import TagASSetScenario_EmptyAS_SETs, \
                  TagASSetScenarioOpenBGPDLatest
from .data6 import TagASSetScenario_Data6
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv6
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDLatestInstance

class TagASSetScenario_EmptyAS_SETs_OpenBGPDIPv6(TagASSetScenario_EmptyAS_SETs,
                                                 TagASSetScenario_Data6,
                                                 TagASSetScenarioOpenBGPDLatest):
    __test__ = True
    SKIP_ON_TRAVIS = True

    RS_INSTANCE_CLASS = OpenBGPDLatestInstance
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6

    SHORT_DESCR = "Live test, OpenBGPD {}, tag prefix/origin empty AS-SET, IPv6".format(
        OpenBGPDLatestInstance.BGP_SPEAKER_VERSION
    )

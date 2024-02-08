# Copyright (C) 2017-2024 Pier Carlo Chiodi
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

from .base import TagASSetScenario_WithAS_SETs, \
                  TagASSetScenarioBIRD3
from .data4 import TagASSetScenario_Data4
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4, BIRD3Instance

class TagASSetScenario_WithAS_SETs_BIRDsIPv4(TagASSetScenario_WithAS_SETs,
                                             TagASSetScenario_Data4,
                                             TagASSetScenarioBIRD3):
    __test__ = True

    RS_INSTANCE_CLASS = BIRD3Instance
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4

    SHORT_DESCR = "Live test, BIRD v3, tag prefix/origin in AS-SET, IPv4"

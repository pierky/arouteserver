# Copyright (C) 2017-2022 Pier Carlo Chiodi
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

from .base import TagRejectPolicyScenarioBIRD2
from .data4 import BasicScenario_Data4
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4, BIRD2Instance

class TagRejectPolicyScenario_BIRD2IPv4(BasicScenario_Data4, TagRejectPolicyScenarioBIRD2):

    __test__ = True

    SHORT_DESCR = "Live test, BIRD v2, 'tag' reject policy scenario, IPv4"
    RS_INSTANCE_CLASS = BIRD2Instance
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4

    ALLOWED_LOG_ERRORS = [
        "Invalid NEXT_HOP attribute - neighbor address 192.0.2.11",
        "Invalid route 1.0.3.0/24 withdrawn"
    ]

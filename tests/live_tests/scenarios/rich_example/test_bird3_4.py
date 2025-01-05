# Copyright (C) 2017-2025 Pier Carlo Chiodi
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

from .base import RichConfigExampleScenarioBIRD3
from .data4 import RichConfigExampleScenario_Data4
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4, BIRD3Instance

class RichConfigExampleScenario_BIRD3IPv4(RichConfigExampleScenario_Data4,
                                          RichConfigExampleScenarioBIRD3):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD v3, examples, rich config, IPv4"
    RS_INSTANCE_CLASS = BIRD3Instance
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4

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

from base import DefaultConfigScenarioBIRD
from data4 import DefaultConfigScenario_Data4
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4

class DefaultConfigScenarioBIRD_IPv4(DefaultConfigScenario_Data4,
                                     DefaultConfigScenarioBIRD):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, default config, IPv4"
    RS_INSTANCE_CLASS = BIRDInstanceIPv4
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

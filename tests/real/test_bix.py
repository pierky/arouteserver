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

from .base import *


class TestRealConfigs_BIX_IPv4(object):

    IXP = "BIX_IPv4"
    CLIENTS_FILE = "bix-ipv4.yml"
    IP_VER = 4

class TestRealConfigs_BIX_IPv4_BIRD(TestRealConfigs_BIX_IPv4,
                                    TestRealConfigs_BIRD):
    __test__ = True

class TestRealConfigs_BIX_IPv4_OpenBGPD64(TestRealConfigs_BIX_IPv4,
                                          TestRealConfigs_OpenBGPD64):
    __test__ = True


class TestRealConfigs_BIX_IPv6(object):

    IXP = "BIX_IPv6"
    CLIENTS_FILE = "bix-ipv6.yml"
    IP_VER = 6

class TestRealConfigs_BIX_IPv6_BIRD(TestRealConfigs_BIX_IPv6,
                                    TestRealConfigs_BIRD):
    __test__ = True

class TestRealConfigs_BIX_IPv6_OpenBGPD64(TestRealConfigs_BIX_IPv6,
                                          TestRealConfigs_OpenBGPD64):
    __test__ = True

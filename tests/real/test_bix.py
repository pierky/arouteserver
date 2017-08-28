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

from base import TestRealConfigs_IXP


class TestRealConfigs_BIX_IPv4(TestRealConfigs_IXP):
    __test__ = True

    IXP = "BIX (IPv4)"
    CLIENTS_FILE = "bix-ipv4.yml"
    IP_VER = 4

class TestRealConfigs_BIX_IPv6(TestRealConfigs_IXP):
    __test__ = True

    IXP = "BIX (IPv6)"
    CLIENTS_FILE = "bix-ipv6.yml"
    IP_VER = 6

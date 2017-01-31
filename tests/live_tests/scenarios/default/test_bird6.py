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

from .base import DefaultConfigScenario
from ...bird import BIRDInstanceIPv6

class TagASSetScenario_BIRDIPv6(DefaultConfigScenario):
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, default config, IPv6"
    RS_INSTANCE_CLASS = BIRDInstanceIPv6
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6
    IP_VER = 6

    DATA = {
        "rs_IPAddress":                     "2001:db8:1:1::2",

        "AS10745_allowed_prefixes":         "2001:500:4::/48",
        "AS3333_allowed_prefixes":          "2001:67c:2e8::/48",
    }

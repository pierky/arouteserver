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

from .base import SkeletonScenario
from pierky.arouteserver.builder import BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv6

class SkeletonScenario_BIRDIPv6(SkeletonScenario):
    """BGP speaker specific and IP version specific derived class.

    Please see test_bird4.py for more information.
    """

    __test__ = True

    SHORT_DESCR = "Live test, BIRD, skeleton, IPv6"
    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    RS_INSTANCE_CLASS = BIRDInstanceIPv6
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv6
    IP_VER = 6

    DATA = {
        "rs_IPAddress":             "2001:db8:1:1::2",
        "AS1_IPAddress":            "2001:db8:1:1::11",
        "AS2_IPAddress":            "2001:db8:1:1::22",

        "AS2_prefix1":              "2a00:2::/32",
        "AS2_bogon1":               "2001:0:8000::/48"
    }

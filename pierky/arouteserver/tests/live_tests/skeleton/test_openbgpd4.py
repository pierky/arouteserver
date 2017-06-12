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

import os
import unittest

from base import SkeletonScenario
from pierky.arouteserver.builder import OpenBGPDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario_TagRejectPolicy
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPD60Instance

@unittest.skipIf("TRAVIS" in os.environ, "not supported on Travis CI")
class SkeletonScenario_OpenBGPDIPv4(LiveScenario_TagRejectPolicy,
                                    SkeletonScenario):
    """BGP speaker specific and IP version specific derived class.

    Please see test_bird4.py for more information.
    """

    __test__ = True
    SKIP_ON_TRAVIS = True

    SHORT_DESCR = "Live test, OpenBGPD 6.0, skeleton, IPv4"
    CONFIG_BUILDER_CLASS = OpenBGPDConfigBuilder
    RS_INSTANCE_CLASS = OpenBGPD60Instance
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

    DATA = {
        "rs_IPAddress":             "192.0.2.2",
        "AS1_IPAddress":            "192.0.2.11",
        "AS2_IPAddress":            "192.0.2.22",

        "AS2_prefix1":              "2.0.1.0/24",
        "AS2_bogon1":               "192.168.2.0/24"
    }

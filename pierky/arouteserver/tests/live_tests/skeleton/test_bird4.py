# Copyright (C) 2017-2018 Pier Carlo Chiodi
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
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4

class SkeletonScenario_BIRDIPv4(SkeletonScenario):
    """BGP speaker specific and IP version specific derived class.

    This class inherits all the test functions from the base class.
    Here, only IP version specific attributes are set, such as the
    prefix IDs / real IP prefixes mapping schema.

    The prefix IDs reported within the ``DATA`` dictionary must be
    used in the parent class' test functions to reference the real
    IP addresses/prefixes used in the scenario. Also the other
    BGP speakers' configuration templates must use these IDs.
    For an example plase see the "AS2.j2" file.

    The ``SHORT_DESCR`` attribute can be set with a brief description
    of this scenario.
    """

    # Leave this to True in order to allow nose to use this class
    # to run tests.
    __test__ = True

    SHORT_DESCR = "Live test, BIRD, skeleton, IPv4"
    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    RS_INSTANCE_CLASS = BIRDInstanceIPv4
    CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
    IP_VER = 4

    DATA = {
        "rs_IPAddress":             "192.0.2.2",
        "AS1_IPAddress":            "192.0.2.11",
        "AS2_IPAddress":            "192.0.2.22",

        "AS2_prefix1":              "2.0.1.0/24",
        "AS2_bogon1":               "192.168.2.0/24"
    }

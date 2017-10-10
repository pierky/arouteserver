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

from .base import *


class TestRealConfigs_SIX(object):

    IXP = "SIX"
    CLIENTS_FILE = "six.yml"

class TestRealConfigs_SIX_BIRD(TestRealConfigs_SIX,
                               TestRealConfigs_BIRD):
    __test__ = True

class TestRealConfigs_SIX_OpenBGPD60(TestRealConfigs_SIX,
                                     TestRealConfigs_OpenBGPD60):
    __test__ = True

class TestRealConfigs_SIX_OpenBGPD62(TestRealConfigs_SIX,
                                     TestRealConfigs_OpenBGPD62):
    __test__ = True

    SKIP_LOAD_NO_RESOURCES = True

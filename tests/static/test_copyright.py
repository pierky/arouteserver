# Copyright (C) 2017-2024 Pier Carlo Chiodi
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

import datetime
import unittest

from pierky.arouteserver.config.program import ConfigParserProgram
from pierky.arouteserver.version import COPYRIGHT_YEAR

class TestCopyright(unittest.TestCase):

    def test_current_year(self):
        """Copyright: is current year"""

        self.assertEqual(COPYRIGHT_YEAR, datetime.datetime.now().year,
                         msg="Consider to run ./utils/apply_copyright")

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

from .base import ARouteServerCommand

class CheckNewRelease(ARouteServerCommand):

    COMMAND_NAME = "check_update"
    COMMAND_HELP = ("Check if a new release of ARouteServer is available.")
    NEEDS_CONFIG = True

    def run(self):
        self.check_new_release(print_output=True)

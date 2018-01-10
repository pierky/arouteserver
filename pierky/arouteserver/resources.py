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

import os
import pkg_resources

from .errors import ResourceNotFoundError


def get_local_dir(dirname):
    pkg_path = pkg_resources.resource_filename("pierky.arouteserver", dirname)
    if os.path.isdir(pkg_path):
        return pkg_path

    raise ResourceNotFoundError(
        "Can't find '{}' directory at {}".format(
            dirname, pkg_path
        )
    )

def get_config_dir():
    return get_local_dir("config.d")

def get_templates_dir():
    return get_local_dir("templates")

def get_live_test_skeleton_dir():
    return get_local_dir("tests/live_tests/skeleton")

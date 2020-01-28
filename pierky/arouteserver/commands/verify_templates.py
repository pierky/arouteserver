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

import textwrap

from .base import ARouteServerCommand

from ..config.program import program_config

class VerifyTemplatesCommand(ARouteServerCommand):

    COMMAND_NAME = "verify-templates"
    COMMAND_HELP = ("Verify if templates are aligned with the current "
                    "version of the program and print debugging info.")
    NEEDS_CONFIG = True

    def run(self):
        errors = program_config.verify_templates()
        all_right = errors == []
        if not all_right:
            print("\n".join(textwrap.wrap(
                  "One or more templates are not aligned with those "
                  "distributed with the current version of the program:\n")))
            print("")
            for err in errors:
                print(" - "
                      "\n   ".join(textwrap.wrap(err)))
            print("")
            print("\n".join(textwrap.wrap(
                  "Unexpected behaviours may occur during the configuration "
                  "building process: if you experience issues please consider "
                  "running the 'arouteserver setup-templates' command to "
                  "restore the original templates that are distributed with "
                  "the current version of the program.")))
            print("\n".join(textwrap.wrap(
                  "To customize the configuration of the route server with "
                  "your own options, please consider using 'Site-specific "
                  "custom configuration files' instead of editing the "
                  "template files: more info at "
                  "https://arouteserver.readthedocs.io/en/latest/CONFIG.html"
                  "#site-specific-custom-config")))
        else:
            print("Everything is fine; templates are aligned with those "
                  "expected by the current version of the program.")
        return all_right

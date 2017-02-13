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

from base import ARouteServerCommand
from ..config.program import program_config
from ..errors import ARouteServerError
from ..resources import get_live_test_skeleton_dir

class InitScenarioCommand(ARouteServerCommand):

    COMMAND_NAME = "init-scenario"
    COMMAND_HELP = ("Initialize a new live test scenario by copying "
                    "files from the skeleton example.")

    @classmethod
    def add_arguments(cls, parser):
        super(InitScenarioCommand, cls).add_arguments(parser)

        cls.add_program_config_arguments(parser)

        parser.add_argument(
            "dest_dir",
            help="Destination directory for the new scenario")

    def run(self):
        if not self.setup():
            return False

        skeleton_dir = get_live_test_skeleton_dir()
        dest_dir = self.args.dest_dir
        templates_dir = program_config.get_cfg_file_path("templates_dir")

        if os.path.exists(dest_dir):
            raise ARouteServerError(
                "The directory {} already exists".format(dest_dir)
            )

        print("")

        try:
            os.makedirs(dest_dir)
        except Exception as e:
            raise ARouteServerError(
                "An error occurred while creating {}: {}".format(
                    dest_dir, str(e)
                )
            )

        link_src = "{}/bird".format(templates_dir)
        link_dst = "{}/bird".format(dest_dir)
        try:
            os.symlink(link_src, link_dst)
        except Exception as e:
            raise ARouteServerError(
                "An error occurred while creating a link "
                "to the BIRD templates directory: link "
                "source {}, link destination {}: {}".format(
                    link_src, link_dst, str(e)
                )
            )
        print("A link to the BIRD templates directory {} "
              "has been created in {}.".format(
                  link_src, link_dst
                )
            )

        for filename in os.listdir(skeleton_dir):
            src_path = "{}/{}".format(skeleton_dir, filename)
            dst_path = "{}/{}".format(dest_dir, filename)
            if not os.path.isfile(src_path):
                continue
            try:
                with open(src_path, "r") as s:
                    with open(dst_path, "w") as d:
                        d.write(s.read())
            except Exception as e:
                raise ARouteServerError(
                    "An error occurred while copying {} "
                    "into {}: {}".format(
                        src_path, dst_path, str(e)
                    )
                )

        print("A new live test scenario has been initialized "
              "in the {} directory.\n\nFor details: {}".format(
                  dest_dir,
                  "https://arouteserver.readthedocs.io/en/latest/LIVETESTS.html"
                  "#how-to-build-custom-scenarios"
              )
        )

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
import re

from .base import ARouteServerCommand
from ..ask import Ask
from ..config.program import program_config
from ..errors import ARouteServerError
from ..resources import get_live_test_skeleton_dir

class InitScenarioCommand(ARouteServerCommand):

    COMMAND_NAME = "init-scenario"
    COMMAND_HELP = ("Initialize a new live test scenario by copying "
                    "files from the skeleton example.")
    NEEDS_CONFIG = True

    @classmethod
    def add_arguments(cls, parser):
        super(InitScenarioCommand, cls).add_arguments(parser)

        parser.add_argument(
            "dest_dir",
            help="Destination directory for the new scenario")

    def run(self):
        print("Please provide an identifier for the new scenario, "
              "something that will be used as the name of the "
              "Python classes where the test functions will be "
              "implemented.")
        print("Examples: TagASSet, BGPCommunities, MaxPrefix, PathHiding")
        print("")
        res, class_name = Ask().ask("Scenario class name:")

        if not res:
            print("")
            print("Aborted.")
            return False

        if class_name.lower().endswith("scenario"):
            class_name = class_name[:-8]

        if not re.match("[a-z_][a-z_0-9 ]+", class_name, re.IGNORECASE):
            print("")
            print("Invalid name. "
                  "It must be in the format "
                  "(letter|\"_\") (letter | digit | \"_\")*")
            print("Aborted.")
            return False

        class_name = "{}Scenario".format(class_name.title()).replace(" ", "")

        skeleton_dir = get_live_test_skeleton_dir()
        dest_dir = os.path.expanduser(self.args.dest_dir)
        templates_dir = program_config.get_dir("templates_dir")

        if os.path.exists(dest_dir):
            raise ARouteServerError(
                "The directory {} already exists".format(dest_dir)
            )

        res, yes_or_no = Ask().ask_yes_no(
            "The {} directory will be created: proceed?".format(dest_dir),
            default="yes"
        )

        print("")

        if not res or yes_or_no.lower() != "yes":
            print("Aborted.")
            return False

        try:
            os.makedirs(dest_dir)
        except Exception as e:
            raise ARouteServerError(
                "An error occurred while creating {}: {}".format(
                    dest_dir, str(e)
                )
            )

        for speaker in ("bird", "openbgpd"):
            link_src = "{}/{}".format(templates_dir, speaker)
            link_dst = "{}/{}".format(dest_dir, speaker)
            try:
                os.symlink(link_src, link_dst)
            except Exception as e:
                raise ARouteServerError(
                    "An error occurred while creating a link "
                    "to the '{}' templates directory: link "
                    "source {}, link destination {}: {}".format(
                        speaker, link_src, link_dst, str(e)
                    )
                )
            print("A link to the '{}' templates directory {} "
                  "has been created in {}.".format(
                    speaker, link_src, link_dst
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
                        content = s.read()
                        if filename in ("base.py", "test_bird4.py",
                                        "test_bird6.py", "test_openbgpd4.py",
                                        "test_openbgpd6.py"):
                            content = content.replace(
                                "SkeletonScenario", class_name
                            )
                            content = content.replace(
                                ", skeleton,", ", {},".format(class_name)
                            )
                        d.write(content)
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

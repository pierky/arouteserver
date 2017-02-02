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

import argparse
import logging
import os
import sys

from .base import ARouteServerCommand
from ..builder import BIRDConfigBuilder
from ..errors import ARouteServerError

class BuildCommand(ARouteServerCommand):

    @classmethod
    def add_arguments(cls, parser):
        super(BuildCommand, cls).add_arguments(parser)

        cls.add_program_config_arguments(parser)

        parser.add_argument(
            "-o", "--output",
            type=argparse.FileType('w'),
            help="Output file. Default: stdout.",
            default=sys.stdout,
            dest="output_file")

        parser.add_argument(
            "--speaker",
            help="The BGP speaker target implementation for "
                "the configuration that will be built.",
            dest="speaker",
            choices=["BIRD"],
            default="BIRD")

        group = parser.add_argument_group(
            title="Route server configuration",
            description="The following arguments override those provided "
                        "in the program's configuration file."
        )

        group.add_argument(
            "--general",
            help="General route server configuration file.",
            metavar="FILE",
            dest="cfg_general")

        group.add_argument(
            "--clients",
            help="Route server clients configuration file.",
            metavar="FILE",
            dest="cfg_clients")

        group.add_argument(
            "--bogons",
            help="Bogons configuration file.",
            metavar="FILE",
            dest="cfg_bogons")

        group = parser.add_argument_group(
            title="Rendering",
            description="The following arguments override those provided "
                        "in the program's configuration file."
        )

        group.add_argument(
            "--template-dir",
            help="Directory where Jinja2 files are stored.",
            metavar="DIR",
            dest="template_dir")

        group.add_argument(
            "--template-file-name",
            help="Main Jinja2 template file name.",
            metavar="NAME",
            dest="template_name")

        group.add_argument(
            "--ip-ver",
            help="IP version. "
                "Default: both IPv4 and IPv6",
            default=None,
            choices=[4, 6],
            type=int,
            dest="ip_ver")

    def run(self):
        if not self.setup():
            return False

        # Config builder setup

        cfg_builder_params = {
            "cfg_general": self.get_cfg_path("cfg_general"),
            "cfg_clients": self.get_cfg_path("cfg_clients"),
            "cfg_bogons": self.get_cfg_path("cfg_bogons"),
            "cache_dir": self.get_cfg_path("cache_dir"),
            "cache_expiry": self.get_cfg_val("cache_expiry"),
            "bgpq3_path": self.get_cfg_val("bgpq3_path"),
            "template_dir": self.get_cfg_path("template_dir"),
            "template_name": self.get_cfg_val("template_name"),
            "ip_ver": self.args.ip_ver,
        }

        template_sub_dir = None
        if self.args.speaker == "BIRD":
            builder_class = BIRDConfigBuilder
            template_sub_dir = "bird"
        else:
            raise ARouteServerError(
                "Unknown BGP speaker implementation: {}".format(args.speaker)
            )
        if template_sub_dir:
            cfg_builder_params["template_dir"] = os.path.join(
                cfg_builder_params["template_dir"], template_sub_dir
            )

        try:
            builder = BIRDConfigBuilder(**cfg_builder_params)
            self.args.output_file.write(builder.render_template())
        except ARouteServerError as e:
            if str(e):
                logging.error(str(e))
            return False

        return True

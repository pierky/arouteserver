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
from ..builder import ConfigBuilder, BIRDConfigBuilder
from ..errors import ARouteServerError

class TemplateRenderingCommands(ARouteServerCommand):

    @classmethod
    def add_arguments(cls, parser):
        super(TemplateRenderingCommands, cls).add_arguments(parser)

        cls.add_program_config_arguments(parser)

        parser.add_argument(
            "-o", "--output",
            type=argparse.FileType('w'),
            help="Output file. Default: stdout.",
            default=sys.stdout,
            dest="output_file")

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
            "--templates-dir",
            help="Directory where Jinja2 files are stored. This is the "
                 "directory where the \"html\" directory and other BGP "
                 "speaker specific directories (\"bird\") can be found.",
            metavar="DIR",
            dest="templates_dir")

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

    def _get_template_sub_dir(self):
        raise NotImplementedError()

    def _get_builder_class(self):
        raise NotImplementedError()

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
            "bgpq3_host": self.get_cfg_val("bgpq3_host"),
            "bgpq3_sources": self.get_cfg_val("bgpq3_sources"),
            "template_dir": self.get_cfg_path("templates_dir"),
            "template_name": self.get_cfg_val("template_name"),
            "ip_ver": self.args.ip_ver,
        }

        builder_class = self._get_builder_class()
        
        template_sub_dir = self._get_template_sub_dir()
        if template_sub_dir:
            cfg_builder_params["template_dir"] = os.path.join(
                cfg_builder_params["template_dir"], template_sub_dir
            )

        try:
            builder = builder_class(**cfg_builder_params)
            self.args.output_file.write(builder.render_template())
        except ARouteServerError as e:
            if str(e):
                logging.error(str(e))
            return False

        return True

class BuildCommand(TemplateRenderingCommands):

    COMMAND_NAME = "build"
    COMMAND_HELP = "Build route server configuration."

    @classmethod
    def add_arguments(cls, parser):
        super(BuildCommand, cls).add_arguments(parser)

        parser.add_argument(
            "--speaker",
            help="The BGP speaker target implementation for "
                "the configuration that will be built.",
            dest="speaker",
            choices=["BIRD"],
            default="BIRD")

    def _get_builder_class(self):
        if self.args.speaker == "BIRD":
            return BIRDConfigBuilder
        raise ARouteServerError(
            "Unknown BGP speaker implementation: {}".format(self.args.speaker)
        )

    def _get_template_sub_dir(self):
        if self.args.speaker == "BIRD":
            return "bird"
        raise ARouteServerError(
            "Unknown BGP speaker implementation: {}".format(self.args.speaker)
        )

class HTMLCommand(TemplateRenderingCommands):

    COMMAND_NAME = "html"
    COMMAND_HELP = ("Build an HTML descriptive page containing the "
                    "textual representation of the route server "
                    "configuration.")

    def _get_builder_class(self):
        return ConfigBuilder

    def _get_template_sub_dir(self):
        return "html"

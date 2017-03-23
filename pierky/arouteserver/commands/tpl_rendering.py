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
from ..builder import ConfigBuilder, BIRDConfigBuilder, \
                      OpenBGPDConfigBuilder, TemplateContextDumper
from ..config.program import program_config
from ..errors import ARouteServerError, TemplateRenderingError

class TemplateRenderingCommands(ARouteServerCommand):

    NEEDS_CONFIG = True

    @classmethod
    def add_arguments(cls, parser):
        super(TemplateRenderingCommands, cls).add_arguments(parser)

        parser.add_argument(
            "-o", "--output",
            type=argparse.FileType('w'),
            help="Output file. Default: stdout.",
            default=sys.stdout,
            dest="output_file")

        parser.add_argument(
            "--test-only",
            action="store_true",
            help="Only verify the input configuration files (general.yml, "
                 "clients.yml and so on), do not produce any output "
                 "configuration.",
            dest="test_only")

        parser.add_argument(
            "--ignore-issues",
            nargs="+",
            help="Ignore compatibility issues identified by the IDs "
                 "provided here.",
            metavar="ISSUE_ID",
            dest="ignore_errors")

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

    def _set_cfg_builder_params(self):
        pass

    def run(self):
        tpl_all_right = program_config.verify_templates() == []
        if not tpl_all_right:
            logging.warning("One or more templates are not aligned "
                            "with those used by the current version "
                            "of the program. "
                            "Run 'arouteserver verify-templates' for "
                            "more information.")

        # Config builder setup
        self.cfg_builder_params = {
            "cfg_general": program_config.get("cfg_general"),
            "cfg_clients": program_config.get("cfg_clients"),
            "cfg_bogons": program_config.get("cfg_bogons"),
            "cache_dir": program_config.get("cache_dir"),
            "cache_expiry": program_config.get("cache_expiry"),
            "bgpq3_path": program_config.get("bgpq3_path"),
            "bgpq3_host": program_config.get("bgpq3_host"),
            "bgpq3_sources": program_config.get("bgpq3_sources"),
            "template_dir": program_config.get("templates_dir"),
            "template_name": program_config.get("template_name"),
            "ip_ver": self.args.ip_ver,
            "threads": program_config.get("threads"),
            "ignore_errors": self.args.ignore_errors
        }
        self._set_cfg_builder_params()

        builder_class = self._get_builder_class()
        
        template_sub_dir = self._get_template_sub_dir()
        if template_sub_dir:
            self.cfg_builder_params["template_dir"] = os.path.join(
                self.cfg_builder_params["template_dir"], template_sub_dir
            )

        try:
            builder = builder_class(**self.cfg_builder_params)
            if not self.args.test_only:
                builder.render_template(output_file=self.args.output_file)
        except TemplateRenderingError as e:
            if tpl_all_right:
                raise
            e.templates_not_aligned = True
            raise e

        return True

class BIRDCommand(TemplateRenderingCommands):

    COMMAND_NAME = "bird"
    COMMAND_HELP = "Build route server configuration for BIRD."

    def _get_builder_class(self):
        return BIRDConfigBuilder

    def _get_template_sub_dir(self):
        return "bird"

class OpenBGPDCommand(TemplateRenderingCommands):

    COMMAND_NAME = "openbgpd"
    COMMAND_HELP = "Build route server configuration for OpenBGPD."

    def _get_builder_class(self):
        return OpenBGPDConfigBuilder

    def _get_template_sub_dir(self):
        return "openbgpd"

    @classmethod
    def add_arguments(cls, parser):
        super(OpenBGPDCommand, cls).add_arguments(parser)

        parser.add_argument(
            "--local-files-dir",
            help="The directory where .local files are located, from the "
                 "route server's perspective.",
            default="/etc/bgpd",
            dest="local_files_dir"
        )

        parser.add_argument(
            "--use-local-files",
            help="Enable the inclusion of .local files into the generated "
                 "OpenBGPD configuration. "
                 "The list of available .local files IDs follows: {}".format(
                     ", ".join(OpenBGPDConfigBuilder.LOCAL_FILES_IDS)
                 ),
            nargs="*",
            choices=OpenBGPDConfigBuilder.LOCAL_FILES_IDS,
            metavar="FILE_ID",
            dest="local_files")

    def _set_cfg_builder_params(self):
        self.cfg_builder_params["local_files_dir"] = self.args.local_files_dir
        self.cfg_builder_params["local_files"] = self.args.local_files

class HTMLCommand(TemplateRenderingCommands):

    COMMAND_NAME = "html"
    COMMAND_HELP = ("Build an HTML descriptive page containing the "
                    "textual representation of the route server "
                    "configuration.")

    def _get_builder_class(self):
        return ConfigBuilder

    def _get_template_sub_dir(self):
        return "html"

class DumpTemplateContextCommand(TemplateRenderingCommands):

    COMMAND_NAME = "template-context"
    COMMAND_HELP = ("Dump the context used to build templates, that is the "
                    "data and the variables that can be consumed within a "
                    "template to build the output configuration.")

    def _get_builder_class(self):
        return TemplateContextDumper

    def _get_template_sub_dir(self):
        return "template-context"

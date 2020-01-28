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

import sys
import yaml

from .base import ARouteServerCommand

from ..config.base import convert_deprecated
from ..config.general import ConfigParserGeneral
from ..config.program import program_config

class ShowConfigCommand(ARouteServerCommand):

    NEEDS_CONFIG = True

    COMMAND_NAME = "show_config"
    COMMAND_HELP = ("Show the current general configuration "
                    "settings and highlight options which are "
                    "missing or left to their default settings.")

    @classmethod
    def add_arguments(cls, parser):
        super(ShowConfigCommand, cls).add_arguments(parser)

        parser.add_argument(
            "--general",
            help="General route server configuration file.",
            metavar="FILE",
            dest="cfg_general")

    def run(self):
        current_config_path = program_config.get("cfg_general")
        self.show_config(current_config_path, sys.stdout)

    @staticmethod
    def show_config(current_config_path, output):

        def wr_line(configured, level, line):
            if configured is True:
                status = "configured"
            elif configured is False:
                status = "default"
            else:
                status = ""

            output.write("{status:<15} {indent}{line}\n".format(
                status=status,
                indent="  " * level,
                line=line
            ))

        with open(current_config_path, "r") as f:
            current_config = yaml.safe_load(f)
        convert_deprecated(current_config["cfg"])

        distrib = ConfigParserGeneral()
        distrib._load_from_yaml("cfg:\n"
                                "  rs_as: 65534\n"
                                "  router_id: 192.0.2.1\n")
        distrib.parse()
        del distrib["communities"]
        del distrib["custom_communities"]

        ordered_schema = ConfigParserGeneral.get_schema()
        del ordered_schema["cfg"]["communities"]
        del ordered_schema["cfg"]["custom_communities"]

        def get_val_repr(val):
            if isinstance(val, dict):
                return ", ".join("{}: {}".format(k, v) for k, v in sorted(val.items()))
            else:
                return str(val).strip()

        def iterate(ordered_schema, distrib, current, level=0):
            for k in ordered_schema:
                if current is distrib:
                    configured = False
                else:
                    configured = k in current

                iterate_over = current if configured else distrib

                if isinstance(ordered_schema[k], dict):

                    wr_line(None, level, k + ":")
                    iterate(ordered_schema[k], distrib[k], iterate_over[k],
                            level + 1)

                elif isinstance(ordered_schema[k], list) or \
                    isinstance(iterate_over[k], list):

                    wr_line(configured, level, k + ":")
                    for v in iterate_over[k]:
                        wr_line(configured, level, "  - " + get_val_repr(v))

                else:
                    v = get_val_repr(iterate_over[k])
                    wr_line(configured, level, "{}: {}".format(k, v))

        iterate(ordered_schema, distrib.cfg, current_config)

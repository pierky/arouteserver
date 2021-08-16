# Copyright (C) 2017-2021 Pier Carlo Chiodi
# Copyright (C) 2021 Vilhelm Prytz
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

import logging

from .base import ARouteServerCommand
from ..config.program import program_config

from ..config.general import ConfigParserGeneral
from ..config.clients import ConfigParserClients


class CheckConfigCommand(ARouteServerCommand):
    COMMAND_NAME = "check-config"
    COMMAND_HELP = (
        "This command will check if the configuration "
        "files for ARouteServer are valid."
    )

    NEEDS_CONFIG = True

    @classmethod
    def add_arguments(cls, parser):
        super(CheckConfigCommand, cls).add_arguments(parser)

        group = parser.add_argument_group(
            title="Route server configuration",
            description="The following arguments override those provided "
            "in the program's configuration file.",
        )

        group.add_argument(
            "--general",
            help="General route server configuration file.",
            metavar="FILE",
            dest="cfg_general",
        )

        group.add_argument(
            "--clients",
            help="Route server clients configuration file.",
            metavar="FILE",
            dest="cfg_clients",
        )

    def check_config(self):
        general = ConfigParserGeneral()
        general.load(self.general_path)
        general.parse()

        clients = ConfigParserClients(general_cfg=general)
        clients.load(self.clients_path)
        clients.parse()

    def run(self):
        self.general_path = program_config.get("cfg_general")
        self.clients_path = program_config.get("cfg_clients")

        if self.args.cfg_general:
            self.general_path = self.args.cfg_general

        if self.args.cfg_clients:
            self.clients_path = self.args.cfg_clients

        logging.info(f"Checking configuration files {self.general_path} and {self.clients_path}...")

        self.check_config()

        return True

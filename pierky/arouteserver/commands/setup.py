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

from .base import ARouteServerCommand

from ..config.program import program_config

class SetupCommand(ARouteServerCommand):

    COMMAND_NAME = "setup"
    COMMAND_HELP = ("Perform the setup of the system by copying "
                    "configuration files and templates in the proper "
                    "directories. Confirmation before each action will "
                    "be asked.")

    @classmethod
    def add_arguments(cls, parser):
        super(SetupCommand, cls).add_arguments(parser)

        parser.add_argument(
            "--dest-dir",
            type=str,
            help="Directory where the program's configuration files and "
                 "templates will be stored.",
            dest="dest_dir")

    def run(self):
        return program_config.setup(destination_directory=self.args.dest_dir)

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

import logging
from logging.config import fileConfig
import os

from ..config.program import program_config
from ..errors import MissingFileError

class ARouteServerCommand(object):

    def __init__(self, args):
        self.args = args

    @classmethod
    def add_arguments(cls, parser):
        pass

    @classmethod
    def add_program_config_arguments(cls, parser):

        parser.add_argument(
            "--cfg",
            help="ARouteServer configuration file.",
            metavar="FILE",
            dest="cfg_program")

        group = parser.add_argument_group(
            title="Program configuration",
            description="The following arguments override those provided "
                        "in the program's configuration file."
        )

        group.add_argument(
            "--cache-dir",
            help="Cache directory.",
            metavar="DIR",
            dest="cache_dir")

        group.add_argument(
            "--logging-config-file",
            help="Logging configuration file, in Python fileConfig() format ("
                "https://docs.python.org/2/library/logging.config.html"
                "#configuration-file-format)",
            dest="logging_config_file")

    def setup(self):
        logging_setted_up = False

        def setup_logging(path):
            if not os.path.exists(path):
                raise MissingFileError(path)
            try:
                fileConfig(path)
                return True
            except Exception as e:
                logging.error(
                    "Error processing the logging configuration file "
                    "{}: {}".format(path, str(e))
                )
                return False

        if self.args.logging_config_file:
            if not setup_logging(self.args.logging_config_file):
                return False
            logging_setted_up = True

        if self.args.cfg_program:
            program_config.load(self.args.cfg_program)

        # Logging setup: if no command line arg given, use the path from
        # program's config file.

        if not logging_setted_up:
            log_ini_path = program_config.get_cfg_file_path("logging_config_file")
            if log_ini_path:
                if not setup_logging(log_ini_path):
                    return False

        return True

    def get_cfg_path(self, arg_name):
        args_dict = vars(self.args)
        if arg_name in args_dict and args_dict[arg_name]:
            return args_dict[arg_name]
        return program_config.get_cfg_file_path(arg_name)

    def get_cfg_val(self, arg_name):
        args_dict = vars(self.args)
        if arg_name in args_dict and args_dict[arg_name]:
            return args_dict[arg_name]
        return program_config.cfg[arg_name]

    def run(self):
        raise NotImplementedError()

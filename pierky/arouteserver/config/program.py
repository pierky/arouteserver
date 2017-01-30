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
# along with this program.  Ifnot, see <http://www.gnu.org/licenses/>.

from copy import deepcopy
import logging
import yaml

from ..errors import ConfigError, ARouteServerError


class ConfigParserProgram(object):

    DEFAULT_CFG_DIR = "/etc/arouteserver"
    DEFAULT_CFG_PATH = "{}/arouteserver.yml".format(DEFAULT_CFG_DIR)

    DEFAULT = {
        "logging_config_file": "{}/log.ini".format(DEFAULT_CFG_DIR),

        "cfg_general": "{}/general.yml".format(DEFAULT_CFG_DIR),
        "cfg_clients": "{}/clients.yml".format(DEFAULT_CFG_DIR),
        "cfg_bogons": "{}/bogons.yml".format(DEFAULT_CFG_DIR),

        "template_dir": "{}/templates".format(DEFAULT_CFG_DIR),
        "template_name": "main.j2",

        "cache_dir": "/var/lib/arouteserver",

        "bgpq3_path": "bgpq3",
        "cache_expiry_time": 43200
    }

    def __init__(self):
        self.cfg = deepcopy(self.DEFAULT)

    def load(self, path):
        try:
            with open(path, "r") as f:
                self.cfg.update(yaml.load(f.read()))
        except Exception as e:
            logging.error("An error occurred while reading global "
                          "configuration at {}: {}".format(path, str(e)))
            raise ConfigError()

program_config = ConfigParserProgram()

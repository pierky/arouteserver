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


import logging

from .base import ConfigParserBase
from .validators import ValidatorPrefixListEntry
from ..errors import ConfigError, ARouteServerError


class ConfigParserBogons(ConfigParserBase):

    ROOT = "bogons"

    def parse(self):
        """
        Contents of cfg dict is updated/normalized by validators.
        """

        if "bogons" not in self.cfg:
            raise ConfigError("Missing 'bogons' top element.")

        errors = False

        for bogon in self.cfg["bogons"]:
            try:
                bogon = ValidatorPrefixListEntry().validate(bogon)
            except ARouteServerError as e:
                msg = "Error in bogon definition"
                if str(e):
                    msg += ": {}.".format(str(e))
                logging.error(msg)
                errors = True

        if errors:
            raise ConfigError()

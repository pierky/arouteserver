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

from .base import ConfigParserBase
from .validators import ValidatorROA
from ..errors import ConfigError, ARouteServerError


class ConfigParserROAEntries(ConfigParserBase):

    ROOT = "roas"

    def parse(self):
        """
        Contents of cfg dict is updated/normalized by validators.
        """

        if "roas" not in self.cfg:
            raise ConfigError("Missing 'roas' top element.")

        errors = False

        for roa in self.cfg["roas"]:
            try:
                roa = ValidatorROA().validate(roa)
            except ARouteServerError as e:
                if str(e):
                    logging.error("Error in ROAs definition: {}.".format(str(e)))
                else:
                    logging.error("Error in ROAs definition")
                errors = True

        if errors:
            raise ConfigError()

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
from .validators import *
from ..errors import ConfigError, ARouteServerError


class ConfigParserASNS(ConfigParserBase):

    ROOT = "asns"

    def parse(self):
        if "clients" in self.cfg:
            del self.cfg["clients"]
        if "asns" not in self.cfg:
            self.cfg["asns"] = {}
            return

        errors = False

        schema = {
            "as_sets": ValidatorListOf(ValidatorASSet,
                                       mandatory=False)
        }

        for asn in self.cfg["asns"]:
            try:
                if not asn.startswith("AS"):
                    raise ConfigError()
                if not ValidatorASN().validate(asn[2:]):
                    raise ConfigError()
            except ConfigError:
                logging.error(
                    "Invalid ASN format in 'asns' section for '{}': "
                    "it must be in the 'AS<asn>' format.".format(asn)
                )
                errors = True

            try:
                ConfigParserBase.validate(schema, self.cfg["asns"][asn], "asns")
            except ARouteServerError as e:
                err_msg = ("One or more errors occurred while processing "
                           "the 'asns' configuration for '{}'".format(asn))
                if str(e):
                    err_msg += ": " + str(e)
                logging.error(err_msg)
                errors = True

        if errors:
            raise ConfigError()

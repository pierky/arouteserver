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

import json
import logging

from six.moves.urllib.request import urlopen
from six.moves.urllib.error import HTTPError

from .cached_objects import CachedObject
from .errors import RPKIValidatorCacheError


class RIPE_RPKI_ROAs(CachedObject):

    DEFAULT_URL = "http://localcert.ripe.net:8088/export.json"

    def __init__(self, *args, **kwargs):
        CachedObject.__init__(self, *args, **kwargs)

        self.url = kwargs.get("ripe_rpki_validator_url",
                              self.DEFAULT_URL)

        self.roas = {}

    def load_data(self):
        logging.debug("Downloading RIPE RPKI cache")

        CachedObject.load_data(self)

        self.roas = self.raw_data

    def _get_object_filename(self):
        return "ripe-rpki-cache.json"

    def _get_data(self):
        try:
            response = urlopen(self.url)
        except HTTPError as e:
            raise RPKIValidatorCacheError(
                "HTTP error while retrieving ROAs from "
                "RIPE RPKI Validator cache ({}): "
                "code: {}, reason: {} - {}".format(
                    self.url, e.code, e.reason, str(e)
                )
            )
        except Exception as e:
            raise RPKIValidatorCacheError(
                "Error while retrieving ROAs from "
                "RIPE RPKI Validator cache ({}): {}".format(
                    self.url, str(e)
                )
            )

        try:
            roas = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise RPKIValidatorCacheError(
                "Error while parsing ROAs from "
                "RIPE RPKI Validator cache ({}): {}".format(
                    self.url, str(e)
                )
            )

        return roas

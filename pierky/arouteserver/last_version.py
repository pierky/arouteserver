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

import json
import logging

from six.moves.urllib.request import urlopen
from six.moves.urllib.error import HTTPError

from .cached_objects import CachedObject
from .errors import LastVersionCheckingError


class LastVersion(CachedObject):

    def __init__(self, *args, **kwargs):
        CachedObject.__init__(self, *args, **kwargs)

        self.last_version = None

    def load_data(self):
        CachedObject.load_data(self)

        self.last_version = self.raw_data

    def _get_object_filename(self):
        return "last_version.json"

    def _get_data(self):
        logging.info("Checking latest version")

        url = "https://pypi.python.org/pypi/arouteserver/json"

        try:
            response = urlopen(url, timeout=10)
        except HTTPError as e:
            raise LastVersionCheckingError(
                "HTTP error while retrieving latest version info from "
                "PyPI ({}): code: {}, reason: {} - {}".format(
                    url, e.code, e.reason, str(e)
                )
            )
        except Exception as e:
            raise LastVersionCheckingError(
                "Error while retrieving latest version info from "
                "PyPI ({}): {}".format(
                    url, str(e)
                )
            )

        try:
            info = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise LastVersionCheckingError(
                "Error while parsing latest version info from "
                "PyPI ({}): {}".format(
                    url, str(e)
                )
            )

        return info["info"]["version"]

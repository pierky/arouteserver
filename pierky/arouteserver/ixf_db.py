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
import six
from six.moves.urllib.request import urlopen

from .errors import IXFDBError, IXFDBSchemaError, EuroIXSchemaError

class IXFDB(object):

    def __init__(self, input_object="https://db.ix-f.net/api/ixp"):
        self.raw_data = None

        if isinstance(input_object, dict):
            self.raw_data = input_object
        elif isinstance(input_object, six.string_types):
            try:
                response = urlopen(input_object)
                raw = response.read().decode("utf-8")
            except Exception as e:
                raise IXFDBError(
                    "Error while retrieving IX-F DB "
                    "JSON file from {}: {}".format(
                        input_object, str(e)
                    )
                )
        else:
            raw = input_object.read().decode("utf-8")

        if not self.raw_data:
            try:
                self.raw_data = json.loads(raw)
            except Exception as e:
                raise EuroIXSchemaError(
                    "Error while processing JSON data: {}".format(str(e))
                )

        if "data" not in self.raw_data:
            raise IXFDBSchemaError(
                "Missing 'data' element"
            )

        if not isinstance(self.raw_data["data"], list):
            raise IXFDBSchemaError(
                "The 'data' element is not a list."
            )

        self.ixp_list = self.raw_data["data"]

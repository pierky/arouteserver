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
import os
import time

from .errors import CachedObjectsError, ExternalDataNoInfoError


class CachedObject(object):

    DEFAULT_EXPIRY = 43200
    MISSING_INFO_EXCEPTION = ExternalDataNoInfoError

    def __init__(self, **kwargs):
        self.cache_dir = kwargs.get("cache_dir", "var")
        if not self.cache_dir:
            raise CachedObjectsError("Missing cache directory")

        self.cache_expiry_time = kwargs.get("cache_expiry",
                                            self.DEFAULT_EXPIRY)
        self.raw_data = None

    def _get_object_filename(self):
        raise NotImplementedError()

    def _get_object_filepath(self):
        return os.path.join(self.cache_dir, self._get_object_filename())

    def load_data_from_cache(self):
        file_path = self._get_object_filepath()

        if not os.path.isfile(file_path):
            return False

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            logging.error(
                "Error while reading data from cache: {} - {}".format(
                    file_path, str(e)
                )
            )
            return False

        if "ts" not in data:
            return False
        if "data" not in data:
            return False

        epoch_time = int(time.time())

        if data["ts"] <= epoch_time - self.cache_expiry_time:
            return False

        if data["data"] is None:
            logging.debug(
                "Cache hit: missing info {}".format(self._get_object_filepath())
            )
            raise self.MISSING_INFO_EXCEPTION()

        self.raw_data = data["data"]
        return True

    def _get_data(self):
        raise NotImplementedError()

    def load_data(self):
        if self.load_data_from_cache():
            logging.debug("Cache hit: {}".format(self._get_object_filepath()))
            return

        # Children classes raise ExternalDataNoInfoError-derived exceptions
        # when no information can be obtained for the requested resource.
        # Here, the data is saved to the file even in case of missing info,
        # then the original exception is re-raised.
        try:
            self.raw_data = self._get_data()
        except ExternalDataNoInfoError:
            self.save_data_to_cache()
            raise

        self.save_data_to_cache()

    def save_data_to_cache(self):
        file_path = self._get_object_filepath()

        epoch_time = int(time.time())

        cache_data = {
            "ts": epoch_time,
            "data": self.raw_data
        }

        try:
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            with open(file_path, "w") as f:
                json.dump(cache_data, f)
        except Exception as e:
            raise CachedObjectsError(
                "Error while saving data to the cache: {}".format(str(e))
            )

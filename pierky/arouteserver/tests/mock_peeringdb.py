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

import os
import json
import mock

from ..cached_objects import CachedObject
from ..peering_db import PeeringDBInfo, PeeringDBNet


def mock_peering_db(data_dir=None):

    def get_data_from_peeringdb(self):
        path = "{}/{}".format(
            data_dir or os.path.dirname(__file__),
            self._get_peeringdb_url()
        )
        with open(path, "r") as f:
            return json.load(f)

    mock_get_data_from_peeringdb = mock.patch.object(
        PeeringDBInfo, "_get_data_from_peeringdb", autospec=True
    ).start()
    mock_get_data_from_peeringdb.side_effect = get_data_from_peeringdb

    def get_url_net(self):
        return "net_{}.json".format(self.asn)

    mock_get_url_net = mock.patch.object(
        PeeringDBNet, "_get_peeringdb_url", autospec=True
    ).start()
    mock_get_url_net.side_effect = get_url_net

    def load_data_from_cache(self):
        return False

    mock_load_data_from_cache = mock.patch.object(
        CachedObject, "load_data_from_cache", autospec=True
    ).start()
    mock_load_data_from_cache.side_effect = load_data_from_cache

    def save_data_to_cache(self):
        return

    mock_save_data_to_cache = mock.patch.object(
        CachedObject, "save_data_to_cache", autospec=True
    ).start()
    mock_save_data_to_cache.side_effect = save_data_to_cache

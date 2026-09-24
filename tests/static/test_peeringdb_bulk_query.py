# Copyright (C) 2017-2026 Pier Carlo Chiodi
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
import tempfile
import time
import unittest
from unittest.mock import MagicMock
try:
    import mock
except ImportError:
    import unittest.mock as mock

from pierky.arouteserver.peering_db import session_cache, PeeringDBNet
from pierky.arouteserver.errors import PeeringDBNoInfoError


def _no_cache():
    session_cache.clear()

    mock_load_data_from_cache = mock.patch(
        "pierky.arouteserver.peering_db.CachedObject.load_data_from_cache",
        autospec=True
    ).start()
    mock_load_data_from_cache.side_effect = lambda _: False

    mock_save_data_to_cache = mock.patch(
        "pierky.arouteserver.peering_db.CachedObject.save_data_to_cache",
        autospec=True
    ).start()
    mock_save_data_to_cache.side_effect = lambda _: None


class TestPeeringDBBulkQueryCache(unittest.TestCase):

    def setUp(self):
        _no_cache()
        PeeringDBNet.BULK_QUERY_CACHE.clear()

    def tearDown(self):
        mock.patch.stopall()

    def test_peeringdb_bulk_query_cache_1(self):
        """PeeringDB bulk query cache: hit"""

        mock_read_from_url = MagicMock()
        mock.patch.object(PeeringDBNet, "_read_from_url", mock_read_from_url).start()

        # Mimic a bulk query returning data for AS1.
        mock_read_from_url.return_value = open("tests/static/peeringdb_data/net_1.json", "r").read()
        PeeringDBNet.populate_bulk_query_cache([1])

        mock_read_from_url.reset_mock()

        net = PeeringDBNet(1)
        net.load_data()

        # No further calls to _read_from_url expected, since the record for the
        # requested network (AS1) is already in the cache.
        self.assertEqual(mock_read_from_url.call_count, 0)

        self.assertEqual(net.irr_as_sets, ["AS-AS1"])

    def test_peeringdb_bulk_query_cache_2(self):
        """PeeringDB bulk query cache: hit missed"""

        mock_read_from_url = MagicMock()
        mock.patch.object(PeeringDBNet, "_read_from_url", mock_read_from_url).start()

        # Mimic a bulk query returning data for AS1, which in this case is not
        # the ASN for which info will be required.
        mock_read_from_url.return_value = open("tests/static/peeringdb_data/net_1.json", "r").read()
        PeeringDBNet.populate_bulk_query_cache([1])

        mock_read_from_url.reset_mock()

        # Now make _read_from_url returning the actual data for AS3, the net
        # for which info are required.
        mock_read_from_url.return_value = open("tests/static/peeringdb_data/net_3.json", "r").read()

        net = PeeringDBNet(3)
        net.load_data()

        # Expecting one further call to _read_from_url, since AS3 was not part
        # of the bulk query cache.
        self.assertEqual(mock_read_from_url.call_count, 1)

        self.assertEqual(net.irr_as_sets, ["AS-AS3"])

    def test_peeringdb_bulk_query_cache_3(self):
        """PeeringDB bulk query cache: hit with no data"""

        mock_read_from_url = MagicMock()
        mock.patch.object(PeeringDBNet, "_read_from_url", mock_read_from_url).start()

        # Mimic a bulk query returning no data. AS1 is part of the bulk query.
        mock_read_from_url.return_value = '{"data": []}'
        PeeringDBNet.populate_bulk_query_cache([1])

        mock_read_from_url.reset_mock()

        net = PeeringDBNet(1)
        with self.assertRaises(PeeringDBNoInfoError):
            net.load_data()

        # Expecting no further calls to _read_from_url, since AS1 was part of
        # the bulk query (even though no data were present in PeeringDB for it).
        self.assertEqual(mock_read_from_url.call_count, 0)

    def test_peeringdb_bulk_query_cache_4(self):
        """PeeringDB bulk query cache: ASNs already loaded are not queried again"""

        mock_read_from_url = MagicMock()
        mock.patch.object(PeeringDBNet, "_read_from_url", mock_read_from_url).start()

        mock_read_from_url.return_value = open("tests/static/peeringdb_data/net_1.json", "r").read()

        # Two enrichers asking for the same ASN within the same run.
        PeeringDBNet.populate_bulk_query_cache([1])
        PeeringDBNet.populate_bulk_query_cache([1])

        self.assertEqual(mock_read_from_url.call_count, 1)

    def test_peeringdb_bulk_query_cache_5(self):
        """PeeringDB bulk query cache: ASNs given as strings"""

        mock_read_from_url = MagicMock()
        mock.patch.object(PeeringDBNet, "_read_from_url", mock_read_from_url).start()

        # The enrichers pass ASNs as strings; AS1 is found, AS2 is not.
        mock_read_from_url.return_value = open("tests/static/peeringdb_data/net_1.json", "r").read()
        PeeringDBNet.populate_bulk_query_cache(["1", "2"])

        mock_read_from_url.reset_mock()

        net = PeeringDBNet(1)
        net.load_data()
        self.assertEqual(net.irr_as_sets, ["AS-AS1"])

        with self.assertRaises(PeeringDBNoInfoError):
            PeeringDBNet(2).load_data()

        # Neither lookup should have needed a further request.
        self.assertEqual(mock_read_from_url.call_count, 0)

    def test_peeringdb_bulk_query_cache_6(self):
        """PeeringDB bulk query cache: ASNs valid in the on-disk cache are not queried"""

        mock_read_from_url = MagicMock()
        mock.patch.object(PeeringDBNet, "_read_from_url", mock_read_from_url).start()

        mock_read_from_url.return_value = open("tests/static/peeringdb_data/net_1.json", "r").read()

        mock_is_cached = mock.patch.object(PeeringDBNet, "_is_cached").start()

        mock_is_cached.return_value = True
        PeeringDBNet.populate_bulk_query_cache([1], cache_dir="var", cache_expiry={"pdb_info": 3600})
        self.assertEqual(mock_read_from_url.call_count, 0)

        mock_is_cached.return_value = False
        PeeringDBNet.populate_bulk_query_cache([1], cache_dir="var", cache_expiry={"pdb_info": 3600})
        self.assertEqual(mock_read_from_url.call_count, 1)

class TestPeeringDBNetIsCached(unittest.TestCase):

    EXPIRY = {"pdb_info": 3600}

    def setUp(self):
        self.cache_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.cache_dir.cleanup()

    def _write(self, asn, ts, data):
        path = "{}/peeringdb_net_{}.json".format(self.cache_dir.name, asn)
        with open(path, "w") as f:
            json.dump({"ts": ts, "data": data}, f)

    def _is_cached(self, asn):
        return PeeringDBNet._is_cached(asn, self.cache_dir.name, self.EXPIRY)

    def test_is_cached_fresh(self):
        """PeeringDBNet._is_cached: fresh entry"""
        self._write(1, int(time.time()), [{"asn": 1}])
        self.assertTrue(self._is_cached(1))

    def test_is_cached_expired(self):
        """PeeringDBNet._is_cached: expired entry"""
        self._write(1, int(time.time()) - 7200, [{"asn": 1}])
        self.assertFalse(self._is_cached(1))

    def test_is_cached_missing(self):
        """PeeringDBNet._is_cached: no entry"""
        self.assertFalse(self._is_cached(1))

    def test_is_cached_fresh_no_data(self):
        """PeeringDBNet._is_cached: fresh 'no data for this network' entry"""
        self._write(1, int(time.time()), None)
        self.assertTrue(self._is_cached(1))

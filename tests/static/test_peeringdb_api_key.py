# Copyright (C) 2017-2025 Pier Carlo Chiodi
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
import unittest
from unittest.mock import MagicMock
try:
    import mock
except ImportError:
    import unittest.mock as mock
from tempfile import TemporaryDirectory

from requests.exceptions import HTTPError

from pierky.arouteserver.peering_db import session_cache, PeeringDBNet
from pierky.arouteserver.errors import PeeringDBError
from pierky.arouteserver.version import __version__


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


class TestPeeringDBAPIKey(unittest.TestCase):

    def setUp(self):
        _no_cache()

        self.mock_requests_session = mock.MagicMock()
        mock_requests_session_get = mock.MagicMock()
        self.mock_requests_session_response = mock.MagicMock()
        self.mock_requests_session_response.content = open("tests/static/peeringdb_data/net_1.json", "rb").read()
        mock_requests_session_get.return_value = self.mock_requests_session_response
        self.mock_requests_session.get = mock_requests_session_get
        mock.patch(
            "pierky.arouteserver.peering_db._get_request_session",
            mock.MagicMock(
                return_value=self.mock_requests_session
            )
        ).start()

    def tearDown(self):
        mock.patch.stopall()

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_peeringdb_api_key_empty(self):
        """PeeringDB API key: empty"""
        PeeringDBNet(1).load_data()
        self.mock_requests_session.get.assert_called_once()
        self.assertEqual(self.mock_requests_session.get.call_args[1], {"headers": {
            "User-Agent": "arouteserver/{}".format(__version__)
        }})

    @mock.patch.dict(os.environ, {"SECRET_PEERINGDB_API_KEY": "test"})
    def test_peeringdb_api_via_env_var(self):
        """PeeringDB API key: via env var"""
        PeeringDBNet(1).load_data()
        self.mock_requests_session.get.assert_called_once()
        call_arg = self.mock_requests_session.get.call_args[1]
        self.assertIn("headers", call_arg)
        headers = call_arg["headers"]
        self.assertIn("User-Agent", headers)
        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Api-Key test")

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_peeringdb_api_via_file(self):
        """PeeringDB API key: via file"""

        with TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "fake_peeringdb_api.key")
            with open(temp_file, "w") as f:
                f.write("The Key From The File")

            mock.patch(
                "pierky.arouteserver.peering_db.PeeringDBInfo.PEERING_DB_API_KEY_WELL_KNOWN_FILES",
                (temp_file, )
            ).start()

            PeeringDBNet(1).load_data()
            self.mock_requests_session.get.assert_called_once()
            call_arg = self.mock_requests_session.get.call_args[1]
            self.assertIn("headers", call_arg)
            headers = call_arg["headers"]
            self.assertIn("User-Agent", headers)
            self.assertIn("Authorization", headers)
            self.assertEqual(headers["Authorization"], "Api-Key The Key From The File")

    @mock.patch.dict(os.environ, {"SECRET_PEERINGDB_API_KEY": "The Key From The Env Var"})
    def test_peeringdb_api_priorities(self):
        """PeeringDB API key: env var wins over file"""

        with TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "fake_peeringdb_api.key")
            with open(temp_file, "w") as f:
                f.write("The Key From The File")

            mock.patch(
                "pierky.arouteserver.peering_db.PeeringDBInfo.PEERING_DB_API_KEY_WELL_KNOWN_FILES",
                (temp_file, )
            ).start()

            PeeringDBNet(1).load_data()
            self.mock_requests_session.get.assert_called_once()
            call_arg = self.mock_requests_session.get.call_args[1]
            self.assertIn("headers", call_arg)
            headers = call_arg["headers"]
            self.assertIn("User-Agent", headers)
            self.assertIn("Authorization", headers)
            self.assertEqual(headers["Authorization"], "Api-Key The Key From The Env Var")

    def test_peeringdb_api_429_handling(self):
        """PeeringDB API key: 429 error handling"""

        def raise_exc():
            mock_response = mock.MagicMock()
            mock_response.status_code = 429
            raise HTTPError(
                response=mock_response
            )

        self.mock_requests_session_response.raise_for_status = raise_exc

        with self.assertRaises(PeeringDBError) as context:
            PeeringDBNet(1).load_data()

            assert "Please consider using a PeeringDB API key to perform authentication, which could help mitigating the effects of anonymous API query rate-limit." in str(context)


class TestPeeringDB429ErrorHandling(unittest.TestCase):

    def setUp(self):
        _no_cache()

        mock.patch.object(
            PeeringDBNet, "_get_peeringdb_url",
            MagicMock(
                return_value="https://mock.codes/429"
            )
        ).start()

    def tearDown(self):
        mock.patch.stopall()

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_peeringdb_429_handling(self):
        """PeeringDB API: 429 error handling"""
        with self.assertRaises(PeeringDBError) as context:
            PeeringDBNet(1).load_data()

            assert "Please consider using a PeeringDB API key to perform authentication, which could help mitigating the effects of anonymous API query rate-limit." in str(context)

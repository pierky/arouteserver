# Copyright (C) 2017-2022 Pier Carlo Chiodi
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
import os
import shutil
import six
import tempfile
try:
    import mock
except ImportError:
    import unittest.mock as mock
import time
import unittest
import datetime


from pierky.arouteserver.ripe_rpki_cache import RIPE_RPKI_ROAs
from pierky.arouteserver.errors import RPKIValidatorCacheError


class TestRPKICache(unittest.TestCase):

    ROAS_MUST_BE_PRESENT = [
        ("103.10.112.0/22", 0, 32, {
            "ripe": "APNIC RPKI Root",
            "ntt": "apnic",
            "rpki-client": "apnic"}),
        ("185.168.163.0/24", 4214120002, 24, {
            "ripe": "RIPE NCC RPKI Root",
            "ntt": "ripe",
            "rpki-client": "ripe"}),
        ("154.127.54.0/24", 397423, 24, {
            "ripe": "AfriNIC RPKI Root",
            "ntt": "afrinic",
            "rpki-client": "afrinic"}),
        ("45.229.7.0/24", 266676, 24, {
            "ripe": "LACNIC RPKI Root",
            "ntt": "lacnic",
            "rpki-client": "lacnic"})
    ]

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")

    def tearDown(self):
        mock.patch.stopall()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_file_path(self, content):
        file_path = os.path.join(self.temp_dir, "data.json")
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    def _setup_obj(self, raw_content):
        self.obj = RIPE_RPKI_ROAs(
            cache_dir=self.temp_dir,
            ripe_rpki_validator_url=[self._get_file_path(raw_content)]
        )
        self.obj.load_data()
        return self.obj.roas["roas"]

    def _roa_is_present(self, roas, prefix, asn, max_len, ta):
        for roa in roas:
            if roa["prefix"] == prefix and \
               roa["asn"] == "AS{}".format(asn) and \
               roa["maxLength"] == max_len and \
               roa["ta"] == ta:
                return True
        self.fail("ROA not found: {}, AS {}, maxLen {} TA {}".format(
            prefix, asn, max_len, ta
        ))

    def test_010(self):
        """RPKI ROAs: RIPE Validator TAs"""
        roas = self._setup_obj(
            open("tests/static/data/rpki_roas_ripe.json").read()
        )
        provider = "ripe"
        for prefix, asn, max_len, tas in self.ROAS_MUST_BE_PRESENT:
            self._roa_is_present(
                roas,
                prefix, asn, max_len, tas[provider]
            )

    def test_020(self):
        """RPKI ROAs: NTT TAs"""
        roas = self._setup_obj(
            open("tests/static/data/rpki_roas_ntt.json").read()
        )
        provider = "ntt"
        for prefix, asn, max_len, tas in self.ROAS_MUST_BE_PRESENT:
            self._roa_is_present(
                roas,
                prefix, asn, max_len, tas[provider]
            )

    @mock.patch.object(
        RIPE_RPKI_ROAs,
        "_get_utc_now",
        return_value=datetime.datetime(2021, 7, 21, 17, 26)
    )
    def test_030(self, _):
        """RPKI ROAs: rpki-client TAs"""
        roas = self._setup_obj(
            open("tests/static/data/rpki_roas_rpki-client.json").read()
        )
        provider = "rpki-client"
        for prefix, asn, max_len, tas in self.ROAS_MUST_BE_PRESENT:
            self._roa_is_present(
                roas,
                prefix, asn, max_len, tas[provider]
            )

    def test_100(self):
        """RPKI ROAs: different formats"""
        roas = self._setup_obj(
            '{'
            '  "roas": ['
            '    { "asn": "AS0", "prefix": "192.0.2.1/32", "maxLength": 32, "ta": "test" }, '
            '    { "asn": "0", "prefix": "192.0.2.2/32", "maxLength": 32, "ta": "test" }, '
            '    { "asn": 0, "prefix": "192.0.2.3/32", "maxLength": 32, "ta": "test" }, '
            '    { "asn": 0, "prefix": "192.0.2.4/32", "maxLength": "32", "ta": "test" }'
            '  ]'
            '}'
        )
        self._roa_is_present(roas, "192.0.2.1/32", 0, 32, "test")
        self._roa_is_present(roas, "192.0.2.2/32", 0, 32, "test")
        self._roa_is_present(roas, "192.0.2.3/32", 0, 32, "test")
        self._roa_is_present(roas, "192.0.2.4/32", 0, 32, "test")

    @mock.patch.object(
        RIPE_RPKI_ROAs,
        "_get_utc_now",
        return_value=datetime.datetime(2030, 12, 31, 23, 59)
    )
    def test_200(self, _):
        """RPKI ROAs: rpki-client expired file"""

        # Same file as in test_030, but this time the mock
        # _get_utc_now is in the future.
        with six.assertRaisesRegex(self, RPKIValidatorCacheError, "was built at .* it will be ignored"):
            roas = self._setup_obj(
                open("tests/static/data/rpki_roas_rpki-client.json").read()
            )

    @mock.patch.object(
        RIPE_RPKI_ROAs,
        "_get_utc_now",
        return_value=datetime.datetime(2021, 7, 21, 17, 26)
    )
    def test_210(self, _):
        """RPKI ROAs: rpki-client expired ROAs"""

        roas = self._setup_obj(
            open("tests/static/data/rpki_roas_rpki-client_expired.json").read()
        )
        self.assertEqual(roas, [])

    @mock.patch.object(
        RIPE_RPKI_ROAs,
        "_get_utc_now",
        return_value=datetime.datetime(2030, 12, 31, 23, 59)
    )
    def test_220(self, _):
        """RPKI ROAs: OctoRPKI expired file"""

        with six.assertRaisesRegex(self, RPKIValidatorCacheError, r"was built at .* it will be ignored"):
            roas = self._setup_obj(
                open("tests/static/data/rpki_roas_octorpki.json").read()
            )

    @mock.patch.object(
        RIPE_RPKI_ROAs,
        "_get_utc_now",
        return_value=datetime.datetime(2030, 12, 31, 23, 59)
    )
    def test_230(self, _):
        """RPKI ROAs: OctoRPKI out of validity"""

        with six.assertRaisesRegex(self, RPKIValidatorCacheError, r"is valid till .* it will be ignored"):
            roas = self._setup_obj(
                open("tests/static/data/rpki_roas_octorpki-validity.json").read()
            )

    @mock.patch.object(
        RIPE_RPKI_ROAs,
        "_get_utc_now",
        return_value=datetime.datetime(2021, 7, 23, 6, 50)
    )
    def test_240(self, _):
        """RPKI ROAs: OctoRPKI valid file"""

        roas = self._setup_obj(
            open("tests/static/data/rpki_roas_octorpki.json").read()
        )
        self.assertEqual(len(roas), 39680)

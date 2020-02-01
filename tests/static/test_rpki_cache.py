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


from pierky.arouteserver.ripe_rpki_cache import RIPE_RPKI_ROAs


class TestRPKICache(unittest.TestCase):

    ROAS_MUST_BE_PRESENT = [
        ("103.10.112.0/22", 0, 32, {
            "ripe": "APNIC RPKI Root",
            "ntt": "apnic"}),
        ("185.168.163.0/24", 4214120002, 24, {
            "ripe": "RIPE NCC RPKI Root",
            "ntt": "ripe"}),
        ("154.127.54.0/24", 397423, 24, {
            "ripe": "AfriNIC RPKI Root",
            "ntt": "afrinic"}),
        ("45.227.254.0/24", 395978, 24, {
            "ripe": "LACNIC RPKI Root",
            "ntt": "lacnic"})
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

    def test_030(self):
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

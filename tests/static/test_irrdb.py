# Copyright (C) 2017-2019 Pier Carlo Chiodi
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


from pierky.arouteserver.errors import ExternalDataNoInfoError
from pierky.arouteserver.irrdb import IRRDBInfo, ASSet, RSet

def load(filename):
    path = os.path.join(os.path.dirname(__file__), "irrdb_data", filename)
    with open(path, "rb") as f:
        return f.read()

class FakeIRRDBObject(IRRDBInfo):

    def _get_data(self):
        return self._run_cmd(["false"])

class TestIRRDBInfo_Base(unittest.TestCase):

    __test__ = False

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")

    def tearDown(self):
        mock.patch.stopall()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def path(self, filename):
        return os.path.join(self.temp_dir, filename)

    def file_exists(self, filename):
        path = self.path(filename)
        self.assertTrue(
            os.path.exists(path) and
            os.path.isfile(path)
        )

    def load(self, filename):
        path = self.path(filename)
        with open(path, "r") as f:
            return f.read()

class TestIRRDBInfo(TestIRRDBInfo_Base):

    __test__ = True

    def setup_obj(self, object_names, cache_expiry=10):
        self.obj = FakeIRRDBObject(
            object_names,
            cache_dir=self.temp_dir,
            cache_expiry=cache_expiry,
            bgpq3_path="false"
        )

    def test_010_as_set_bundle1(self):
        """IRRDB info: base, AS_SET bundle info (1)"""
        self.setup_obj(["AA-two@"])
        self.assertEqual(self.obj.object_names, ["AA-TWO@"])
        self.assertEqual(self.obj.descr, "AA-TWO@")
        self.assertEqual(self.obj.name, "AA_TWO_")
        self.assertEqual(self.obj.source, None)

    def test_010_as_set_bundle3(self):
        """IRRDB info: base, AS_SET bundle info (3)"""
        self.setup_obj(["bb", "Cc_one", "AA-two@"])
        self.assertEqual(self.obj.object_names, ["AA-TWO@", "BB", "CC_ONE"])
        self.assertEqual(self.obj.descr, "AA-TWO@, BB, CC_ONE")
        self.assertEqual(self.obj.name, "AA_TWO__BB_CC_ONE")
        self.assertEqual(self.obj.source, None)

    def test_010_as_set_bundle4(self):
        """IRRDB info: base, AS_SET bundle info (4)"""
        self.setup_obj(["bb", "Cc_one", "AA-two@", "-three"])
        self.assertEqual(self.obj.object_names, ["-THREE", "AA-TWO@", "BB", "CC_ONE"])
        self.assertEqual(self.obj.descr, "-THREE, AA-TWO@, BB and 1 more")
        self.assertTrue(self.obj.name.startswith("_THREE_and_3_more_"))
        self.assertEqual(self.obj.source, None)

    def test_010_as_set_bundle5(self):
        """IRRDB info: base, AS_SET bundle info (5 with RIPE::)"""
        self.setup_obj(["bb", "Cc_one", "AA-two@", "-three", "RIPE::AS-ONE"])
        self.assertEqual(self.obj.object_names, ["-THREE", "AA-TWO@", "BB", "CC_ONE", "RIPE::AS-ONE"])
        self.assertEqual(self.obj.descr, "-THREE, AA-TWO@, BB and 2 more")
        self.assertTrue(self.obj.name.startswith("_THREE_and_4_more_"))
        self.assertEqual(self.obj.source, "RIPE")

    def test_010_as_set_bundle6(self):
        """IRRDB info: base, AS_SET bundle info (5 with RIPE:: and ARIN::)"""
        self.setup_obj(["bb", "RIPE::Cc_one", "AA-two@", "-three", "ARIN::AS-ONE"])
        self.assertEqual(self.obj.object_names, ["-THREE", "AA-TWO@", "ARIN::AS-ONE", "BB", "RIPE::CC_ONE"])
        self.assertEqual(self.obj.descr, "-THREE, AA-TWO@, ARIN::AS-ONE and 2 more")
        self.assertTrue(self.obj.name.startswith("_THREE_and_4_more_"))
        self.assertEqual(self.obj.source, "RIPE")

    def test_010_as_set_bundle7(self):
        """IRRDB info: base, AS_SET bundle info (5 with ARIN:: and RIPE::)"""
        self.setup_obj(["bb", "ARIN::Cc_one", "AA-two@", "-three", "RIPE::AS-ONE"])
        self.assertEqual(self.obj.object_names, ["-THREE", "AA-TWO@", "ARIN::CC_ONE", "BB", "RIPE::AS-ONE"])
        self.assertEqual(self.obj.descr, "-THREE, AA-TWO@, ARIN::CC_ONE and 2 more")
        self.assertTrue(self.obj.name.startswith("_THREE_and_4_more_"))
        self.assertEqual(self.obj.source, "ARIN")

    def test_010_as_set_bundle8(self):
        """IRRDB info: base, AS_SET bundle info (1 with RIPE::)"""
        self.setup_obj(["RIPE::AS-ONE"])
        self.assertEqual(self.obj.object_names, ["RIPE::AS-ONE"])
        self.assertEqual(self.obj.descr, "RIPE::AS-ONE")
        self.assertEqual(self.obj.name, "RIPE__AS_ONE")
        self.assertEqual(self.obj.source, "RIPE")

    def test_010_as_set_bundle8(self):
        """IRRDB info: base, AS_SET bundle info (2 with RIPE:: and ARIN::)"""
        self.setup_obj(["RIPE::AS-ONE", "ARIN::AS-TWO"])
        self.assertEqual(self.obj.object_names, ["ARIN::AS-TWO", "RIPE::AS-ONE"])
        self.assertEqual(self.obj.descr, "ARIN::AS-TWO, RIPE::AS-ONE")
        self.assertEqual(self.obj.name, "ARIN__AS_TWO_RIPE__AS_ONE")
        self.assertEqual(self.obj.source, "RIPE")

    def test_010_as_set_bundle9(self):
        """IRRDB info: base, AS_SET names longer than 64 characters"""

        #                         1         2         3         4         5
        #                12345678901234567890123456789012345678901234567890
        self.setup_obj(["RIPE::AS-A123456789B123456789C123456789D12345678"])
        expected_name = "RIPE__AS_A123456789B123456789C123456789D12345678"
        self.assertEqual(self.obj.name, expected_name)

        #                         1         2         3         4         5
        #                12345678901234567890123456789012345678901234567890
        self.setup_obj(["RIPE::AS-A123456789B123456789C123456789D123456789"])
        expected_part = "RIPE__AS_A123456789B123456789C123456789D12_"
        self.assertEqual(self.obj.name[:len(expected_part)], expected_part)
        self.assertEqual(self.obj.name[len(expected_part)-1], "_")
        self.assertEqual(len("AS_SET_" + self.obj.name + "_prefixes"), 64)
        tag_1 = self.obj.name[len(expected_part):]

        #                         1         2         3         4         5
        #                12345678901234567890123456789012345678901234567890
        self.setup_obj(["RIPE::AS-A123456789B123456789C123456789D1234567890ZZZZ"])
        expected_part = "RIPE__AS_A123456789B123456789C123456789D12_"
        self.assertEqual(self.obj.name[:len(expected_part)], expected_part)
        self.assertEqual(self.obj.name[len(expected_part)-1], "_")
        self.assertEqual(len("AS_SET_" + self.obj.name + "_prefixes"), 64)
        tag_2 = self.obj.name[len(expected_part):]

        self.assertNotEqual(tag_1, tag_2)

    @mock.patch.object(FakeIRRDBObject, "_get_object_filename", return_value="test1_file")
    @mock.patch.object(FakeIRRDBObject, "_run_cmd", return_value="test1")
    def test_011_simple(self, _, run_cmd):
        """IRRDB info: base, simple"""
        self.setup_obj(["TEST"])
        self.obj.load_data()

        self.file_exists("test1_file")

        cached_data = json.loads(self.load("test1_file"))
        self.assertEqual(cached_data["data"], "test1")
        self.assertTrue(cached_data["ts"] > int(time.time()) - 1)

    @mock.patch.object(FakeIRRDBObject, "_get_object_filename", return_value="test2_file")
    @mock.patch.object(FakeIRRDBObject, "_run_cmd", side_effect=ExternalDataNoInfoError)
    def test_012_noexternaldata(self, run_cmd, _):
        """IRRDB info: base, no external data available"""
        self.setup_obj(["TEST"])

        raised = False
        try:
            self.obj.load_data()
        except ExternalDataNoInfoError:
            raised = True
            pass

        self.assertTrue(raised)
        self.assertEqual(run_cmd.call_count, 1)

        self.assertTrue(self.obj.raw_data is None)

        # Verify that cache file is regularly written with empty data.
        self.file_exists("test2_file")
        cached_data = json.loads(self.load("test2_file"))
        self.assertEqual(cached_data["data"], None)
        self.assertTrue(cached_data["ts"] > int(time.time()) - 1)

        # Reuse data from cache.
        self.setup_obj(["TEST"])
        raised = False
        try:
            self.obj.load_data()
        except ExternalDataNoInfoError:
            raised = True
            pass
        self.assertTrue(raised)
        self.assertTrue(self.obj.raw_data is None)

        # No further calls to _run_cmd.
        self.assertEqual(run_cmd.call_count, 1)

    @mock.patch.object(FakeIRRDBObject, "_get_object_filename", return_value="test3_file")
    @mock.patch.object(FakeIRRDBObject, "_run_cmd", return_value="test3")
    def test_013_cache_expired(self, run_cmd, _):
        """IRRDB info: base, cache expired"""
        self.setup_obj(["TEST"], cache_expiry=1)
        self.obj.load_data()

        self.assertEqual(self.obj.raw_data, "test3")
        self.file_exists("test3_file")
        self.assertEqual(run_cmd.call_count, 1)

        time.sleep(2)

        self.setup_obj(["TEST"], cache_expiry=1)
        self.obj.load_data()

        self.assertEqual(self.obj.raw_data, "test3")
        self.file_exists("test3_file")
        self.assertEqual(run_cmd.call_count, 2)

    @mock.patch.object(FakeIRRDBObject, "_get_object_filename", return_value="test4_file")
    @mock.patch.object(FakeIRRDBObject, "_run_cmd", return_value="test4")
    def test_014_corrupted_cache(self, run_cmd, _):
        """IRRDB info: base, corrupted cache file"""
        self.setup_obj(["TEST"])
        self.obj.load_data()

        self.assertEqual(self.obj.raw_data, "test4")
        self.file_exists("test4_file")
        self.assertEqual(run_cmd.call_count, 1)

        with open(self.path("test4_file"), "w") as f:
            f.write("bad things")

        self.setup_obj(["TEST"])
        self.obj.load_data()

        self.assertEqual(self.obj.raw_data, "test4")
        self.file_exists("test4_file")
        self.assertEqual(run_cmd.call_count, 2)

class TestIRRDBInfo_ASSet(TestIRRDBInfo_Base):

    __test__ = True

    def setup_obj(self, object_names, cache_expiry=10):
        self.obj = ASSet(
            object_names,
            cache_dir=self.temp_dir,
            cache_expiry=cache_expiry,
            bgpq3_path="false"
        )

    @mock.patch.object(ASSet, "_run_cmd", return_value=load("asset_test_10.json"))
    def test_010_simple(self, run_cmd):
        """IRRDB info: ASNs, simple"""

        self.setup_obj(["AS-ONE"])
        self.obj.load_data()

        self.assertEqual(sorted(self.obj.asns), [1, 2, 3])
        self.file_exists("AS_ONE-as_set.json")
        run_cmd.assert_called_once()

    @mock.patch.object(ASSet, "_run_cmd", return_value=load("asset_test_10.json"))
    def test_011_from_cache(self, run_cmd):
        """IRRDB info: ASNs, from cache"""
        for i in [1, 2]:
            self.setup_obj(["AS-ONE"])
            self.obj.load_data()

            self.assertEqual(sorted(self.obj.asns), [1, 2, 3])
            self.file_exists("AS_ONE-as_set.json")
            run_cmd.assert_called_once()

    @mock.patch.object(ASSet, "_run_cmd", return_value=load("asset_test_10.json"))
    def test_012_cache_expired(self, run_cmd):
        """IRRDB info: ASNs, cache expired"""
        for i in [1, 2]:
            self.setup_obj(["AS-ONE"], cache_expiry=1)
            self.obj.load_data()

            self.assertEqual(sorted(self.obj.asns), [1, 2, 3])
            self.file_exists("AS_ONE-as_set.json")

            if i == 1:
                run_cmd.assert_called_once()
                time.sleep(1)
            else:
                self.assertEqual(run_cmd.call_count, 2)

class TestIRRDBInfo_RSet(TestIRRDBInfo_Base):

    __test__ = True

    def setup_obj(self, object_names, allow_longer_prefixes=False,
                  cache_expiry=10):
        self.obj = RSet(
            object_names,
            4,
            allow_longer_prefixes,
            cache_dir=self.temp_dir,
            cache_expiry=cache_expiry,
            bgpq3_path="false"
        )

    @mock.patch.object(RSet, "_run_cmd", return_value=load("rset_test_10.json"))
    def test_010_simple(self, run_cmd):
        """IRRDB info: RSets, simple"""

        exp_res = json.loads(load("rset_test_10.expected.json").decode("utf-8"))
        self.setup_obj(["AS-ONE"])
        self.obj.load_data()

        self.assertEqual(self.obj.prefixes, exp_res)
        self.file_exists("AS_ONE-r_set-ipv4.json")
        run_cmd.assert_called_once()

    @mock.patch.object(RSet, "_run_cmd", return_value=load("rset_test_10.json"))
    def test_011_from_cache(self, run_cmd):
        """IRRDB info: RSets, from cache"""
        exp_res = json.loads(load("rset_test_10.expected.json").decode("utf-8"))

        for i in [1, 2]:
            self.setup_obj(["AS-ONE"])
            self.obj.load_data()

            self.assertEqual(self.obj.prefixes, exp_res)
            self.file_exists("AS_ONE-r_set-ipv4.json")
            run_cmd.assert_called_once()

    @mock.patch.object(RSet, "_run_cmd", return_value=load("rset_test_10.json"))
    def test_012_cache_expired(self, run_cmd):
        """IRRDB info: RSets, cache expired"""
        exp_res = json.loads(load("rset_test_10.expected.json").decode("utf-8"))

        for i in [1, 2]:
            self.setup_obj(["AS-ONE"], cache_expiry=1)
            self.obj.load_data()

            self.assertEqual(self.obj.prefixes, exp_res)
            self.file_exists("AS_ONE-r_set-ipv4.json")

            if i == 1:
                run_cmd.assert_called_once()
                time.sleep(1)
            else:
                self.assertEqual(run_cmd.call_count, 2)

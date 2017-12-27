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

import yaml
import shutil
import tempfile
import unittest

from pierky.arouteserver.arin_db_dump import ARINWhoisDBDump
from pierky.arouteserver.config.general import ConfigParserGeneral
from pierky.arouteserver.ixf_db import IXFDB
from pierky.arouteserver.last_version import LastVersion
from pierky.arouteserver.peering_db import PeeringDBNet
from pierky.arouteserver.ripe_rpki_cache import RIPE_RPKI_ROAs

cache_dir = None
cache_cfg = {
    "cache_dir": None
}

def setUpModule():
    global cache_dir
    cache_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")
    cache_cfg["cache_dir"] = cache_dir

def tearDownModule():
    shutil.rmtree(cache_dir, ignore_errors=True)

class TestExternalResources(unittest.TestCase):

    def test_peeringdb(self):
        """External resources: PeeringDB, max-prefix and AS-SET"""
        net = PeeringDBNet(3333, **cache_cfg)
        net.load_data()
        self.assertTrue(net.info_prefixes4 > 0)
        self.assertTrue(net.info_prefixes6 > 0)
        self.assertEqual(net.irr_as_sets, ["AS-RIPENCC"])

    def test_arin_db_dump(self):
        """External resources: ARIN Whois database dump"""
        cfg = ConfigParserGeneral()
        url = cfg.get_schema()["cfg"]["filtering"]["irrdb"]["use_arin_bulk_whois_data"]["source"].default
        db_dump = ARINWhoisDBDump(arin_whois_db_source=url, **cache_cfg)
        db_dump.load_data()
        self.assertTrue(len(db_dump.whois_records) > 0)

    def test_ixf_db(self):
        """External resources: IXF DB"""
        db = IXFDB()
        self.assertTrue(len(db.ixp_list) > 0)

    def test_last_version(self):
        """External resources: last version via PyPI"""
        last_ver = LastVersion(**cache_cfg)
        last_ver.load_data()
        ver = last_ver.last_version
        self.assertTrue(int(ver.split(".")[0]) >= 0)
        self.assertTrue(int(ver.split(".")[1]) >= 17)

    def test_ripe_rpki_cache(self):
        """External resources: RIPE RPKI cache"""
        cfg = ConfigParserGeneral()
        url = cfg.get_schema()["cfg"]["rpki_roas"]["ripe_rpki_validator_url"].default
        ripe_rpki_cache = RIPE_RPKI_ROAs(ripe_rpki_validator_url=url, **cache_cfg)
        ripe_rpki_cache.load_data()
        self.assertTrue(len(ripe_rpki_cache.roas) > 0)

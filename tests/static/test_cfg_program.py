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

import os
import shutil
import six
import tempfile
import unittest

from pierky.arouteserver.config.program import ConfigParserProgram
from pierky.arouteserver.errors import ProgramConfigError

class TestProgramConfig(unittest.TestCase):

    CFG_FILE_PATH = "config.d/{}".format(ConfigParserProgram.DEFAULT_CFG_FILE)

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")
        self.pr_cfg = ConfigParserProgram(verbose=False, ask=False)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _mk_dir(self, d):
        os.makedirs(os.path.join(self.temp_dir, d))

    def _rm_dir(self, d):
        shutil.rmtree(os.path.join(self.temp_dir, d), ignore_errors=True)

    def _load_from_temp_dir(self, cfg):
        buf = cfg.format(temp_dir=self.temp_dir)
        f = six.StringIO(buf)
        self.pr_cfg.load(f)

    def test_010_load_distributed_file(self):
        """Program config: load distributed configuration file"""
        self.pr_cfg.load(self.CFG_FILE_PATH)

        expected_values = [
            ("cfg_dir", "config.d"),
            ("logging_config_file", "config.d/log.ini"),
            ("cfg_general", "config.d/general.yml"),
            ("cfg_clients", "config.d/clients.yml"),
            ("cfg_bogons", "config.d/bogons.yml"),
            ("templates_dir", "config.d/templates"),
            ("template_name", "main.j2"),
            ("cache_dir", "config.d/cache"),
            ("bgpq3_path", "bgpq3"),
            ("bgpq3_host", "rr.ntt.net"),
            ("bgpq3_sources", ("RIPE,APNIC,AFRINIC,ARIN,NTTCOM,ALTDB,BBOI,"
                               "BELL,JPIRR,LEVEL3,RADB,RGNET,SAVVIS,TC")),
            ("rtt_getter_path", ""),
            ("threads", 4),
            ("cache_expiry",
                {
                    "general": 43200,
                    "pdb_info": 86400,
                    "ripe_rpki_roas": 43200,
                    "irr_as_sets": 43200,
                    "arin_whois_db_dump": 43200,
                    "registrobr_whois_db_dump": 43200
                }
            )
        ]
        for exp_key, exp_val in expected_values:
            self.assertEqual(self.pr_cfg.cfg[exp_key], exp_val)

    def test_020_load_from_temp_dir(self):
        """Program config: load from temporary directory"""
        self._load_from_temp_dir("cfg_dir: {temp_dir}")

        expected_values = [
            ("cfg_dir", self.temp_dir),
            ("logging_config_file", self.temp_dir + "/log.ini"),
            ("cfg_general", self.temp_dir + "/general.yml"),
            ("cfg_clients", self.temp_dir + "/clients.yml"),
            ("cfg_bogons", self.temp_dir + "/bogons.yml"),
            ("templates_dir", self.temp_dir + "/templates"),
            ("cache_dir", self.temp_dir + "/cache")
        ]
        for exp_key, exp_val in expected_values:
            self.assertEqual(self.pr_cfg.cfg[exp_key], exp_val)

        self.pr_cfg.get_dir("cfg_dir")

        for d in ("templates_dir", "cache_dir"):
            with six.assertRaisesRegex(self, ProgramConfigError,
                                       "does not exist"):
                self.pr_cfg.get_dir(d)

        self._mk_dir("templates")
        self._mk_dir("cache")

        for d in ("templates_dir", "cache_dir"):
            try:
                self.pr_cfg.get_dir(d)
            except:
                self.fail("get_dir() failed for {}".format(d))

    def test_030_setup(self):
        """Program config: setup"""
        self.pr_cfg.setup(destination_directory=self.temp_dir)
        errors = self.pr_cfg.verify_templates()
        self.assertEqual(len(errors), 0)

    def test_031_setup_and_setup_again(self):
        """Program config: setup, then setup again"""
        self.pr_cfg.setup(destination_directory=self.temp_dir)
        self.pr_cfg.setup(destination_directory=self.temp_dir)

    def test_040_setup_edit_one_template(self):
        """Program config: setup, then change a template file"""
        self.test_030_setup()

        with open(os.path.join(self.temp_dir, "templates", "bird", "main.j2"), "w") as f:
            f.write("A")

        errors = self.pr_cfg.verify_templates()

        self.assertEqual(len(errors), 1)
        self.assertTrue("templates/bird/main.j2 file has been edited" in errors[0])

    def test_040_setup_edit_one_template_then_fix(self):
        """Program config: setup, change a template file then fix it"""
        self.test_040_setup_edit_one_template()

        self.pr_cfg.setup_templates()
        errors = self.pr_cfg.verify_templates()
        self.assertEqual(len(errors), 0)

    def test_050_setup_then_rm_templates(self):
        """Program config: setup, then remove templates"""
        self.test_030_setup()

        self._rm_dir("templates")
        self._mk_dir("templates")

        errors = self.pr_cfg.verify_templates()
        self.assertEqual(len(errors), 17)
        for err in errors:
            self.assertTrue("expected but not found on the local templates directory" in err)

    def test_060_setup_rm_templates_then_fix(self):
        """Program config: setup, remove templates then fix it"""
        self.test_050_setup_then_rm_templates()

        self.pr_cfg.setup_templates()
        errors = self.pr_cfg.verify_templates()
        self.assertEqual(len(errors), 0)

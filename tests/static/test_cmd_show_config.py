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
from six import StringIO
import shutil
import tempfile
import unittest

from pierky.arouteserver.commands import ShowConfigCommand

class TestShowConfig(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def get_exp_path(self, fname):
        base_dir=os.path.dirname(__file__)
        return os.path.join(base_dir, "data", "test_cmd_show_config", fname)

    def get_exp(self, fname):
        path = self.get_exp_path(fname)
        with open(path, "r") as f:
            return f.read()

    def _test(self, src, exp_fname):
        self.maxDiff = None

        buf = StringIO()
        ShowConfigCommand.show_config(src, buf)
        buf.seek(0)

        try:
            self.assertMultiLineEqual(buf.read(), self.get_exp(exp_fname))
        except:
            print("TO FIX IT:\n\n")
            print("  cat << EOF > {}".format(self.get_exp_path(exp_fname)))
            buf.seek(0)
            print(buf.read().rstrip())
            print("EOF")
            raise

    def test_distrib(self):
        """Show config command: distributed config"""
        self._test("config.d/general.yml", "distrib.txt")

    def test_empty(self):
        """Show config command: empty config"""
        path = os.path.join(self.temp_dir, "empty.yml")
        with open(path, "w") as f:
            f.write("cfg:\n")
            f.write("  rs_as: 65534\n")
            f.write("  router_id: 192.0.2.1\n")
        self._test(path, "empty.txt")

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
from logging.config import fileConfig
import os
import subprocess
import unittest

from pierky.arouteserver.tests.base import ARouteServerTestCase
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPD60Instance, \
                                                          OpenBGPD61Instance
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4, \
                                                      BIRDInstanceIPv6

class TestRealConfigs(ARouteServerTestCase):
    __test__ = False

    IXP = None
    CLIENTS_FILE = None

    # Set to True for those tests that don't run locally on my machine,
    # because of lack of resources!!! If True, the REMOTE_IP env var is
    # used to get the IP address of a remote host where OpenBGPD is
    # running; if the REMOTE_IP env var is not found, then the file at
    # ~/ars_remote_ip is used to load a dictionary containing similar
    # data:
    # {"openbgpd_6.0": "A.B.C.D", "openbgpd_6.1": "w.x.y.z"}
    # If REMOTE_IP_NEEDED is True and no remote IP can be found, the
    # test is skipped.
    REMOTE_IP_NEEDED = True

    @classmethod
    def _setUpClass(cls):
        cwd = os.path.dirname(__file__)

        if os.path.exists(os.path.join(cwd, "arouteserver.log")):
            os.remove(os.path.join(cwd, "arouteserver.log"))

        fileConfig(os.path.join(cwd, "log.ini"))

        cls.var_dir = os.path.join(cwd, "var")
        if not os.path.exists(cls.var_dir):
            os.makedirs(cls.var_dir)

        cls.cache_dir = os.path.join(cls.var_dir, "cache")
        if not os.path.exists(cls.cache_dir):
            os.makedirs(cls.cache_dir)

        cls.rs_config_dir = os.path.join(cls.var_dir, "configs")
        if not os.path.exists(cls.rs_config_dir):
            os.makedirs(cls.rs_config_dir)

    def get_rs_config_file_path(self, bgp_speaker, target_ver, ip_ver):
        filename = "{ixp}_{bgp_speaker}{bgp_speaker_version}{ip_ver}.conf".format(
            ixp=self.IXP,
            bgp_speaker=bgp_speaker,
            bgp_speaker_version="_{}".format(target_ver) if target_ver else "",
            ip_ver="_ipv{}".format(ip_ver) if ip_ver else ""
        )
        return os.path.join(self.rs_config_dir, filename)

    def build_config(self, bgp_speaker, target_ver, ip_ver):
        cwd = os.path.dirname(__file__)

        if bgp_speaker not in ("bird", "openbgpd"):
            raise ValueError("Unknown bgp_speaker: {}".format(bgp_speaker))

        rs_config_file_path = self.get_rs_config_file_path(
            bgp_speaker, target_ver, ip_ver)

        cmd = ["./scripts/arouteserver"]
        cmd += [bgp_speaker]
        cmd += ["--cfg", os.path.join(cwd, "arouteserver.yml")]
        cmd += ["--output", rs_config_file_path]
        cmd += ["--ignore-issues", "path_hiding"]
        if target_ver:
            cmd += ["--target-version", target_ver]
        cmd += ["--clients", os.path.join(cwd, "clients", self.CLIENTS_FILE)]
        if ip_ver:
            cmd += ["--ip-ver", str(ip_ver)]

        subprocess.check_output(cmd)

    def load_config(self, bgp_speaker, target_ver, ip_ver):
        remote_ip = os.environ.get("REMOTE_IP", "").strip()

        if not remote_ip:
            remote_ip_key = "{}_{}".format(bgp_speaker, target_ver)
            remote_ip_file = os.path.expanduser("~/ars_remote_ip")
            if os.path.exists(remote_ip_file):
                with open(remote_ip_file, "r") as f:
                    remote_ip_file_data = json.load(f)
                remote_ip = remote_ip_file_data.get(remote_ip_key, None)

        if bgp_speaker == "bird":
            if ip_ver == 4:
                inst_class = BIRDInstanceIPv4
            elif ip_ver == 6:
                inst_class = BIRDInstanceIPv6
            else:
                raise ValueError("Unknown ip_ver: {}".format(ip_ver))
        elif bgp_speaker == "openbgpd":
            if not remote_ip and self.REMOTE_IP_NEEDED:
                self.skipTest("Remote IP not found")

            if target_ver == "6.0":
                inst_class = OpenBGPD60Instance
            elif target_ver == "6.1":
                inst_class = OpenBGPD61Instance
            else:
                raise ValueError("Unknown target_ver: {}".format(target_ver))

        rs_config_file_path = self.get_rs_config_file_path(
            bgp_speaker, target_ver, ip_ver)

        if not os.path.exists(rs_config_file_path):
            raise ValueError("RS config file does not exist: {}".format(
                rs_config_file_path))

        inst = inst_class(
            "rs", "2001:db8:1:1::2" if ip_ver == 6 else "192.0.2.2",
            [(rs_config_file_path,
              "/etc/bird/bird.conf" if bgp_speaker == "bird"
                                    else "/etc/bgpd.conf")],
            remote_ip=remote_ip
        )
        inst.set_var_dir(self.rs_config_dir)
        inst.start()
        inst.stop()

    def shortDescription(self):
        return "Real configs: {}, {}".format(self.IXP, self._testMethodDoc)

class TestRealConfigs_IXP(TestRealConfigs):
    __test__ = False

    def test_bird4_010_build(self):
        """BIRD, IPv4, build"""
        self.build_config("bird", None, 4)

    def test_bird4_020_load(self):
        """BIRD, IPv4, load"""
        if "BUILD_ONLY" in os.environ:
            self.skipTest("Build only")
        self.load_config("bird", None, 4)

    def test_bird6_010_build(self):
        """BIRD, IPv6, build"""
        self.build_config("bird", None, 6)

    def test_bird6_020_load(self):
        """BIRD, IPv6, load"""
        if "BUILD_ONLY" in os.environ:
            self.skipTest("Build only")
        self.load_config("bird", None, 6)

    def test_openbgpd60_010_build(self):
        """OpenBGPD 6.0, build"""
        self.build_config("openbgpd", "6.0", None)

    @unittest.skipIf("TRAVIS" in os.environ, "not supported on Travis CI")
    def test_openbgpd60_020_load(self):
        """OpenBGPD 6.0, load"""
        if "BUILD_ONLY" in os.environ:
            self.skipTest("Build only")
        self.load_config("openbgpd", "6.0", None)

    def test_openbgpd61_010_build(self):
        """OpenBGPD 6.1, build"""
        self.build_config("openbgpd", "6.1", None)

    @unittest.skipIf("TRAVIS" in os.environ, "not supported on Travis CI")
    def test_openbgpd61_020_load(self):
        """OpenBGPD 6.1, load"""
        if "BUILD_ONLY" in os.environ:
            self.skipTest("Build only")
        self.load_config("openbgpd", "6.1", None)

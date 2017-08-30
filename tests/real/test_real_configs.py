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

import logging
import os
import time
import unittest

from pierky.arouteserver.builder import BIRDConfigBuilder, \
                                        OpenBGPDConfigBuilder
from pierky.arouteserver.tests.base import ARouteServerTestCase
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPD60Instance, \
                                                          OpenBGPD61Instance
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4, \
                                                      BIRDInstanceIPv6

class TestRealConfigs(ARouteServerTestCase):
    __test__ = False

    IXP = None
    CLIENTS_FILE = None

    def setUp(self):
        self.skipTest("Work in progress on 'dev' branch")

    @classmethod
    def _setUpClass(cls):
        cwd = os.path.dirname(__file__)

        cls.var_dir = os.path.join(cwd, "var")
        if not os.path.exists(cls.var_dir):
            os.makedirs(cls.var_dir)

        cls.cache_dir = os.path.join(cls.var_dir, "cache")
        if not os.path.exists(cls.cache_dir):
            os.makedirs(cls.cache_dir)

        cls.now = int(time.time())

    def get_rs_config_file_path(self, bgp_speaker, target_ver, ip_ver):
        filename = "{ixp}_{bgp_speaker}{bgp_speaker_version}{ip_ver}_{ts}.conf".format(
            ixp=self.IXP,
            bgp_speaker=bgp_speaker,
            bgp_speaker_version="_{}".format(target_ver) if target_ver else "",
            ip_ver="_ipv{}".format(ip_ver) if ip_ver else "",
            ts=self.now
        )
        return os.path.join(self.var_dir, filename)

    def build_config(self, bgp_speaker, target_ver, ip_ver):
        cwd = os.path.dirname(__file__)

        if bgp_speaker == "bird":
            builder_class = BIRDConfigBuilder
        elif bgp_speaker == "openbgpd":
            builder_class = OpenBGPDConfigBuilder
        else:
            raise ValueError("Unknown bgp_speaker: {}".format(bgp_speaker))

        builder = builder_class(
            template_dir=os.path.join(cwd, "templates", bgp_speaker),
            template_name="main.j2",
            cache_dir=self.cache_dir,
            ip_ver=ip_ver,
            ignore_errors=["path_hiding"],
            target_version=target_ver,
            cfg_general=os.path.join(cwd, "general.yml"),
            cfg_bogons=os.path.join(cwd, "bogons.yml"),
            cfg_clients=os.path.join(cwd, "clients", self.CLIENTS_FILE)
        )

        rs_config_file_path = self.get_rs_config_file_path(
            bgp_speaker, target_ver, ip_ver)

        with open(rs_config_file_path, "w") as f:
            builder.render_template(f)

    def load_config(self, bgp_speaker, target_ver, ip_ver):
        if bgp_speaker == "bird":
            if ip_ver == 4:
                inst_class = BIRDInstanceIPv4
            elif ip_ver == 6:
                inst_class = BIRDInstanceIPv6
            else:
                raise ValueError("Unknown ip_ver: {}".format(ip_ver))
        elif bgp_speaker == "openbgpd":
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
                                    else "/etc/bgpd.conf")]
        )
        inst.set_var_dir(self.var_dir)
        inst.start()
        inst.stop()

    def shortDescription(self):
        return "Real configs: {}, {}".format(self.IXP, self._testMethodDoc)

class TestRealConfigs_IXP(TestRealConfigs):
    __test__ = False

    def test_bird4_a(self):
        """BIRD, IPv4, build"""
        self.build_config("bird", None, 4)

    def test_bird4_b(self):
        """BIRD, IPv4, load"""
        if "BUILD_ONLY" in os.environ:
            self.skipTest("Build only")
        self.load_config("bird", None, 4)

    def test_bird6_a(self):
        """BIRD, IPv6, build"""
        self.build_config("bird", None, 6)

    def test_bird6_b(self):
        """BIRD, IPv6, load"""
        if "BUILD_ONLY" in os.environ:
            self.skipTest("Build only")
        self.load_config("bird", None, 6)

    def test_openbgpd60_a(self):
        """OpenBGPD 6.0, build"""
        self.build_config("openbgpd", "6.0", None)

    @unittest.skipIf("TRAVIS" in os.environ, "not supported on Travis CI")
    def test_openbgpd60_b(self):
        """OpenBGPD 6.0, load"""
        if "BUILD_ONLY" in os.environ:
            self.skipTest("Build only")
        self.load_config("openbgpd", "6.0", None)

    def test_openbgpd61_a(self):
        """OpenBGPD 6.1, build"""
        self.build_config("openbgpd", "6.1", None)

    @unittest.skipIf("TRAVIS" in os.environ, "not supported on Travis CI")
    def test_openbgpd61_b(self):
        """OpenBGPD 6.1, load"""
        if "BUILD_ONLY" in os.environ:
            self.skipTest("Build only")
        self.load_config("openbgpd", "6.1", None)


class TestRealConfigs_ASM_IX(TestRealConfigs_IXP):
    __test__ = True

    IXP = "ASM-IX"
    CLIENTS_FILE = "ams-ix.yml"

class TestRealConfigs_BCIX_IX(TestRealConfigs_IXP):
    __test__ = True

    IXP = "BCIX"
    CLIENTS_FILE = "bcix.yml"

class TestRealConfigs_BIX(TestRealConfigs_IXP):
    __test__ = True

    IXP = "BIX"
    CLIENTS_FILE = "bix.yml"

class TestRealConfigs_GR_IX(TestRealConfigs_IXP):
    __test__ = True

    IXP = "GR-IX"
    CLIENTS_FILE = "gr-ix.yml"

class TestRealConfigs_INEX(TestRealConfigs_IXP):
    __test__ = True

    IXP = "INEX"
    CLIENTS_FILE = "inex.yml"

class TestRealConfigs_LONAP(TestRealConfigs_IXP):
    __test__ = True

    IXP = "LONAP"
    CLIENTS_FILE = "lonap.yml"

class TestRealConfigs_SIX(TestRealConfigs_IXP):
    __test__ = True

    IXP = "SIX"
    CLIENTS_FILE = "six.yml"

class TestRealConfigs_STHIX(TestRealConfigs_IXP):
    __test__ = True

    IXP = "STHIX"
    CLIENTS_FILE = "sthix.yml"

class TestRealConfigs_SwissIX(TestRealConfigs_IXP):
    __test__ = True

    IXP = "SwissIX"
    CLIENTS_FILE = "swissix.yml"


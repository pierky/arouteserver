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
import unittest

import yaml

from .cfg_base import TestConfigParserBase
from pierky.arouteserver.builder import BIRDConfigBuilder, OpenBGPDConfigBuilder
from pierky.arouteserver.config.general import ConfigParserGeneral
from pierky.arouteserver.config.clients import ConfigParserClients
from pierky.arouteserver.errors import BuilderError
from pierky.arouteserver.tests.base import ARouteServerTestCase

class TestRPKIAnnounceInvalid(ARouteServerTestCase):
    __test__ = False

    BUILDER_CLASS = None
    TEMPLATE_DIR = None
    IP_VER = None

    CFG_TPL = [
        "cfg:",
        "  rs_as: 999",
        "  router_id: 192.0.2.2",
        "  filtering:",
        "    irrdb:",
        "      enforce_origin_in_as_set: False",
        "      enforce_prefix_in_as_set: False",
        "      tag_as_set: False",
        "    rpki:",
        "      enabled: True"
    ]

    CLIENTS_TPL = [
        "clients:",
        "  - asn: 1",
        "    ip: 192.0.2.10",
        "  - asn: 2",
        "    ip: 192.0.2.20"
    ]

    def _create_builder(self, cfg_lines, clients_lines):
        cfg = ConfigParserGeneral()
        cfg._load_from_yaml("\n".join(cfg_lines))
        cfg.parse()

        clients = ConfigParserClients(general_cfg=cfg)
        clients._load_from_yaml("\n".join(clients_lines))
        clients.parse()
        builder = self.BUILDER_CLASS(
            template_dir="templates/{}".format(self.TEMPLATE_DIR),
            template_name="main.j2",
            cache_dir="var",
            ip_ver=self.IP_VER,
            cfg_general=cfg,
            cfg_clients=clients,
            cfg_bogons="config.d/bogons.yml",
            ignore_errors=["*"]
        )

    def test_common_not_enabled(self):
        """{}: no announce_invalid"""

        cfg_tpl = self.CFG_TPL
        clients_tpl = self.CLIENTS_TPL
        self._create_builder(cfg_tpl, clients_tpl)

    def test_common_enabled_all_no_comm(self):
        """{}: enabled for all, no 'roa_invalid'"""

        cfg_tpl = self.CFG_TPL + [
            "      announce_invalid: True"
        ]
        clients_tpl = self.CLIENTS_TPL

        with self.assertRaisesRegexp(
            BuilderError,
            "The BGP community 'roa_invalid' has not been configured but "
            "'rpki.announce_invalid' has been set for the following clients: "
            "192.0.2.10, 192.0.2.20."
        ):
            self._create_builder(cfg_tpl, clients_tpl)

    def test_common_enabled_one_no_comm(self):
        """{}: enabled for one, no 'roa_invalid'"""

        cfg_tpl = self.CFG_TPL
        clients_tpl = self.CLIENTS_TPL + [
            "    cfg:",
            "      filtering:",
            "        rpki:",
            "          announce_invalid: True"
        ]

        with self.assertRaisesRegexp(
            BuilderError,
            "The BGP community 'roa_invalid' has not been configured but "
            "'rpki.announce_invalid' has been set for the following clients: "
            "192.0.2.20."
        ):
            self._create_builder(cfg_tpl, clients_tpl)

    def test_common_enabled_all_with_comm(self):
        """{}: enabled for all, with 'roa_invalid'"""

        cfg_tpl = self.CFG_TPL + [
            "      announce_invalid: True",
            "  communities:",
            "    roa_invalid:",
            "      std: '65534:1'"
        ]
        clients_tpl = self.CLIENTS_TPL

        self._create_builder(cfg_tpl, clients_tpl)

class TestRPKIAnnounceInvalidBIRD(TestRPKIAnnounceInvalid):
    __test__ = False

    SHORT_DESCR = "RPKI, announce invalid, BIRD"
    BUILDER_CLASS = BIRDConfigBuilder
    TEMPLATE_DIR = "bird"
    IP_VER = 4

class TestRPKIAnnounceInvalidOpenBGPD(TestRPKIAnnounceInvalid):
    __test__ = False

    SHORT_DESCR = "RPKI, announce invalid, OpenBGPD"
    BUILDER_CLASS = OpenBGPDConfigBuilder
    TEMPLATE_DIR = "openbgpd"
    IP_VER = 4

    def test_openbgpd_enabled_all_with_large_comm(self):
        """{}: enabled for all, with 'roa_invalid' large comm only"""

        cfg_tpl = self.CFG_TPL + [
            "      announce_invalid: True",
            "  communities:",
            "    roa_invalid:",
            "      lrg: '999:65534:1'"
        ]
        clients_tpl = self.CLIENTS_TPL

        with self.assertRaisesRegexp(
            BuilderError,
            "The BGP community 'roa_invalid' has not been configured but "
            "'rpki.announce_invalid' has been set for the following clients: "
            "192.0.2.10, 192.0.2.20."
        ):
            self._create_builder(cfg_tpl, clients_tpl)

    def test_openbgpd_enabled_all_with_large_comm_and_ext_comm(self):
        """{}: enabled for all, with 'roa_invalid' large comm + ext comm"""

        cfg_tpl = self.CFG_TPL + [
            "      announce_invalid: True",
            "  communities:",
            "    roa_invalid:",
            "      lrg: '999:65534:1'",
            "      ext: 'rt:65534:1'"
        ]
        clients_tpl = self.CLIENTS_TPL

        self._create_builder(cfg_tpl, clients_tpl)


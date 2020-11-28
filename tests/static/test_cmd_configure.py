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

import copy
import os
import shutil
import tempfile
from packaging import version
try:
    import mock
except ImportError:
    import unittest.mock as mock
import yaml

from pierky.arouteserver.ask import Ask
from pierky.arouteserver.builder import BIRDConfigBuilder, \
                                        OpenBGPDConfigBuilder
from pierky.arouteserver.commands import ConfigureCommand
from pierky.arouteserver.tests.mocked_env import MockedEnv
from pierky.arouteserver.tests.base import ARouteServerTestCase

class FakeConfigureCommand(ConfigureCommand):

    NEEDS_CONFIG = False

class TestConfigureCmd(ARouteServerTestCase):

    NEED_TO_CAPTURE_LOG = True

    EXPECTED_CONFIG = {
        "cfg": {
            "rs_as": 999,
            "router_id": "192.0.2.1",
            "filtering": {
                "next_hop": {
                    "policy": "strict"
                },
                "ipv4_pref_len": {
                    "min": 8,
                    "max": 24
                },
                "ipv6_pref_len": {
                    "min": 12,
                    "max": 48
                },
                "global_black_list_pref": [
                    {"prefix": "192.0.2.0", "length": 24},
                    {"prefix": "2001:db8::", "length": 32}
                ],
                "max_as_path_len": 32,
                "reject_invalid_as_in_as_path": True,
                "transit_free": {
                    "action": "reject",
                    "asns": [
                        174, 209, 286, 701, 1239, 1299, 2828, 2914,
                        3257, 3320, 3356, 3549, 5511, 6453, 6461,
                        6762, 6830, 7018, 12956
                    ]
                },
                "never_via_route_servers": {
                    "peering_db": True
                },
                "irrdb": {
                    "enforce_origin_in_as_set": True,
                    "enforce_prefix_in_as_set": True,
                    "allow_longer_prefixes": True,
                    "tag_as_set": True,
                    "peering_db": True,
                    "use_rpki_roas_as_route_objects": {
                        "enabled": True
                    },
                    "use_arin_bulk_whois_data": {
                        "enabled": True
                    },
                    "use_registrobr_bulk_whois_data": {
                        "enabled": True
                    }
                },
                "rpki_bgp_origin_validation": {
                    "enabled": True,
                    "reject_invalid": True
                },
                "max_prefix": {
                    "action": "shutdown",
                    "peering_db": {
                        "enabled": True
                    }
                },
            },
            "graceful_shutdown": {
                "enabled": True
            },
            "rfc1997_wellknown_communities": {
                "policy": "pass"
            }
        }
    }

    def setup_builder(self, cls, general, **kwargs):
        tpl_dir = "bird" if cls is BIRDConfigBuilder else "openbgpd"

        MockedEnv(base_dir=os.path.dirname(__file__),
                  default=True)

        self.builder = cls(
            template_dir="templates/{}/".format(tpl_dir),
            template_name="main.j2",
            cfg_general=self.write_file("general.yml", general),
            cfg_clients=self.write_clients(),
            cfg_bogons="config.d/bogons.yml",
            cache_dir=self.temp_dir,
            cache_expiry=120,
            **kwargs
        )

    def _setUp(self, *patches):
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")
        self.expected_config = copy.deepcopy(self.EXPECTED_CONFIG)

    def tearDown(self):
        mock.patch.stopall()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write_file(self, name, buff):
        path = os.path.join(self.temp_dir, name)
        with open(path, "w") as f:
            f.write(buff)
        return path

    def write_clients(self):
        buff = "\n".join([
            "clients:",
            "  - asn: 2",
            "    ip:",
            "      - '192.0.2.10'",
            "      - '2001:db8::10'"
        ])
        return self.write_file("clients.yml", buff)

    def mock_answers(self, answers):

        self.answers = answers
        self.next_answer_idx = 0

        def get_input(ask_self):
            answer = self.answers[self.next_answer_idx]
            self.next_answer_idx += 1
            return answer

        mock_ask_get_input = mock.patch.object(
            Ask, "get_input", autospec=True
        ).start()
        mock_ask_get_input.side_effect = get_input

        mock_ask_wr_out = mock.patch.object(
            Ask, "wr_out", autospec=True
        ).start()
        mock_ask_wr_out.side_effect = None

        mock_wr_text = mock.patch.object(
            ConfigureCommand, "wr_text", autospec=True
        ).start()
        mock_wr_text.side_effect = None

    def configure_and_build(self, builder_cls, expected_config=None, **kwargs):

        def iter_compare(dic1, dic2, path=""):
            self.assertEqual(
                sorted(dic1.keys()),
                sorted(dic2.keys())
            )
            for k in dic1:
                if k not in dic2:
                    self.fail("{} not in dic2 (path: {})".format(k, path))
                if isinstance(dic2[k], dict):
                    iter_compare(dic1[k], dic2[k], path=path + ".{}".format(k))
                else:
                    self.assertEqual(
                        dic1[k], dic2[k],
                        msg="path: {}".format(path)
                    )

        cmd = FakeConfigureCommand(None)
        general = cmd.configure_yml()
        dic = cmd.configure_dict()

        compare_dic = copy.deepcopy(dic)
        del compare_dic["cfg"]["communities"]
        iter_compare(compare_dic, expected_config or self.expected_config)

        self.setup_builder(builder_cls, general, **kwargs)
        self.builder.render_template()
        for msg in self.logger_handler.warnings:
            if msg.startswith("No AS-SETs provided"):
                continue
            self.fail("One or more warnings detected: " + msg)
        for msg in self.logger_handler.msgs:
            self.fail("One or more errors detected: " + msg)

        return dic

    def test_bird_simple(self):
        """Configure command: BIRD, simple"""
        self.mock_answers([
            "bird",
            BIRDConfigBuilder.DEFAULT_VERSION,
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            BIRDConfigBuilder,
            ip_ver=4,
            target_version=BIRDConfigBuilder.DEFAULT_VERSION
        )

        for comm_name in dic["cfg"]["communities"]:
            self.assertTrue("std" in dic["cfg"]["communities"][comm_name])
            self.assertTrue("ext" in dic["cfg"]["communities"][comm_name])
            self.assertTrue("lrg" in dic["cfg"]["communities"][comm_name])

    def test_openbgpd60_simple(self):
        """Configure command: OpenBGPD 6.0, simple"""
        self.expected_config["cfg"]["path_hiding"] = False
        self.expected_config["cfg"]["graceful_shutdown"]["enabled"] = False
        self.mock_answers([
            "openbgpd",
            "6.0",
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            OpenBGPDConfigBuilder,
            target_version="6.0"
        )

        for comm_name in dic["cfg"]["communities"]:
            self.assertTrue("std" in dic["cfg"]["communities"][comm_name])
            self.assertTrue("ext" not in dic["cfg"]["communities"][comm_name])
            self.assertTrue("lrg" not in dic["cfg"]["communities"][comm_name])

    def test_openbgpd61_simple(self):
        """Configure command: OpenBGPD 6.1, simple"""
        self.expected_config["cfg"]["path_hiding"] = False
        self.expected_config["cfg"]["graceful_shutdown"]["enabled"] = False
        self.mock_answers([
            "openbgpd",
            "6.1",
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            OpenBGPDConfigBuilder,
            target_version="6.1"
        )

        for comm_name in dic["cfg"]["communities"]:
            self.assertTrue("std" in dic["cfg"]["communities"][comm_name])
            self.assertTrue("ext" not in dic["cfg"]["communities"][comm_name])
            self.assertTrue("lrg" in dic["cfg"]["communities"][comm_name])

    def test_openbgpd62_simple(self):
        """Configure command: OpenBGPD 6.2, simple"""
        self.expected_config["cfg"]["path_hiding"] = False
        self.mock_answers([
            "openbgpd",
            "6.2",
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            OpenBGPDConfigBuilder,
            target_version="6.2"
        )

        for comm_name in dic["cfg"]["communities"]:
            self.assertTrue("std" in dic["cfg"]["communities"][comm_name])
            self.assertTrue("ext" not in dic["cfg"]["communities"][comm_name])
            self.assertTrue("lrg" in dic["cfg"]["communities"][comm_name])

    def test_openbgpd64_simple(self):
        """Configure command: OpenBGPD 6.4, simple"""
        self.expected_config["cfg"]["path_hiding"] = False
        self.mock_answers([
            "openbgpd",
            "6.4",
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            OpenBGPDConfigBuilder,
            target_version="6.4"
        )

        for comm_name in dic["cfg"]["communities"]:
            self.assertTrue("std" in dic["cfg"]["communities"][comm_name])
            self.assertTrue("ext" not in dic["cfg"]["communities"][comm_name])
            self.assertTrue("lrg" in dic["cfg"]["communities"][comm_name])

    def test_openbgpd65_simple(self):
        """Configure command: OpenBGPD 6.5, simple"""
        self.expected_config["cfg"]["path_hiding"] = False
        self.mock_answers([
            "openbgpd",
            "6.5",
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            OpenBGPDConfigBuilder,
            target_version="6.5"
        )

        for comm_name in dic["cfg"]["communities"]:
            self.assertTrue("std" in dic["cfg"]["communities"][comm_name])
            self.assertTrue("ext" not in dic["cfg"]["communities"][comm_name])
            self.assertTrue("lrg" in dic["cfg"]["communities"][comm_name])

    def test_openbgpd67_simple(self):
        """Configure command: OpenBGPD 6.7, simple"""
        self.expected_config["cfg"]["path_hiding"] = False
        self.mock_answers([
            "openbgpd",
            "6.7",
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            OpenBGPDConfigBuilder,
            target_version="6.7"
        )

        for comm_name in dic["cfg"]["communities"]:
            self.assertTrue("std" in dic["cfg"]["communities"][comm_name])
            self.assertTrue("ext" not in dic["cfg"]["communities"][comm_name])
            self.assertTrue("lrg" in dic["cfg"]["communities"][comm_name])

    def test_32bit_asn(self):
        """Configure command: 32 bit route server ASN"""
        self.expected_config["cfg"]["rs_as"] = 999999
        self.mock_answers([
            "bird",
            BIRDConfigBuilder.DEFAULT_VERSION,
            "999999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            BIRDConfigBuilder,
            ip_ver=4,
            target_version=BIRDConfigBuilder.DEFAULT_VERSION
        )
        self.assertEqual(
            dic["cfg"]["communities"]["do_not_announce_to_any"]["std"],
            "0:65534"
        )
        self.assertEqual(
            dic["cfg"]["communities"]["announce_to_peer"]["std"],
            "65534:peer_as"
        )

    def test_bird2_simple(self):
        """Configure command: BIRD 2.0, simple"""
        self.mock_answers([
            "bird",
            "2.0.7",
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])

        expected_config = copy.deepcopy(self.expected_config)
        expected_config["cfg"]["filtering"]["max_prefix"]["count_rejected_routes"] = False
        dic = self.configure_and_build(
            BIRDConfigBuilder,
            expected_config=expected_config,
            target_version="2.0.7"
        )

    def test_bird2_receive_limit_check(self):
        """Configure command: BIRD 2.0, receive limit > 2.0.7"""

        # This test just verifies if there is any known BIRD
        # release newer than 2.0.7, for which the 'receive limit'
        # issue might be fixed; if so, we need to relax the check
        # implemented in 'validate_bgpspeaker_specific_configuration'
        # inside BIRDConfigBuilder, and also change the class
        # ConfigureCommand so that count_rejected_routes will not
        # be set to False anymore for BIRD > 2.0.7.
        #
        # If/when that will happen, this test can be dropped.

        if any([version.parse(v) >= version.parse("2.0.8")
                for v in BIRDConfigBuilder.AVAILABLE_VERSION]):
            self.fail("A release of BIRD > 2.0.7 has been added "
                      "to the BIRDConfigBuilder class: maybe we "
                      "need to relax the way 'receive limit' is "
                      "handled? Check the test case for details.")

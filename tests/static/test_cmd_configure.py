# Copyright (C) 2017-2024 Pier Carlo Chiodi
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
try:
    import mock
except ImportError:
    import unittest.mock as mock

from pierky.arouteserver.ask import Ask
from pierky.arouteserver.builder import BIRDConfigBuilder, \
                                        OpenBGPDConfigBuilder
from pierky.arouteserver.commands import ConfigureCommand
from pierky.arouteserver.tests.mocked_env import MockedEnv
from pierky.arouteserver.tests.base import ARouteServerTestCase
from pierky.arouteserver.reject_reasons import REJECT_REASONS

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
                        174, 701, 1299, 2914, 3257, 3320, 3356, 5511,
                        6453, 6461, 6762, 6830, 7018, 12956
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
                "roles": {
                    "enabled": True
                }
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
                        msg="path: {} k: {} {} != {}".format(path, k, dic1[k], dic2[k])
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

    def verify_communities(self, communities, ext_expected=True, lrg_expected=True):
        for comm_name in communities:
            if comm_name == "reject_cause_map":
                continue

            self.assertTrue("std" in communities[comm_name])

            if ext_expected:
                self.assertTrue("ext" in communities[comm_name])
            else:
                self.assertTrue("ext" not in communities[comm_name])

            if lrg_expected:
                self.assertTrue("lrg" in communities[comm_name])
            else:
                self.assertTrue("lrg" not in communities[comm_name])

        if lrg_expected:
            self.assertIn("reject_cause_map", communities)

            for reject_code in communities["reject_cause_map"]:
                self.assertTrue(isinstance(reject_code, int))
                self.assertTrue(str(reject_code) in REJECT_REASONS)
                self.assertTrue("lrg" in communities["reject_cause_map"][reject_code])
                self.assertTrue(communities["reject_cause_map"][reject_code]["lrg"])
        else:
            self.assertNotIn("reject_cause_map", communities)

        self.assertEqual(
            communities["reject_cause"]["std"],
            "65520:dyn_val"
        )

        if lrg_expected:
            # Large BGP comms not expected, thus Euro-IX communities should not be added.
            self.assertEqual(
                communities["reject_cause"]["lrg"],
                "rs_as:65520:dyn_val"
            )
        else:
            self.assertNotIn("lrg", communities["reject_cause"])

    def test_bird_simple(self):
        """Configure command: BIRD, simple"""
        self.mock_answers([
            "bird",
            BIRDConfigBuilder.DEFAULT_VERSION,
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])

        self.expected_config["cfg"]["filtering"]["reject_policy"] = {
            "policy": "tag_and_reject"
        }

        dic = self.configure_and_build(
            BIRDConfigBuilder,
            ip_ver=4,
            target_version=BIRDConfigBuilder.DEFAULT_VERSION
        )

        self.verify_communities(dic["cfg"]["communities"])

    def test_bird_latest_simple(self):
        """Configure command: BIRD 2.0, latest, simple"""
        target_version = BIRDConfigBuilder.AVAILABLE_VERSION[-1]

        self.mock_answers([
            "bird",
            target_version,
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])

        self.expected_config["cfg"]["filtering"]["reject_policy"] = {
            "policy": "tag_and_reject"
        }

        dic = self.configure_and_build(
            BIRDConfigBuilder,
            ip_ver=4,
            target_version=target_version
        )

        self.verify_communities(dic["cfg"]["communities"])

    def test_openbgpd_latest_simple_75(self):
        """Configure command: OpenBGPD 7.5, simple"""
        self.expected_config["cfg"]["filtering"]["reject_policy"] = {
            "policy": "tag"
        }

        del self.expected_config["cfg"]["filtering"]["roles"]

        latest_version = OpenBGPDConfigBuilder.AVAILABLE_VERSION[-1]
        self.mock_answers([
            "openbgpd",
            "7.5",
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            OpenBGPDConfigBuilder,
            target_version=latest_version
        )

        self.verify_communities(
            dic["cfg"]["communities"],
            ext_expected=False
        )

    def test_openbgpd_latest_simple(self):
        """Configure command: OpenBGPD 7.0, simple"""
        self.expected_config["cfg"]["filtering"]["reject_policy"] = {
            "policy": "tag"
        }

        latest_version = OpenBGPDConfigBuilder.AVAILABLE_VERSION[-1]
        self.mock_answers([
            "openbgpd",
            latest_version,
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            OpenBGPDConfigBuilder,
            target_version=latest_version
        )

        self.verify_communities(
            dic["cfg"]["communities"],
            ext_expected=False
        )

    def test_openbgpd_latest_path_hiding(self):
        """Configure command: OpenBGPD, path-hiding"""

        self.expected_config["cfg"]["filtering"]["reject_policy"] = {
            "policy": "tag"
        }

        latest_version = OpenBGPDConfigBuilder.AVAILABLE_VERSION[-1]

        self.mock_answers([
            "openbgpd",
            latest_version,
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])
        dic = self.configure_and_build(
            OpenBGPDConfigBuilder,
            target_version=latest_version
        )
        self.verify_communities(
            dic["cfg"]["communities"],
            ext_expected=False
        )

    def test_32bit_asn(self):
        """Configure command: 32 bit route server ASN"""
        self.expected_config["cfg"]["filtering"]["reject_policy"] = {
            "policy": "tag_and_reject"
        }

        self.expected_config["cfg"]["rs_as"] = 999999
        self.mock_answers([
            "bird",
            BIRDConfigBuilder.DEFAULT_VERSION,
            "999999",
            "65533",
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
            "0:65533"
        )
        self.assertEqual(
            dic["cfg"]["communities"]["announce_to_peer"]["std"],
            "65533:peer_as"
        )

        self.assertEqual(
            dic["cfg"]["communities"]["reject_cause"]["std"],
            "65520:dyn_val"
        )
        self.assertEqual(
            dic["cfg"]["communities"]["reject_cause"]["lrg"],
            "rs_as:65520:dyn_val"
        )
        self.assertEqual(
            dic["cfg"]["communities"]["reject_cause_map"][1]["lrg"],
            "rs_as:1101:5"
        )

        self.verify_communities(dic["cfg"]["communities"])

    def test_bird2_simple(self):
        """Configure command: BIRD 2.0, simple"""
        target_version = BIRDConfigBuilder.AVAILABLE_VERSION[-1]

        self.mock_answers([
            "bird",
            target_version,
            "999",
            "192.0.2.1",
            "192.0.2.0/24,2001:db8::/32"
        ])

        self.expected_config["cfg"]["filtering"]["reject_policy"] = {
            "policy": "tag_and_reject"
        }
        dic = self.configure_and_build(
            BIRDConfigBuilder,
            target_version=BIRDConfigBuilder.AVAILABLE_VERSION[-1]
        )

        self.assertEqual(
            dic["cfg"]["communities"]["reject_cause"]["std"],
            "65520:dyn_val"
        )
        self.assertEqual(
            dic["cfg"]["communities"]["reject_cause"]["lrg"],
            "rs_as:65520:dyn_val"
        )

        self.verify_communities(dic["cfg"]["communities"])

# Copyright (C) 2017-2023 Pier Carlo Chiodi
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
import tempfile
import yaml
try:
    import mock
except ImportError:
    import unittest.mock as mock
import subprocess

from pierky.arouteserver.builder import TemplateContextDumper
from pierky.arouteserver.errors import BuilderError
from pierky.arouteserver.irrdb import ASSet, RSet, IRRDBInfo, TIMEDOUT_IRR_HOSTS
from pierky.arouteserver.tests.mocked_env import MockedEnv
from pierky.arouteserver.tests.base import ARouteServerTestCase


class TestIRRDBEnricher_HostsFailover(ARouteServerTestCase):

    NEED_TO_CAPTURE_LOG = True

    GENERAL_SIMPLE = {
        "cfg": {
            "rs_as": 999,
            "router_id": "192.0.2.2",
            "filtering": {
                "irrdb": {
                    "enforce_origin_in_as_set": True,
                    "enforce_prefix_in_as_set": True
                }
            }
        }
    }
    CLIENTS_SIMPLE = {
        "clients": [
            {
                "asn": 1,
                "ip": "192.0.2.11",
                "cfg": {
                    "filtering": {
                        "irrdb": {
                            "as_sets": ["AS-FAKE1"]
                        }
                    }
                }
            }
        ]
    }

    FIRST_HOST = IRRDBInfo.BGPQ3_DEFAULT_HOST[0]
    SECOND_HOST = IRRDBInfo.BGPQ3_DEFAULT_HOST[1]

    # Arguments to be set on child classes.
    HOSTS_TO_FAIL = None  # one | all
    TYPE_OF_ERROR = None  # timeout | failure

    def _setUp(self, *patches):
        # We need to clear the global list of hosts that timed out
        # before a test case is run, since it could contain hosts
        # added during the execution of previous test cases.
        TIMEDOUT_IRR_HOSTS.clear()

        # Don't use the MockedEnv 'irr=True' argument, because here
        # the IRRDBInfo's _run_cmd method needs to be mocked in a
        # different way, to introduce a fake timeout.
        MockedEnv(base_dir=os.path.dirname(__file__), default=False)
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")

        def _fail_query(cmd):
            if self.HOSTS_TO_FAIL == "one":
                # Fail only for the first host in the list.
                if self.FIRST_HOST not in cmd:
                    return
            elif self.HOSTS_TO_FAIL == "all":
                pass
            else:
                raise ValueError("HOSTS_TO_FAIL unknown " + self.HOSTS_TO_FAIL)

            if self.TYPE_OF_ERROR == "timeout":
                raise subprocess.TimeoutExpired(cmd, 1)
            elif self.TYPE_OF_ERROR == "failure":
                raise RuntimeError("fake failure")
            else:
                raise ValueError("TYPE_OF_ERROR unknown " + self.TYPE_OF_ERROR)

        def _mock_ASSet_run_cmd(self, cmd):
            _fail_query(cmd)

            return json.dumps({"asn_list": [10, 20, 30]}).encode()

        def _mock_RSet_run_cmd(self, cmd):
            _fail_query(cmd)

            if "AS-FAKE1" in cmd:
                return json.dumps({"prefix_list": [{"prefix": "192.168.0.0/16"}, {"prefix": "192.168.1.0/24"}]}).encode()
            else:
                return json.dumps({"prefix_list": []}).encode()

        mock_ASSet_run_cmd = mock.patch.object(
            ASSet, "_run_cmd", autospec=True
        ).start()
        mock_ASSet_run_cmd.side_effect = _mock_ASSet_run_cmd

        mock_RSet_run_cmd = mock.patch.object(
            RSet, "_run_cmd", autospec=True
        ).start()
        mock_RSet_run_cmd.side_effect = _mock_RSet_run_cmd

    def tearDown(self):
        MockedEnv.stopall()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def write_file(self, name, dic):
        path = os.path.join(self.temp_dir, name)
        with open(path, "w") as f:
            yaml.dump(dic, f, default_flow_style=False)
        return path

    def setup_builder(self, general, clients, ip_ver=4):
        self.builder = TemplateContextDumper(
            template_dir="templates/template-context/",
            template_name="main.j2",
            cfg_general=self.write_file("general.yml", general),
            cfg_clients=self.write_file("clients.yml", clients),
            cfg_bogons="config.d/bogons.yml",
            cache_dir=self.temp_dir,
            cache_expiry=120,
            ip_ver=ip_ver
        )

    def get_client_by_id(self, id):
        for client in self.builder.data["clients"]:
            if client["id"] == id:
                return client
        return None

    def get_client_info(self, client):
        asns = []
        prefixes = []
        for bundle_id in client["cfg"]["filtering"]["irrdb"]["as_set_bundle_ids"]:
            bundle = self.builder.data["irrdb_info"][bundle_id]
            asns.extend(bundle.asns)
            prefixes.extend(bundle.prefixes)
        return sorted(asns), ["{}/{}".format(_["prefix"], _["length"])
                              for _ in sorted(prefixes,
                                              key=lambda item: item["prefix"])]


class TestIRRDBEnricher_HostsFailover_SingleTimeout(TestIRRDBEnricher_HostsFailover):

    HOSTS_TO_FAIL = "one"
    TYPE_OF_ERROR = "timeout"

    def test_failure(self, *patches):
        """IRR queries fail-over: single timeout"""
        self.setup_builder(self.GENERAL_SIMPLE, self.CLIENTS_SIMPLE)
        self.builder.render_template()

        self.assertEqual(
            self.get_client_info(self.get_client_by_id("AS1_1")),
            ([1, 10, 20, 30], ["192.168.0.0/16", "192.168.1.0/24"])
        )

        self.assertTrue(
            any(
                "bgpq4 timed out while running the following command: 'bgpq4 -h " + self.FIRST_HOST in msg and
                "The host " + self.FIRST_HOST + " will not be used for the next IRR queries." in msg and
                "Another attempt will be performed using the next host in the list." in msg
                for msg in self.logger_handler.warnings
            )
        )


class TestIRRDBEnricher_HostsFailover_SingleFailure(TestIRRDBEnricher_HostsFailover):

    HOSTS_TO_FAIL = "one"
    TYPE_OF_ERROR = "failure"

    def test_failure(self, *patches):
        """IRR queries fail-over: single failure"""
        self.setup_builder(self.GENERAL_SIMPLE, self.CLIENTS_SIMPLE)
        self.builder.render_template()

        self.assertEqual(
            self.get_client_info(self.get_client_by_id("AS1_1")),
            ([1, 10, 20, 30], ["192.168.0.0/16", "192.168.1.0/24"])
        )

        self.assertTrue(
            any(
                "Error while parsing bgpq4 output for the following command: 'bgpq4 -h " + self.FIRST_HOST in msg and
                "Another attempt will be performed using the next host in the list." in msg
                for msg in self.logger_handler.warnings
            )
        )


class TestIRRDBEnricher_HostsFailover_AllTimeout(TestIRRDBEnricher_HostsFailover):

    HOSTS_TO_FAIL = "all"
    TYPE_OF_ERROR = "timeout"

    def test_failure(self, *patches):
        """IRR queries fail-over: all timeout"""
        with self.assertRaisesRegex(BuilderError, ""):
            self.setup_builder(self.GENERAL_SIMPLE, self.CLIENTS_SIMPLE)

        self.assertTrue(
            any(
                "bgpq4 timed out while running the following command: 'bgpq4 -h " + self.FIRST_HOST in msg and
                "The host " + self.FIRST_HOST + " will not be used for the next IRR queries." in msg and
                "Another attempt will be performed using the next host in the list." in msg
                for msg in self.logger_handler.warnings
            )
        )
        self.assertTrue(
            any(
                "bgpq4 timed out while running the following command: 'bgpq4 -h " + self.SECOND_HOST in msg and
                "The host " + self.SECOND_HOST + " will not be used for the next IRR queries." in msg and
                "No more attempts will be performed, all the hosts in the list failed." in msg
                for msg in self.logger_handler.msgs
            )
        )

        self.clear_log()

        with self.assertRaisesRegex(BuilderError, ""):
            self.setup_builder(self.GENERAL_SIMPLE, self.CLIENTS_SIMPLE)

        self.assertTrue(
            any(
                (
                    "Error while retrieving origin ASNs from AS-FAKE1 for client AS1_1: "
                    "Can't get list of authorized ASNs for AS-FAKE1: "
                    "All the IRRD hosts timed out so far; there are no more hosts to use to perform the IRR queries."
                ) in msg
            )
            for msg in self.logger_handler.msgs
        )


class TestIRRDBEnricher_HostsFailover_AllFailure(TestIRRDBEnricher_HostsFailover):

    HOSTS_TO_FAIL = "all"
    TYPE_OF_ERROR = "failure"

    def test_failure(self, *patches):
        """IRR queries fail-over: all failure"""
        with self.assertRaisesRegex(BuilderError, ""):
            self.setup_builder(self.GENERAL_SIMPLE, self.CLIENTS_SIMPLE)

        self.assertTrue(
            any(
                "Error while parsing bgpq4 output for the following command: 'bgpq4 -h " + self.FIRST_HOST in msg and
                "Another attempt will be performed using the next host in the list." in msg
                for msg in self.logger_handler.warnings
            )
        )
        self.assertTrue(
            any(
                "Error while parsing bgpq4 output for the following command: 'bgpq4 -h " + self.SECOND_HOST in msg and
                "No more attempts will be performed, all the hosts in the list failed." in msg
                for msg in self.logger_handler.msgs
            )
        )

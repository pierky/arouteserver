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

import time

from pierky.arouteserver.builder import BIRDConfigBuilder, OpenBGPDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario
from pierky.arouteserver.tests.live_tests.bird import BIRDInstance
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance, OpenBGPDLatestInstance
from pierky.arouteserver.tests.live_tests.routinator import RoutinatorInstance
from pierky.arouteserver.tests.live_tests.instances import Route

class RPKIRTRScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    TARGET_VERSION = None

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls._setup_rs_instance(),

            cls.CLIENT_INSTANCE_CLASS(
                "AS1_1",
                cls.DATA["AS1_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS1.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
        ]

    def set_instance_variables(self):
        self.rs = self._get_instance_by_name("rs")
        self.AS1_1 = self._get_instance_by_name("AS1_1")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1_1)

    def test_030_routinator_not_running(self):
        """{}: route accepted because validator not running"""
        self.receive_route(self.rs, self.DATA["AS1_1"], self.AS1_1,
                           next_hop=self.AS1_1, as_path="1",
                           std_comms=[], lrg_comms=[],
                           ext_comms=[Route.RFC8097_NOT_FOUND])

    def test_040_spin_up_routinator(self):
        """{}: spin up the validator"""
        routinator = RoutinatorInstance(
            "routinator",
            "192.0.2.10",
            mount=[
                (
                    self.use_static_file("routinator_local_exceptions.json"),
                    "/tmp/routinator_local_exceptions.json"
                )
            ]
        )
        routinator.set_var_dir("{}/var".format(self._get_module_dir()))
        self.INSTANCES.append(routinator)
        routinator.start()

        time.sleep(10)

    def test_050_check_rtr_up(self):
        """{}: check the RTR session is up"""
        raise NotImplementedError()

    def test_051_route_dropped(self):
        """{}: route dropped after spinning the validator up"""
        self.rs.clear_cached_routes()

        with self.assertRaisesRegex(AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS1_1"])


class RPKIRTRScenarioBIRD(RPKIRTRScenario):

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    IP_VER = 4

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER,
                                     target_version=cls.TARGET_VERSION or cls.RS_INSTANCE_CLASS.TARGET_VERSION),
                    "/etc/bird/bird.conf"
                ),
                (
                    cls.use_static_file("rpki_rtr_config.local.BIRD"),
                    "/etc/bird/rpki_rtr_config.local"
                )
            ]
        )

    def test_041_restart_bird_rtr(self):
        """{}: restart the RTR protocol on BIRD to speed up session establishment"""

        # This step is done only to speed up the RTR session
        # establishment, that otherwise would remain down for
        # several minutes before the connection attempt is
        # performed.
        res = self.rs.run_cmd("birdc restart MyValidator1")

        if "MyValidator1: restarted" not in res:
            self.fail("RTR restart not successful: {}".format(res))

    def test_050_check_rtr_up(self):
        """{}: check the RTR session is up"""
        time.sleep(10)

        res = self.rs.run_cmd("birdc show protocol MyValidator1")

        if "Established" not in res:
            self.fail("RTR protocol is not Established: {}".format(res))


class RPKIRTRScenarioOpenBGPD(RPKIRTRScenario):

    CONFIG_BUILDER_CLASS = OpenBGPDConfigBuilder

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("openbgpd", "main.j2", "rs.conf", None,
                                     target_version=cls.TARGET_VERSION or cls.RS_INSTANCE_CLASS.TARGET_VERSION),
                    "/etc/bgpd.conf"
                ),
                (
                    cls.use_static_file("rpki_rtr_config.local.OpenBGPD"),
                    "/etc/bgpd/rpki_rtr_config.local"
                )
            ]
        )

    def test_041_restart_openbgpd(self):
        """{}: restart OpenBGPD to speed up RTR session establishment"""

        # This step is done only to speed up the RTR session
        # establishment, that otherwise would remain down for
        # several minutes before the connection attempt is
        # performed.
        self.rs.stop()
        self.rs.start()

    def test_050_check_rtr_up(self):
        """{}: check the RTR session is up"""
        time.sleep(10)

        res = self.rs.run_cmd("bgpctl show rtr")

        # RTR neighbor is 192.0.2.10, port 3323
        #  Description: MyValidator1
        #  Session ID: 46017 Serial #: 0
        #  Refresh: 590, Retry: 600, Expire: 7200

        #   RTR RefreshTimer     due in 00:09:27
        #   RTR ExpireTimer      due in 01:59:37

        if "Session ID:" not in res:
            self.fail("RTR protocol is not Established:\n{}".format(res))

        res = self.rs.run_cmd("bgpctl show set")

        # arouteserver69# bgpctl show set
        # Type   Name                                 #IPv4   #IPv6 #ASnum Last Change
        # ROA    RPKI ROA                                 1       1      -    00:00:06
        # PREFIX bogons                                  13      29      -    00:00:06

        lines = res.splitlines()
        for line in lines:
            if line.startswith("ROA "):
                parts = line.split()
                if (
                    len(parts) >= 4 and
                    parts[3].isdigit() and
                    int(parts[3]) > 0
                ):
                    break
        else:
            self.fail("No ROAs received via RTR:\n{}".format(res))

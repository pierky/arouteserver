# Copyright (C) 2017-2021 Pier Carlo Chiodi
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

from pierky.arouteserver.builder import BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario
from pierky.arouteserver.tests.live_tests.bird import BIRDInstance
from pierky.arouteserver.tests.live_tests.routinator import RoutinatorInstance

class BIRD2RPKIRTRScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    TARGET_VERSION = "2.0.8"
    IP_VER = None

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER,
                                     target_version=cls.TARGET_VERSION),
                    "/etc/bird/bird.conf"
                ),
                (
                    cls.use_static_file("rpki_rtr_config.local"),
                    "/etc/bird/rpki_rtr_config.local"
                )
            ]
        )

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
                           ext_comms=["generic:0x43000000:0x1"])

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

    def test_041_restart_bird_rtr(self):
        """{}: restart the RTR protocol on BIRD"""

        # This step is done only to speed up the RTR session
        # establishment, that otherwise would remain down for
        # several minutes before the connection attempt is
        # performed.
        res = self.rs.run_cmd("birdc restart MyValidator1")

        if "MyValidator1: restarted" not in res:
            self.fail("RTR restart not successful: {}".format(res))

    def test_042_check_bird_rtr(self):
        """{}: check the RTR protocol on BIRD"""
        time.sleep(10)

        res = self.rs.run_cmd("birdc show protocol MyValidator1")

        if "Established" not in res:
            self.fail("RTR protocol is not Established: {}".format(res))

    def test_050_route_dropped(self):
        """{}: route dropped after spinning the validator up"""
        self.rs.clear_cached_routes()

        self.receive_route(self.rs, self.DATA["AS1_1"], self.AS1_1,
                           next_hop=self.AS1_1, as_path="1",
                           std_comms=[], lrg_comms=[],
                           ext_comms=["generic:0x43000000:0x2"],
                           filtered=True)

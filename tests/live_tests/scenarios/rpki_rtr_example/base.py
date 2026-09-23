# Copyright (C) 2017-2026 Pier Carlo Chiodi
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
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance
from pierky.arouteserver.tests.live_tests.rtrtr import RTRTRInstance
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

    def test_030_validator_not_running(self):
        """{}: routes accepted because validator not running"""

        self.receive_route(self.rs, self.DATA["AS1_1"], self.AS1_1,
                           next_hop=self.AS1_1, as_path="1",
                           std_comms=[], lrg_comms=[],
                           ext_comms=[Route.RFC8097_NOT_FOUND])

        # No ASPA is known yet, so the AS_PATH of these routes can't
        # be ASPA INVALID and they are all accepted.
        for prefix_id in ("AS1_aspa_valid", "AS1_aspa_invalid",
                          "AS1_aspa_unknown"):
            self.receive_route(self.rs, self.DATA[prefix_id], self.AS1_1,
                               next_hop=self.AS1_1)

    def test_040_spin_up_validator(self):
        """{}: spin up the validator"""
        rtrtr = RTRTRInstance(
            "rtrtr",
            "192.0.2.10",
            mount=[
                (
                    self.use_static_file("rtrtr.conf"),
                    "/etc/rtrtr/rtrtr.conf"
                ),
                (
                    self.use_static_file("rpki.json"),
                    "/etc/rtrtr/rpki.json"
                )
            ]
        )
        rtrtr.set_var_dir(self._get_var_dir())
        self.INSTANCES.append(rtrtr)
        rtrtr.start()

        time.sleep(10)

    def test_050_check_rtr_up(self):
        """{}: check the RTR session is up"""
        raise NotImplementedError()

    def test_051_route_dropped(self):
        """{}: RPKI INVALID route dropped after spinning the validator up"""
        self.rs.clear_cached_routes()

        with self.assertRaisesRegex(AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS1_1"])

    def test_052_aspa_invalid_route_dropped(self):
        """{}: ASPA INVALID route dropped after spinning the validator up"""
        self.rs.clear_cached_routes()

        with self.assertRaisesRegex(AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS1_aspa_invalid"])

    def test_053_aspa_valid_and_unknown_accepted(self):
        """{}: ASPA VALID and UNKNOWN routes still accepted"""
        self.rs.clear_cached_routes()

        self.receive_route(self.rs, self.DATA["AS1_aspa_valid"], self.AS1_1,
                           next_hop=self.AS1_1, as_path="1 103")
        self.receive_route(self.rs, self.DATA["AS1_aspa_unknown"], self.AS1_1,
                           next_hop=self.AS1_1, as_path="1 105")


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
        """{}: check the RTR session is up and ASPAs are received"""
        time.sleep(10)

        res = self.rs.run_cmd("birdc show protocols all MyValidator1")

        if "Established" not in res:
            self.fail("RTR protocol is not Established: {}".format(res))

        # ASPAs are carried only by version 2 of the RTR protocol.
        if "Protocol version: 2" not in res:
            self.fail("RTR protocol version is not 2: {}".format(res))

        res = self.rs.run_cmd("birdc show route table ASPA")

        # Table ASPA:
        # 103                   [MyValidator1 10:11:12.345] * (100)
        # 104                   [MyValidator1 10:11:12.345] * (100)
        for customer_asn in ("103", "104"):
            if not any(line.split()[0:1] == [customer_asn]
                       for line in res.splitlines()):
                self.fail("No ASPA received via RTR for AS{}:\n{}".format(
                    customer_asn, res))


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
        """{}: check the RTR session is up and ASPAs are received"""
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

        # ASPA   RPKI ASPA                                -       -      2    00:00:06
        # The number of ASNs is reported in the '#ASnum' column.
        for line in lines:
            if line.startswith("ASPA "):
                parts = line.split()
                if (
                    len(parts) >= 6 and
                    parts[5].isdigit() and
                    int(parts[5]) > 0
                ):
                    break
        else:
            self.fail("No ASPAs received via RTR:\n{}".format(res))

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

from pierky.arouteserver.builder import OpenBGPDConfigBuilder, BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario, \
                                                      LiveScenario_TagRejectPolicy

class MaxPrefixScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    CONFIG_BUILDER_CLASS = None
    TARGET_VERSION = None

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls._setup_rs_instance(),

            cls.CLIENT_INSTANCE_CLASS(
                "AS1",
                cls.DATA["AS1_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS1.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS2",
                cls.DATA["AS2_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS2.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS3",
                cls.DATA["AS3_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS3.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS4",
                cls.DATA["AS4_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS4.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
        ]

    def set_instance_variables(self):
        self.rs = self._get_instance_by_name("rs")
        self.AS1 = self._get_instance_by_name("AS1")
        self.AS2 = self._get_instance_by_name("AS2")
        self.AS3 = self._get_instance_by_name("AS3")
        self.AS4 = self._get_instance_by_name("AS4")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_900_reconfigure(self):
        """{}: reconfigure"""
        self.rs.reload_config()

class MaxPrefixScenarioBIRD(MaxPrefixScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    IP_VER = None

    EXPECTED_LOG_MSG = "receive"

    @classmethod
    def _setup_instances(cls):
        super(MaxPrefixScenarioBIRD, cls)._setup_instances()

        cls.INSTANCES.extend([
            cls.CLIENT_INSTANCE_CLASS(
                "AS5",
                cls.DATA["AS5_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS5.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),

            cls.CLIENT_INSTANCE_CLASS(
                "AS6",
                cls.DATA["AS6_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS6.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            )
        ])

    def set_instance_variables(self):
        super(MaxPrefixScenarioBIRD, self).set_instance_variables()
        self.AS5 = self._get_instance_by_name("AS5")
        self.AS6 = self._get_instance_by_name("AS6")

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER,
                                     cfg_general="general_bird.yml",
                                     cfg_clients="clients_bird.yml",
                                     target_version=cls.TARGET_VERSION or cls.RS_INSTANCE_CLASS.TARGET_VERSION),
                    "/etc/bird/bird.conf"
                )
            ]
        )

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS3)
        self.session_is_up(self.rs, self.AS4)

        self.session_is_up(self.rs, self.AS6)

    def test_020_sessions_up_AS5(self):
        """{}: AS5 session is down (max-prefix hit, action == shutdown)"""
        with self.assertRaisesRegex(AssertionError, "is not up"):
            self.session_is_up(self.rs, self.AS5)

    def test_030_blocked_sessions(self):
        """{}: log is populated: receive limit, routes blocked"""
        log_tpl = "Protocol {{inst}} hits route {expected_log_msg} limit ({limit}), action: block"

        log = log_tpl.format(limit=4, expected_log_msg=self.EXPECTED_LOG_MSG)
        self.log_contains(self.rs, log, {"inst": self.AS1})

        log = log_tpl.format(limit=3, expected_log_msg=self.EXPECTED_LOG_MSG)
        self.log_contains(self.rs, log, {"inst": self.AS2})

        log = log_tpl.format(limit=2, expected_log_msg=self.EXPECTED_LOG_MSG)
        self.log_contains(self.rs, log, {"inst": self.AS3})

        log = log_tpl.format(limit=6, expected_log_msg=self.EXPECTED_LOG_MSG)
        self.log_contains(self.rs, log, {"inst": self.AS4})

    def test_030_blocked_sessions_AS5(self):
        """{}: log is populated: receive limit, session shutdown (AS5)"""
        log_tpl = "Protocol {{inst}} hits route {expected_log_msg} limit ({limit}), action: disable"
        log = log_tpl.format(limit=3, expected_log_msg=self.EXPECTED_LOG_MSG)
        self.log_contains(self.rs, log, {"inst": self.AS5})

    def test_030_blocked_sessions_AS6(self):
        """{}: log is populated: import limit, no warning in the log file (AS6)"""

        log = "Protocol {{inst}} hits route import limit"
        # Please note: opposite=True, it fails if the msg is found in the logs:
        # AS6 announces 2 valid routes + 2 invalid routes, so it doesn't hit
        # the limit because invalid routes are not taken into account.
        self.log_contains(self.rs, log, {"inst": self.AS6}, opposite=True)

    def _get_routes_from(self, asn, include_filtered=False):
        routes = []
        for prefix_num in (1,2,3,4,5,6,7):
            if "AS{}_pref{}".format(asn, prefix_num) not in self.DATA:
                continue
            routes.extend(
                self.rs.get_routes(
                    self.DATA["AS{}_pref{}".format(asn, prefix_num)],
                    include_filtered=include_filtered
                )
            )
        return routes

    def test_040_count_received_prefixes_AS1(self):
        """{}: number of prefixes received by rs from AS1"""
        asn = 1

        self.assertEqual(len(self._get_routes_from(asn)), 4)
        self.assertEqual(len(self._get_routes_from(asn, include_filtered=True)), 4)

    def test_040_count_received_prefixes_AS2(self):
        """{}: number of prefixes received by rs from AS2"""
        asn = 2

        self.assertEqual(len(self._get_routes_from(asn)), 3)
        self.assertEqual(len(self._get_routes_from(asn, include_filtered=True)), 3)

    def test_040_count_received_prefixes_AS3(self):
        """{}: number of prefixes received by rs from AS3"""
        asn = 3

        self.assertEqual(len(self._get_routes_from(asn)), 2)
        self.assertEqual(len(self._get_routes_from(asn, include_filtered=True)), 2)

    def test_040_count_received_prefixes_AS4(self):
        """{}: number of prefixes received by rs from AS4"""
        asn = 4

        self.assertEqual(len(self._get_routes_from(asn)), 6)
        self.assertEqual(len(self._get_routes_from(asn, include_filtered=True)), 6)

    def test_040_count_received_prefixes_AS6(self):
        """{}: number of prefixes received by rs from AS6"""
        asn = 6

        self.assertEqual(len(self._get_routes_from(asn)), 2)
        self.assertEqual(len(self._get_routes_from(asn, include_filtered=True)), 4)

    def test_900_reconfigure(self):
        """{}: reconfigure"""
        self.rs.reload_config()
        self.test_020_sessions_up()

class MaxPrefixScenarioBIRD2(MaxPrefixScenarioBIRD):
    __test__ = False

class MaxPrefixScenarioOpenBGPD(LiveScenario_TagRejectPolicy, MaxPrefixScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = OpenBGPDConfigBuilder

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("openbgpd", "main.j2", "rs.conf", None,
                                     cfg_general=cls._get_cfg_general("general_openbgpd.yml"),
                                     target_version=cls.TARGET_VERSION or cls.RS_INSTANCE_CLASS.TARGET_VERSION),
                    "/etc/bgpd.conf"
                )
            ]
        )

    def test_020_sessions_down(self):
        """{}: sessions are down"""
        for inst in (self.AS1, self.AS2, self.AS3, self.AS4):
            with self.assertRaisesRegex(AssertionError, "is not up"):
                self.session_is_up(self.rs, inst)

    def test_030_clients_receive_maxpref_not(self):
        """{}: clients log max-prefix notification"""
        for inst in (self.AS1, self.AS2, self.AS3, self.AS4):
            self.log_contains(inst, "the_rs: Received: Maximum number of prefixes reached")

class MaxPrefixScenarioOpenBGPDPrevious(MaxPrefixScenarioOpenBGPD):
    __test__ = False

class MaxPrefixScenarioOpenBGPDLatest(MaxPrefixScenarioOpenBGPD):
    __test__ = False

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

from pierky.arouteserver.tests.live_tests.base import LiveScenario, LiveScenario_TagAndRejectRejectPolicy
from pierky.arouteserver.builder import BIRDConfigBuilder

class RFC8950Scenario(LiveScenario_TagAndRejectRejectPolicy, LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    TARGET_VERSION = None

    DATA = {
        "rs_IPAddress":                "2001:db8:1:1::2",

        "AS1_1_IPAddress":             "2001:db8:1:1::11",
        "AS1_2_IPAddress":             "2001:db8:1:1::12",
        "AS2_1_IPAddress":             "2001:db8:1:1::21",
        "AS2_1_authorized_nexthop":    "2001:db8:1:1::22",

        "AS1_v4_route1":               "1.1.1.0/24",
        "AS1_v6_route1":               "2a02:0:1::/48",

        "AS1_v4_route2":               "2.2.2.0/24",
        "AS1_v6_route2":               "2aff:0:1::/48",

        "AS1_v4_route3":               "1.1.3.0/24",
        "AS1_v4_route4":               "11.1.0.0/16",
        "AS1_v4_route5":               "11.3.0.0/16",
        "AS1_v4_route6":               "1.1.4.0/24",
        "AS1_v4_route7":               "104.0.0.0/24",
        "AS1_v4_route8":               "104.1.1.0/24",
        "AS1_v4_route9":               "1.1.5.0/24",
        "AS1_v4_route10":              "1.1.6.0/24",
        "AS1_v4_route11":              "1.1.7.0/24",

        "AS2_v4_route12":              "2.2.1.0/24",

        "AS1_allowed_prefixes_v4":     "1.0.0.0/8",
        "AS1_allowed_prefixes_v6":     "2a02::/32",

        "AS2_allowed_prefixes_v4":     "2.0.0.0/8",
    }

    AS_SET = {
        "AS-AS1": [1],
        "AS-AS2": [2],
    }
    R_SET = {
        "AS-AS1": [
            "AS1_allowed_prefixes_v4",
            "AS1_allowed_prefixes_v6",
        ],
        "AS-AS2": [
            "AS2_allowed_prefixes_v4",
        ],
    }

    # Even though routes are accepted, the following errors show up in BIRD's log.
    ALLOWED_LOG_ERRORS = [
        "AS1_1: Invalid NEXT_HOP attribute - neighbor address 2001:db8:1:1::11",
        "AS1_1: Invalid route 1.1.4.0/24 withdrawn"
    ]

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("bird", "main.j2", "rs.conf", None,
                                     target_version=cls.TARGET_VERSION or cls.RS_INSTANCE_CLASS.TARGET_VERSION),
                    "/etc/bird/bird.conf"
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
                        cls.build_other_cfg("AS1_1.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS1_2",
                cls.DATA["AS1_2_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS1_2.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS2_1",
                cls.DATA["AS2_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS2_1.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
        ]

    def set_instance_variables(self):
        self.AS1_1 = self._get_instance_by_name("AS1_1")
        self.AS1_2 = self._get_instance_by_name("AS1_2")
        self.AS2_1 = self._get_instance_by_name("AS2_1")
        self.rs = self._get_instance_by_name("rs")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1_1)
        self.session_is_up(self.rs, self.AS1_2)

    def test_030_accepted_routes(self):
        """{}: accepted routes"""

        for prefix in (
            self.DATA["AS1_v4_route1"],
            self.DATA["AS1_v6_route1"],
            self.DATA["AS1_v4_route4"],
            self.DATA["AS1_v4_route5"],
            self.DATA["AS1_v4_route7"],
            self.DATA["AS1_v4_route8"],
        ):
            self.receive_route(self.rs, prefix, self.AS1_1,
                            next_hop=self.AS1_1, as_path="1",
                            std_comms=[], lrg_comms=[])

    def test_030_not_in_irr_rset(self):
        """{}: dropped routes, not in r_set"""

        for prefix in (self.DATA["AS1_v4_route2"], self.DATA["AS1_v6_route2"]):
            self.receive_route(self.rs, prefix, filtered=True, reject_reason=12)
            self.log_contains(self.rs, "prefix not in client's r_set - REJECTING " + prefix)

    def test_030_next_hop_strict_1(self):
        """{}: next hop strict mode on AS1_1"""

        for prefix in (self.DATA["AS1_v4_route3"],):
            self.receive_route(self.rs, prefix, filtered=True, reject_reason=5)
            self.log_contains(self.rs, "NEXT_HOP [" + self.DATA["AS1_2_IPAddress"] + "] not allowed - REJECTING " + prefix)

    def test_030_next_hop_same_as(self):
        """{}: next hop same-as AS1_2"""

        for prefix in (self.DATA["AS1_v4_route6"],):
            self.receive_route(self.rs, prefix, self.AS1_2,
                               next_hop=self.AS1_1, as_path="1",
                               std_comms=[], lrg_comms=[])

    def test_030_next_hop_authorized_address(self):
        """{}: next hop authorized address AS2_1"""

        for prefix in (self.DATA["AS2_v4_route12"],):
            self.receive_route(self.rs, prefix, self.AS2_1,
                               next_hop=self.DATA["AS2_1_authorized_nexthop"],
                               as_path="2",
                               std_comms=[], lrg_comms=[])

    def test_030_rpki_rejected_as0(self):
        """{}: RPKI rejected routes, AS0"""
        for prefix in (self.DATA["AS1_v4_route9"],):
            self.receive_route(self.rs, prefix, filtered=True, reject_reason=14,
                               ext_comms=["rfc8097-invalid"])
            self.log_contains(self.rs, "RPKI, route is INVALID - REJECTING " + prefix)

    def test_030_rpki_valid(self):
        """{}: RPKI VALID routes"""
        for prefix in (self.DATA["AS1_v4_route10"],):
            self.receive_route(self.rs, prefix, self.AS1_1,
                               next_hop=self.AS1_1, as_path="1",
                               std_comms=[], lrg_comms=[], ext_comms=["rfc8097-valid"])

    def test_030_rpki_rejected_invalid(self):
        """{}: RPKI rejected routes, INVALID"""
        for prefix in (self.DATA["AS1_v4_route11"],):
            self.receive_route(self.rs, prefix, filtered=True, reject_reason=14,
                               ext_comms=["rfc8097-invalid"])
            self.log_contains(self.rs, "RPKI, route is INVALID - REJECTING " + prefix)

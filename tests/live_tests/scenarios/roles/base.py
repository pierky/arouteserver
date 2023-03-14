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
import unittest
from packaging import version

from pierky.arouteserver.builder import BIRDConfigBuilder, OpenBGPDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario
from pierky.arouteserver.tests.live_tests.bird import BIRD2Instance
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance


class RolesScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    IP_VER = None
    TARGET_VERSION = None

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder

    # Populated on the BGP-speaker-specific classes.
    AS2_EXPECTED_ROUTES = []

    @classmethod
    def _setup_rs_instance(cls):
        raise NotImplementedError()

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls._setup_rs_instance(),

            BIRD2Instance(
                "AS1",
                cls.DATA["AS1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS1.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            BIRD2Instance(
                "AS2",
                cls.DATA["AS2_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS2.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            BIRD2Instance(
                "AS101",
                cls.DATA["AS101_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS101.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            )
        ]

    def set_instance_variables(self):
        self.AS1 = self._get_instance_by_name("AS1")
        self.AS2 = self._get_instance_by_name("AS2")
        self.AS101 = self._get_instance_by_name("AS101")
        self.rs = self._get_instance_by_name("rs")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.AS1, self.AS101)

    def test_030_route_with_otc_from_as1(self):
        """{}: routes with OTC from AS1"""

        # From https://datatracker.ietf.org/doc/rfc9234/:
        #
        #    The following ingress procedure applies to the processing of the OTC
        #    Attribute on route receipt:
        #
        #    1.  If a route with the OTC Attribute is received from a Customer or
        #        an RS-Client, then it is a route leak and MUST be considered
        #        ineligible (see Section 3).

        # The route is announced by AS101 to AS1, AS1 attaches the OTC attribute
        # to it, then it announces it over the AS1->rs session (because there is
        # no local role on the AS1 side). So the route server receives that
        # route and detects the OTC attribute, and drops it.
        #
        # Please note: this situation is not handled correctly by OpenBGPD (till
        # 7.7): https://github.com/openbgpd-portable/openbgpd-portable/issues/50

        target_version = self.TARGET_VERSION or self.RS_INSTANCE_CLASS.TARGET_VERSION

        if isinstance(self.rs, OpenBGPDInstance) and \
           version.parse(target_version.replace("p0", "")) <= version.parse("7.7"):
            # To be removed when OpenBGPD will fix the issue above.
            raise unittest.SkipTest("wrong behaviour on OpenBGPD <= 7.7")

        prefix = self.DATA["AS101_to_AS1"]

        if isinstance(self.rs, BIRD2Instance):
            for msg in (
                "{AS1}: Route leak detected - OTC attribute from downstream",
                "{AS1}: Invalid route " + prefix + " withdrawn"
            ):
                self.log_contains(self.rs, msg, instances={"AS1": self.AS1})

            # BIRD does not keep track of the route even though it's configured
            # in 'reject_policy.policy: tag' mode.
            with self.assertRaisesRegex(AssertionError, "Routes not found."):
                self.receive_route(self.rs, prefix)
        else:
            self.receive_route(self.rs, prefix, self.AS1, filtered=True, otc=101)

    def test_030_route_with_otc_from_as2(self):
        """{}: routes with OTC from AS2 are dropped"""

        # From https://datatracker.ietf.org/doc/rfc9234/:
        #
        #    The following ingress procedure applies to the processing of the OTC
        #    Attribute on route receipt:
        #
        #    1.  If a route with the OTC Attribute is received from a Customer or
        #        an RS-Client, then it is a route leak and MUST be considered
        #        ineligible (see Section 3).

        # The route is originated by AS2. AS2 has role rs-client on the session
        # towards the route server. Since the route is locally originated, it
        # gets announced to the route server, but the outbound filter forces
        # the OTC attribute when it's processed, and sets it to 202.
        #
        # This test case is complementary to test_030_route_with_otc_from_as1.
        # It leverages the "trick" done in the egress filter of AS2 to simulate
        # a weird situation in which a role-aware BGP speaker would announce a
        # route with the OTC attribute set to a route server, in violation of
        # point n. 2 from the egress procedure from paragraph 5 of the RFC.

        prefix = self.DATA["AS2_route1"]

        for msg in (
            "{AS2}: Route leak detected - OTC attribute from downstream",
            "{AS2}: Invalid route " + prefix + " withdrawn"
        ):
            self.log_contains(self.rs, msg, instances={"AS2": self.AS2})

        # BIRD does not keep track of the route even though it's configured
        # in 'reject_policy.policy: tag' mode.
        if isinstance(self.rs, BIRD2Instance):
            with self.assertRaisesRegex(AssertionError, "Routes not found."):
                self.receive_route(self.rs, prefix)
        else:
            self.receive_route(self.rs, prefix, self.AS2, filtered=True, otc=202)

    def test_030_otc_added(self):
        """{}: OTC is attached to routes without it"""

        # From https://datatracker.ietf.org/doc/rfc9234/:
        #
        #    The following egress procedure applies to the processing of the OTC
        #    Attribute on route advertisement:
        #
        #    1.  If a route is to be advertised to a Customer, a Peer, or an RS-
        #        Client (when the sender is an RS), and the OTC Attribute is not
        #        present, then when advertising the route, an OTC Attribute MUST
        #        be added with a value equal to the AS number of the local AS.

        # The route is originated by AS1 and announced to the route server.
        # There is no role on the AS1->rs session (on the AS1 side), so the
        # OTC attribute is not attached to the route when it's advertised.
        # When the route server propagates that route to AS2, it attaches the
        # OTC with value 999 (route server's ASN), as per RFC9234.

        prefix = self.DATA["AS1_route1"]

        self.receive_route(
            self.rs,
            prefix,
            self.AS1,
            otc=0  # 0 to match routes without OTC attribute.
        )

        self.receive_route(
            self.AS2,
            prefix,
            self.rs,
            otc=999
        )

    def test_040_expected_routes_as2(self):
        """{}: routes expected on AS2"""

        expected_routes = [
            prefix
            for prefix_id, prefix in self.DATA.items()
            if prefix_id in self.AS2_EXPECTED_ROUTES
        ]

        not_expected_routes = [
            prefix
            for prefix_id, prefix in self.DATA.items()
            if prefix_id not in self.AS2_EXPECTED_ROUTES
        ]

        for prefix in expected_routes:
            self.receive_route(self.AS2, prefix, self.rs)

        for prefix in not_expected_routes:
            with self.assertRaisesRegex(AssertionError, "Routes not found."):
                self.receive_route(self.AS2, prefix)


class RolesScenarioBIRD(RolesScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    IP_VER = None

    AS2_EXPECTED_ROUTES = ["AS1_route1"]

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
                )
            ]
        )


class RolesScenarioOpenBGPD(RolesScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = OpenBGPDConfigBuilder
    IP_VER = None

    # The reason why this attribute contains one extra prefix for OpenBGPD
    # can be found inside the comments of test_030_route_with_otc_from_as1 and
    # test_030_route_with_otc_from_as2.
    AS2_EXPECTED_ROUTES = [
        "AS1_route1",

        # To be removed when OpenBGPD will fix the issue https://github.com/openbgpd-portable/openbgpd-portable/issues/50
        "AS101_to_AS1"
    ]

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
                )
            ]
        )

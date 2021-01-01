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

import six
import unittest

from pierky.arouteserver.builder import OpenBGPDConfigBuilder, BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario, \
                                                      LiveScenario_TagRejectPolicy
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance, \
                                                          OpenBGPDPreviousInstance, \
                                                          OpenBGPDLatestInstance
from pierky.arouteserver.tests.live_tests.bird import BIRDInstance

class TagRejectPolicyScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    CONFIG_BUILDER_CLASS = None

    AS_SET = {
        "AS-AS1": [1],
        "AS-AS1_CUSTOMERS": [101],
        "AS-AS2": [2],
        "AS-AS2_CUSTOMERS": [101],
    }
    R_SET = {
        "AS-AS1": [
            "AS1_allowed_prefixes",
            "pref_len1"
        ],
        "AS-AS1_CUSTOMERS": [
            "AS101_allowed_prefixes"
        ],
        "AS-AS2": [
            "AS2_allowed_prefixes"
        ],
        "AS-AS2_CUSTOMERS": [
            "AS101_allowed_prefixes"
        ],
    }

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls._setup_rs_instance(),

            # Run AS3 as soon as possible because it's configured with passive
            # session, so while other instance come up rs has more time to
            # setup the session with it.
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
                "AS101",
                cls.DATA["AS101_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS101.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "rc",
                cls.DATA["RoutesCollector_IPAddress"],
                [
                    (
                        cls.build_other_cfg("RC.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            )
        ]

    def set_instance_variables(self):
        self.AS1_1 = self._get_instance_by_name("AS1_1")
        self.AS1_2 = self._get_instance_by_name("AS1_2")
        self.AS2 = self._get_instance_by_name("AS2")
        # AS3 is passive, rs client configured with passive: False
        self.AS3 = self._get_instance_by_name("AS3")
        self.AS101 = self._get_instance_by_name("AS101")
        self.rs = self._get_instance_by_name("rs")
        self.rc = self._get_instance_by_name("rc")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1_1)
        self.session_is_up(self.rs, self.AS1_2)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS3)
        self.session_is_up(self.rs, self.rc)
        self.session_is_up(self.AS101, self.AS1_1)
        self.session_is_up(self.AS101, self.AS1_2)
        self.session_is_up(self.AS101, self.AS2)

    def test_040_bogon1(self):
        """{}: bogon prefix"""
        self.receive_route(self.rc, self.DATA["bogon1"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:2"],
                ext_comms=["rt:65520:1"])

    def test_040_bogon1_wrong_announcing_asn(self):
        """{}: bogon prefix, wrong announcing ASN"""
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.rc, self.DATA["bogon1"],
                    self.rs, next_hop=self.AS1_1,
                    filtered=False, std_comms=["65520:0", "65520:2"],
                    ext_comms=["rt:65520:111"])

    def test_040_local1(self):
        """{}: local black list"""
        self.receive_route(self.rc, self.DATA["local1"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:3"],
                ext_comms=["rt:65520:1"])

    def test_040_pref_len1(self):
        """{}: prefix length"""
        self.receive_route(self.rc, self.DATA["pref_len1"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:13"],
                ext_comms=["rt:65520:1"])

    def test_040_peer_as1(self):
        """{}: invalid left-most ASN"""
        self.receive_route(self.rc, self.DATA["peer_as1"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:6"],
                ext_comms=["rt:65520:1"])

    def test_040_invalid_asn1(self):
        """{}: invalid ASN in AS_PATH"""
        self.receive_route(self.rc, self.DATA["invalid_asn1"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:7"],
                ext_comms=["rt:65520:1"])

    def test_040_aspath_len1(self):
        """{}: AS_PATH too long"""
        self.receive_route(self.rc, self.DATA["aspath_len1"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:1"],
                ext_comms=["rt:65520:1"])

    def test_040_invalid_nexthop(self):
        """{}: invalid NEXT_HOP"""
        self.receive_route(self.rc, self.DATA["AS2_nonclient_nexthop2"],
                self.rs, next_hop=self.DATA["AS2_nonclient_nexthop2_nh"],
                filtered=False, std_comms=["65520:0", "65520:5"],
                ext_comms=["rt:65520:2"])

    def test_040_transitfree_asn(self):
        """{}: transit-free ASN in AS_PATH"""
        self.receive_route(self.rc, self.DATA["AS101_transitfree_1"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:8"],
                ext_comms=["rt:65520:1"])

    def test_040_client_blacklist(self):
        """{}: prefix in client's blacklist"""
        self.receive_route(self.rc, self.DATA["AS3_blacklist1"],
                self.rs, next_hop=self.AS3,
                filtered=False, std_comms=["65520:0", "65520:11"],
                ext_comms=["rt:65520:3"])

    def test_040_prefix_not_in_asset(self):
        """{}: prefix not in as-macro"""
        self.receive_route(self.rc, self.DATA["AS101_no_rset"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:12"],
                ext_comms=["rt:65520:1"])

    def test_040_origin_not_in_asset(self):
        """{}: origin not in as-macro"""
        r = self.receive_route(self.rc, self.DATA["AS102_no_asset"],
                self.rs, next_hop=self.AS1_1,
                filtered=False,
                ext_comms=["rt:65520:1"])
        # The reject community and reject cause community are
        # tested in that way because, after white_list_route,
        # rejected routes may also be tagged with
        # "prefix/origin is not present in AS-SET" comms,
        # so a straight match could fail.
        self.assertTrue("65520:0" in r.std_comms)
        self.assertTrue("65520:9" in r.std_comms)

    def test_040_no_ipv6_global_unicast(self):
        """{}: prefix is not in IPv6 global unicast space"""
        if "AS101_no_ipv6_gl_uni" not in self.DATA:
            raise unittest.SkipTest("IPv6 only test")
        self.receive_route(self.rc, self.DATA["AS101_no_ipv6_gl_uni"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:10"],
                ext_comms=["rt:65520:1"])

    def test_040_rpki_invalid(self):
        """{}: RPKI INVALID route"""
        if isinstance(self.rs, OpenBGPDInstance):
            raise unittest.SkipTest("RPKI not supported by OpenBGPD")

        self.receive_route(self.rc, self.DATA["AS101_roa_invalid1"],
                self.rs, next_hop=self.AS1_1,
                filtered=False, std_comms=["65520:0", "65520:14"],
                ext_comms=["rt:65520:1"])

    def test_100_good_routes_not_seen_by_rc(self):
        """{}: good routes not received"""
        for prefix in ("AS1_good1", "AS1_good2", "AS1_good3",
                       "AS2_good1", "AS2_good2", "AS2_blackhole1",
                       "AS2_blackhole2", "AS2_nonclient_nexthop1",
                       "AS3_cc_AS1only", "AS3_cc_not_AS1", "AS3_cc_none",
                       "AS3_prepend1any", "AS3_prepend2any", "AS3_prepend3any",
                       "AS3_prepend1_AS1", "AS3_prepend2_AS2",
                       "AS3_prep3AS1_1any", "AS3_noexport_any",
                       "AS3_noexport_AS1"):
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(self.rc, self.DATA[prefix])

    def test_100_prefixes_received_by_clients_AS1_1(self):
        """{}: prefixes received by clients: AS1_1"""
        self.receive_route(self.AS1_1, self.DATA["AS2_good1"], self.rs, as_path="2", next_hop=self.AS2,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        self.receive_route(self.AS1_1, self.DATA["AS2_good2"], self.rs, as_path="2", next_hop=self.AS2,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        self.receive_route(self.AS1_1, self.DATA["AS2_nonclient_nexthop1"],
                           self.rs, as_path="2",
                           next_hop=self.DATA["AS2_nonclient_nexthop1_nh"],
                           std_comms=[], ext_comms=[], lrg_comms=[])

    def test_100_prefixes_received_by_clients_AS1_2(self):
        """{}: prefixes received by clients: AS1_2"""

        self.receive_route(self.AS1_2, self.DATA["AS2_good1"], self.rs, as_path="2", next_hop=self.AS2,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        self.receive_route(self.AS1_2, self.DATA["AS2_good2"], self.rs, as_path="2", next_hop=self.AS2,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        self.receive_route(self.AS1_2, self.DATA["AS2_nonclient_nexthop1"],
                           self.rs, as_path="2",
                           next_hop=self.DATA["AS2_nonclient_nexthop1_nh"],
                           std_comms=[], ext_comms=[], lrg_comms=[])

    def test_100_prefixes_received_by_clients_AS2(self):
        """{}: prefixes received by clients: AS2"""

        self.receive_route(self.AS2, self.DATA["AS1_good1"], self.rs, as_path="1", next_hop=self.AS1_1,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        self.receive_route(self.AS2, self.DATA["AS1_good2"], self.rs, as_path="1", next_hop=self.AS1_1,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        self.receive_route(self.AS2, self.DATA["AS1_good3"], self.rs, as_path="1", next_hop=self.AS1_1,
                           std_comms=[], ext_comms=[], lrg_comms=[])

    def test_900_reconfigure(self):
        """{}: reconfigure"""
        self.rs.reload_config()
        self.test_020_sessions_up()

class TagRejectPolicyScenarioBIRD(LiveScenario_TagRejectPolicy, TagRejectPolicyScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    TARGET_VERSION = None
    IP_VER = None

    @classmethod
    def _get_local_file_name(cls):
        return "bird_local_file"

    @classmethod
    def _get_local_file(cls):
        local_filename = cls._get_local_file_name()

        res = []
        for ip_ver in (4, 6):
            if ip_ver == cls.IP_VER or cls.IP_VER is None:
                res.append(
                    (
                        cls.use_static_file("{}.local{}".format(local_filename, ip_ver)),
                        "/etc/bird/footer{}.local".format(ip_ver)
                    )
                )
        return res

    @classmethod
    def _setup_rs_instance(cls):
        if cls.IP_VER is None:
            ip_vers = [4, 6]
        else:
            ip_vers = [cls.IP_VER]

        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER,
                                     local_files=["footer{}".format(ip_ver) for ip_ver in ip_vers],
                                     target_version=cls.TARGET_VERSION),
                    "/etc/bird/bird.conf"
                )
            ] + cls._get_local_file(),
        )

class TagRejectPolicyScenarioBIRD2(TagRejectPolicyScenarioBIRD):
    __test__ = False

    TARGET_VERSION = "2.0.7"

    @classmethod
    def _get_local_file_name(cls):
        return "bird2_local_file"

class TagRejectPolicyScenarioOpenBGPDPrevious(LiveScenario_TagRejectPolicy, TagRejectPolicyScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = OpenBGPDConfigBuilder
    TARGET_VERSION = OpenBGPDPreviousInstance.BGP_SPEAKER_VERSION

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("openbgpd", "main.j2", "rs.conf", None,
                                     local_files_dir="/etc/bgpd",
                                     local_files=["post-clients", "post-filters"],
                                     target_version=cls.TARGET_VERSION),
                    "/etc/bgpd.conf"
                ),
                (
                    cls.use_static_file("openbgpd_post-clients.local"),
                    "/etc/bgpd/post-clients.local"
                ),
                (
                    cls.use_static_file("openbgpd_post-filters.local"),
                    "/etc/bgpd/post-filters.local"
                )
            ]
        )

class TagRejectPolicyScenarioOpenBGPDLatest(TagRejectPolicyScenarioOpenBGPDPrevious, TagRejectPolicyScenario):
    __test__ = False

    TARGET_VERSION = OpenBGPDLatestInstance.BGP_SPEAKER_VERSION

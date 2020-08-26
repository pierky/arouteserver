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

import six
import unittest

from pierky.arouteserver.builder import OpenBGPDConfigBuilder, BIRDConfigBuilder
from pierky.arouteserver.ipaddresses import IPNetwork
from pierky.arouteserver.tests.live_tests.base import LiveScenario, \
                                                      LiveScenario_TagRejectPolicy, \
                                                      LiveScenario_TagAndRejectRejectPolicy
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance, \
                                                          OpenBGPDPreviousInstance, \
                                                          OpenBGPDLatestInstance
from pierky.arouteserver.tests.live_tests.bird import BIRDInstance
from pierky.arouteserver.tests.live_tests.exabgp import ExaBGPInstance

class BasicScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    CONFIG_BUILDER_CLASS = None

    AS_SET = {
        "AS-AS1": [1],
        "AS-AS1_CUSTOMERS": [101, 103, 104],
        "AS-AS2": [2],
        "AS-AS2_CUSTOMERS": [101, 103],
        "AS-AS222": [333],
    }
    R_SET = {
        "AS-AS1": [
            "AS1_allowed_prefixes",
            "pref_len1"
        ],
        "AS-AS1_CUSTOMERS": [
            "AS101_allowed_prefixes",
            "AS103_allowed_prefixes",
        ],
        "AS-AS2": [
            "AS2_allowed_prefixes"
        ],
        "AS-AS2_CUSTOMERS": [
            "AS101_allowed_prefixes",
            "AS103_allowed_prefixes",
        ],
        "AS-AS222": [
            "AS222_allowed_prefixes"
        ],
    }
    RTT = {
        "AS1_1_IPAddress": 0.1,
        "AS1_2_IPAddress": 5,
        "AS2_1_IPAddress": 17.3,
        "AS3_1_IPAddress": 123.8,
        "AS4_1_IPAddress": 600
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
                "AS4",
                cls.DATA["AS4_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS4.j2"),
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
            ExaBGPInstance(
                "AS222",
                cls.DATA["AS222_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS222.j2"),
                        "/etc/exabgp/exabgp.conf"
                    ),
                    (
                        cls.use_static_file("exabgp.env"),
                        "/etc/exabgp/exabgp.env"
                    )
                ],
            )
        ]

    def set_instance_variables(self):
        self.AS1_1 = self._get_instance_by_name("AS1_1")
        self.AS1_2 = self._get_instance_by_name("AS1_2")
        self.AS2 = self._get_instance_by_name("AS2")
        # AS3 is passive, rs client configured with passive: False
        self.AS3 = self._get_instance_by_name("AS3")
        self.AS4 = self._get_instance_by_name("AS4")
        self.AS101 = self._get_instance_by_name("AS101")
        self.AS222 = self._get_instance_by_name("AS222")
        self.rs = self._get_instance_by_name("rs")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1_1)
        self.session_is_up(self.rs, self.AS1_2)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS3)
        self.session_is_up(self.rs, self.AS4)
        self.session_is_up(self.rs, self.AS222)
        self.session_is_up(self.AS101, self.AS1_1)
        self.session_is_up(self.AS101, self.AS1_2)
        self.session_is_up(self.AS101, self.AS2)

    def test_021_session_configured_via_local_files(self):
        """{}: session configured via local include files"""

        # A dummy session is configured using local include files.
        # The following tests if those files are really included.
        self.session_exists(self.rs, self.DATA["RoutesCollector_IPAddress"])

    def test_030_good_prefixes_received_by_rs(self):
        """{}: good prefixes received by rs"""
        if isinstance(self.rs, BIRDInstance):
            ext_comm_rpki_unknown = ["generic:0x43000000:0x1"]
        else:
            ext_comm_rpki_unknown = []
        self.receive_route(self.rs, self.DATA["AS1_good1"], self.AS1_1,
                           next_hop=self.AS1_1, as_path="1",
                           std_comms=[], ext_comms=ext_comm_rpki_unknown, lrg_comms=[])
        self.receive_route(self.rs, self.DATA["AS1_good2"], self.AS1_1,
                           next_hop=self.AS1_1, as_path="1",
                           std_comms=[], ext_comms=ext_comm_rpki_unknown, lrg_comms=[])
        self.receive_route(self.rs, self.DATA["AS1_good1"], self.AS1_2,
                           next_hop=self.AS1_2, as_path="1",
                           std_comms=[], ext_comms=ext_comm_rpki_unknown, lrg_comms=[])
        self.receive_route(self.rs, self.DATA["AS1_good2"], self.AS1_2,
                           next_hop=self.AS1_2, as_path="1",
                           std_comms=[], ext_comms=ext_comm_rpki_unknown, lrg_comms=[])
        # AS1_good3 is announced by AS1_2 with NEXT_HOP = AS1_1
        self.receive_route(self.rs, self.DATA["AS1_good3"], self.AS1_2,
                           next_hop=self.AS1_1, as_path="1",
                           std_comms=[], ext_comms=ext_comm_rpki_unknown, lrg_comms=[])
        self.receive_route(self.rs, self.DATA["AS2_good1"], self.AS2,
                           next_hop=self.AS2, as_path="2",
                           std_comms=[], ext_comms=ext_comm_rpki_unknown, lrg_comms=[])
        self.receive_route(self.rs, self.DATA["AS2_good2"], self.AS2,
                           next_hop=self.AS2, as_path="2",
                           std_comms=[], ext_comms=ext_comm_rpki_unknown, lrg_comms=[])

        # rs should not receive prefixes with the following criteria
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS1_good1"], self.AS2)
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS1_good2"], self.AS2)
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS2_good1"], self.AS1_1)
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS2_good2"], self.AS1_1)

        # AS_PATH should match the expectations
        self.receive_route(self.rs, self.DATA["AS1_good1"], self.AS1_1, as_path="1")
        self.receive_route(self.rs, self.DATA["AS2_good1"], self.AS2, as_path="2")

        # NEXT_HOP should match the expectations
        self.receive_route(self.rs, self.DATA["AS1_good1"], self.AS1_1, as_path="1", next_hop=self.AS1_1)
        self.receive_route(self.rs, self.DATA["AS2_good1"], self.AS2, as_path="2", next_hop=self.AS2)

    def test_030_good_prefixes_because_of_rpki_roas_as_route_objects_1(self):
        """{}: good prefixes because of use_rpki_roas_as_route_objects: exact"""

        prefix = self.DATA["AS101_roa_routeobj_1"]
        self.receive_route(self.rs, prefix,
                           self.AS1_1, as_path="1 101", next_hop=self.AS1_1)
        self.receive_route(self.rs, prefix,
                           self.AS2, as_path="2 101", next_hop=self.AS2)

    def test_030_good_prefixes_because_of_rpki_roas_as_route_objects_2(self):
        """{}: good prefixes because of use_rpki_roas_as_route_objects: covering"""

        prefix = self.DATA["AS101_roa_routeobj_3"]
        self.receive_route(self.rs, prefix,
                           self.AS1_1, as_path="1 101", next_hop=self.AS1_1)
        self.receive_route(self.rs, prefix,
                           self.AS2, as_path="2 101", next_hop=self.AS2)

    def test_030_good_prefixes_because_of_arin_db_1(self):
        """{}: good prefixes because of use_arin_bulk_whois_data"""

        prefix = self.DATA["AS104_arin_1"]
        self.receive_route(self.rs, prefix,
                           self.AS1_1, as_path="1 101 104",
                           next_hop=self.AS1_1)

        # AS101 peers with AS2 too but that route should be reject
        # because only AS1 has AS104 in its AS-SET
        self.receive_route(self.rs, prefix,
                           self.AS2, as_path="2 101 104", next_hop=self.AS2,
                           filtered=True, reject_reason=9)

        self.receive_route(self.AS4, prefix, self.rs, as_path="1 101 104",
                           next_hop=self.AS1_1)

    def test_030_good_prefixes_because_of_registrobr_db_1(self):
        """{}: good prefixes because of use_registrobr_bulk_whois_data"""

        prefix = self.DATA["AS104_nicbr_1"]
        self.receive_route(self.rs, prefix,
                           self.AS1_1, as_path="1 101 104",
                           next_hop=self.AS1_1)

        # AS101 peers with AS2 too but that route should be reject
        # because only AS1 has AS104 in its AS-SET
        self.receive_route(self.rs, prefix,
                           self.AS2, as_path="2 101 104", next_hop=self.AS2,
                           filtered=True, reject_reason=9)

        self.receive_route(self.AS4, prefix, self.rs, as_path="1 101 104",
                           next_hop=self.AS1_1)

    def test_030_good_prefixes_received_by_rs_nonclient_nexthop(self):
        """{}: good prefixes received by rs: non-client NEXT_HOP"""

        self.receive_route(self.rs, self.DATA["AS2_nonclient_nexthop1"],
                           as_path="2",
                           next_hop=self.DATA["AS2_nonclient_nexthop1_nh"])

    def test_030_good_prefixes_because_of_irrdb_whitelist(self):
        """{}: good prefixes received by rs: IRRdb white-list"""

        self.receive_route(self.rs, self.DATA["AS1_whitel_1"], as_path="1 1011")
        self.receive_route(self.rs, self.DATA["AS1_whitel_4"], as_path="1 1011")
        self.receive_route(self.rs, self.DATA["AS1_whitel_5"], as_path="1 1000")

    def test_040_bad_prefixes_received_by_rs_aggregate1(self):
        """{}: bad prefixes received by rs: AS_SET origin, RFC6907 7.1.9"""

        # Route that is allowed by an explicit 'white_list_route' that matches
        # the prefix but that doesn't enforce the origin ASN (so that the IRR
        # origin validation check is passed), but that later on is rejected by
        # the RPKI BOV check.
        #
        # Details on https://github.com/pierky/arouteserver/pull/56

        self.receive_route(self.rs, self.DATA["AS222_aggregate1"],
                           as_path="222 333", as_set="333 333",
                           filtered=True, reject_reason=14)

    def test_040_bad_prefixes_received_by_rs_aggregate2(self):
        """{}: bad prefixes received by rs: IRR check for AS_SET origin, BIRD"""

        if isinstance(self.rs, OpenBGPDInstance):
            raise unittest.SkipTest("BIRD specific")

        # Route that is rejected by the IRR-based origin validation check.
        #
        # This test case is specific for BIRD, it's used to verify that
        # bgp_path.last would not match any ASN in the right-most AS_SET
        # used to originate this route nor the last non aggregated ASN,
        # regardless of the fact that they are all 333 (which is included
        # in the IRR as-set for this client).
        #
        # Details on https://github.com/pierky/arouteserver/pull/56

        self.receive_route(self.rs, self.DATA["AS222_aggregate2"],
                           as_path="222 333", as_set="333 333",
                           filtered=True, reject_reason=9)

    def test_040_bad_prefixes_received_by_rs_aggregate3(self):
        """{}: bad prefixes received by rs: IRR check for AS_SET origin, OpenBGPD"""

        if isinstance(self.rs, BIRDInstance):
            raise unittest.SkipTest("OpenBGPD specific")

        # Route that is accepted by OpenBGPD.
        #
        # This test covers the behaviour of OpenBGPD, that matches the
        # last non aggregated ASN in the AS_PATH. 333 is the ASN included
        # in the IRR as-set for this client.
        #
        # Details on https://github.com/pierky/arouteserver/pull/56

        self.receive_route(self.rs, self.DATA["AS222_aggregate3"],
                           as_path="222 333", as_set="444 555",
                           filtered=False)

    def test_040_bad_prefixes_received_by_rs_bogon(self):
        """{}: bad prefixes received by rs: bogon"""
        self.receive_route(self.rs, self.DATA["bogon1"], self.AS1_1,
                           as_path="1", next_hop=self.AS1_1,
                           filtered=True, reject_reason=2)
        self.log_contains(self.rs, "prefix is bogon - REJECTING " + self.DATA["bogon1"])

    def test_040_bad_prefixes_received_by_rs_global_blacklist(self):
        """{}: bad prefixes received by rs: global blacklist"""

        self.receive_route(self.rs, self.DATA["local1"], self.AS1_1,
                           as_path="1", next_hop=self.AS1_1,
                           filtered=True, reject_reason=3)
        self.log_contains(self.rs, "prefix is in global blacklist - REJECTING " + self.DATA["local1"])

    def test_040_bad_prefixes_received_by_rs_prefix_len(self):
        """{}: bad prefixes received by rs: invalid prefix-len"""

        ip_ver = IPNetwork(self.DATA["pref_len1"]).version

        self.receive_route(self.rs, self.DATA["pref_len1"], self.AS1_1,
                           as_path="1", next_hop=self.AS1_1,
                           filtered=True, reject_reason=13)
        pref_len = 7 if ip_ver == 4 else 16
        pref_len_range = "8-24" if ip_ver == 4 else "17-48"
        self.log_contains(self.rs, "prefix len [{}] not in {} - REJECTING {}".format(
            pref_len, pref_len_range, self.DATA["pref_len1"]))

    def test_040_bad_prefixes_received_by_rs_leftmost_asn(self):
        """{}: bad prefixes received by rs: left-most ASN"""

        self.receive_route(self.rs, self.DATA["peer_as1"], self.AS1_1,
                           as_path="2 1", next_hop=self.AS1_1,
                           filtered=True, reject_reason=6)
        self.log_contains(self.rs, "invalid left-most ASN [2] - REJECTING " + self.DATA["peer_as1"])

    def test_040_bad_prefixes_received_by_rs_invalid_aspath(self):
        """{}: bad prefixes received by rs: invalid ASN in AS-PATH"""

        self.receive_route(self.rs, self.DATA["invalid_asn1"], self.AS1_1,
                           as_path="1 65536 1", next_hop=self.AS1_1,
                           filtered=True, reject_reason=7)
        self.log_contains(self.rs, "AS_PATH [(path 1 65536 1)] contains invalid ASN - REJECTING " + self.DATA["invalid_asn1"])

    def test_040_bad_prefixes_received_by_rs_transitfree_as_path(self):
        """{}: bad prefixes received by rs: transit-free ASN in AS-PATH"""

        self.receive_route(self.rs, self.DATA["AS101_transitfree_1"],
                           self.AS1_1, as_path="1 101 174",
                           next_hop=self.AS1_1, filtered=True, reject_reason=8)
        self.log_contains(self.rs, "AS_PATH [(path 1 101 174)] contains transit-free ASN - REJECTING " + self.DATA["AS101_transitfree_1"])

    def test_040_bad_prefixes_received_by_rs_transitfree_as_path_transit_peer(self):
        """{}: bad prefixes received by rs: transit-free ASN in AS-PATH from a transit peer"""

        self.receive_route(self.rs, self.DATA["AS3_transitfree_2"],
                           self.AS3, as_path="3 174 33",
                           next_hop=self.AS3, filtered=True, reject_reason=8)
        self.log_contains(self.rs, "AS_PATH [(path 3 174 33)] contains transit-free ASN - REJECTING " + self.DATA["AS3_transitfree_2"])

    def test_040_bad_prefixes_received_by_rs_never_via_rs_peeringdb(self):
        """{}: bad prefixes received by rs: never via route servers ASN in AS-PATH (PeeringDB)"""

        self.receive_route(self.rs, self.DATA["AS101_neverviars_1"],
                           self.AS1_1, as_path="1 101 666",
                           next_hop=self.AS1_1, filtered=True, reject_reason=15)
        self.log_contains(self.rs, "AS_PATH [(path 1 101 666)] contains never via route-servers ASN - REJECTING " + self.DATA["AS101_neverviars_1"])

    def test_040_bad_prefixes_received_by_rs_never_via_rs_asn(self):
        """{}: bad prefixes received by rs: never via route servers ASN in AS-PATH (asns list)"""

        self.receive_route(self.rs, self.DATA["AS101_neverviars_2"],
                           self.AS1_1, as_path="1 101 777",
                           next_hop=self.AS1_1, filtered=True, reject_reason=15)
        self.log_contains(self.rs, "AS_PATH [(path 1 101 777)] contains never via route-servers ASN - REJECTING " + self.DATA["AS101_neverviars_2"])

    def test_040_bad_prefixes_received_by_rs_aspath_len(self):
        """{}: bad prefixes received by rs: AS_PATH len"""

        self.receive_route(self.rs, self.DATA["aspath_len1"], self.AS1_1,
                           as_path="1 2 2 2 2 2 2 1", next_hop=self.AS1_1,
                           filtered=True, reject_reason=1)
        self.log_contains(self.rs, "AS_PATH len [8] longer than 6 - REJECTING " + self.DATA["aspath_len1"])

    def test_040_bad_prefixes_received_by_rs_client_blacklist(self):
        """{}: bad prefixes received by rs: client blacklist"""

        self.receive_route(self.rs, self.DATA["AS3_blacklist1"], self.AS3,
                           as_path="3", next_hop=self.AS3,
                           filtered=True, reject_reason=11)
        self.log_contains(self.rs, "prefix is in client's blacklist - REJECTING " + self.DATA["AS3_blacklist1"])

    def test_040_bad_prefixes_received_by_rs_invalid_nexthop(self):
        """{}: bad prefixes received by rs: invalid NEXT_HOP"""

        self.receive_route(self.rs, self.DATA["AS101_good1"], self.AS1_2,
                           as_path="1 101", next_hop=self.AS101,
                           filtered=True, reject_reason=5)
        self.log_contains(self.rs, "NEXT_HOP [" + self.AS101.ip + "] not allowed - REJECTING " + self.DATA["AS101_good1"])

    def test_040_bad_prefixes_received_by_rs_unknown_nonclient_nexthop(self):
        """{}: bad prefixes received by rs: unknown NEXT_HOP"""

        self.receive_route(self.rs, self.DATA["AS2_nonclient_nexthop2"],
                           self.AS2, as_path="2",
                           next_hop=self.DATA["AS2_nonclient_nexthop2_nh"],
                           filtered=True, reject_reason=5)
        self.log_contains(self.rs, "NEXT_HOP [" + self.DATA["AS2_nonclient_nexthop2_nh"] + "] not allowed - REJECTING " + self.DATA["AS2_nonclient_nexthop2"])

    def test_040_bad_prefixes_received_by_rs_no_rset(self):
        """{}: bad prefixes received by rs: prefix not in AS-SET"""

        # AS101_no_rset is not included in AS-AS1_CUSTOMERS nor in AS-AS2_CUSTOMERS, so it's
        # rejected by the rs.
        self.receive_route(self.rs, self.DATA["AS101_no_rset"], self.AS1_1,
                           as_path="1 101", next_hop=self.AS1_1,
                           filtered=True, reject_reason=12)
        self.receive_route(self.rs, self.DATA["AS101_no_rset"], self.AS2,
                           as_path="2 101", next_hop=self.AS2,
                           filtered=True, reject_reason=12)
        self.log_contains(self.rs, "prefix not in client's r_set - REJECTING " + self.DATA["AS101_no_rset"])

    def test_040_bad_prefixes_received_by_rs_no_asset(self):
        """{}: bad prefixes received by rs: origin not in AS-SET"""

        # AS102_no_asset is announced by an (hypothetical) AS102 to AS101,
        # and AS102 is not included in AS-AS1_CUSTOMERS nor in AS-AS2_CUSTOMERS, so it's
        # rejected by the rs.
        self.receive_route(self.rs, self.DATA["AS102_no_asset"], self.AS1_1,
                           as_path="1 101 102", next_hop=self.AS1_1,
                           filtered=True, reject_reason=9)
        self.receive_route(self.rs, self.DATA["AS102_no_asset"], self.AS2,
                           as_path="2 101 102", next_hop=self.AS2,
                           filtered=True, reject_reason=9)
        self.log_contains(self.rs, "origin ASN [102] not in allowed as-sets - REJECTING " + self.DATA["AS102_no_asset"])

    def test_040_bad_prefix_not_ipv6_global_unicat(self):
        """{}: bad prefixes received by rs: not IPv6 global unicast space"""
        if "AS101_no_ipv6_gl_uni" not in self.DATA:
            # it's an IPv4-only scenario
            return
        self.receive_route(self.rs, self.DATA["AS101_no_ipv6_gl_uni"],
                           filtered=True, reject_reason=10)
        self.log_contains(self.rs, "prefix is not in IPv6 Global Unicast space - REJECTING " + self.DATA["AS101_no_ipv6_gl_uni"])

    def test_040_default_rejected_by_rs(self):
        """{}: bad prefixes received by rs: default route"""
        self.receive_route(self.rs, self.DATA["Default_route"],
                           other_inst=self.AS3,
                           filtered=True, reject_reason=(2, 10))
        if IPNetwork(self.DATA["Default_route"]).version == 4:
            msg = "prefix is bogon - REJECTING " + self.DATA["Default_route"]
        else:
            msg = "prefix is not in IPv6 Global Unicast space - REJECTING " + self.DATA["Default_route"]
        self.log_contains(self.rs, msg)

    def test_040_bad_prefixes_even_if_irrdb_whitelist(self):
        """{}: bad prefixes received by rs: IRRdb white-list"""

        self.receive_route(self.rs, self.DATA["AS1_whitel_2"], as_path="1 1000",
                           filtered=True, reject_reason=9)
        self.log_contains(self.rs, "origin ASN [1000] not in allowed as-sets - REJECTING " + self.DATA["AS1_whitel_2"])

        self.receive_route(self.rs, self.DATA["AS1_whitel_3"], as_path="1 1011",
                           filtered=True, reject_reason=12)
        self.log_contains(self.rs, "prefix not in client's r_set - REJECTING " + self.DATA["AS1_whitel_3"])

        self.receive_route(self.rs, self.DATA["AS1_whitel_6"], as_path="1 1011",
                           filtered=True, reject_reason=12)
        self.log_contains(self.rs, "prefix not in client's r_set - REJECTING " + self.DATA["AS1_whitel_6"])

    def test_040_bad_prefixes_rpki_roas_as_route_objects_failed(self):
        """{}: bad prefixes received by rs: RPKI ROAs as route objects failed"""

        # More specific than ROA
        prefix = self.DATA["AS101_roa_routeobj_2"]
        self.receive_route(self.rs, prefix, self.AS1_1, as_path="1 101",
                           filtered=True, reject_reason=12)
        self.receive_route(self.rs, prefix, self.AS2, as_path="2 101",
                           filtered=True, reject_reason=12)

        # ROA OK but origin ASN not authorized by AS-SET
        prefix = self.DATA["AS101_roa_routeobj_4"]
        self.receive_route(self.rs, prefix, self.AS1_1, as_path="1 101 105",
                           filtered=True, reject_reason=9)
        self.receive_route(self.rs, prefix, self.AS2, as_path="2 101 105",
                           filtered=True, reject_reason=9)

    def test_041_bad_prefixes_not_received_by_clients(self):
        """{}: bad prefixes not received by clients"""
        for prefix in (self.DATA["bogon1"],
                       self.DATA["local1"],
                       self.DATA["pref_len1"],
                       self.DATA["peer_as1"],
                       self.DATA["invalid_asn1"],
                       self.DATA["aspath_len1"],
                       self.DATA["AS2_nonclient_nexthop2"]):
            for inst in (self.AS2, self.AS3, self.AS4):
                with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                    self.receive_route(inst, prefix)

        # Among the clients, only AS3 is expected to not see the
        # following prefixes because AS1 and AS2
        # receive them on their session with AS101
        for prefix in (self.DATA["AS101_no_rset"],
                       self.DATA["AS102_no_asset"],
                       self.DATA["AS101_roa_routeobj_2"],
                       self.DATA["AS101_roa_routeobj_4"]):
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(self.AS3, prefix)

    def test_045_rpki_valid_prefix(self):
        """{}: RPKI, valid prefix received by rs"""

        self.receive_route(self.rs, self.DATA["AS101_roa_valid1"], self.AS1_1,
                           as_path="1 101")
        self.receive_route(self.rs, self.DATA["AS101_roa_valid1"], self.AS2,
                           as_path="2 101")

    def test_045_rpki_invalid_prefix_asn(self):
        """{}: RPKI, invalid prefix (bad ASN) received by rs"""

        if isinstance(self.rs, BIRDInstance):
            ext_comm_rpki_invalid = ["generic:0x43000000:0x2"]
        else:
            ext_comm_rpki_invalid = []

        self.receive_route(self.rs, self.DATA["AS101_roa_invalid1"], self.AS1_1,
                           as_path="1 101", filtered=True,
                           ext_comms=ext_comm_rpki_invalid)
        self.receive_route(self.rs, self.DATA["AS101_roa_invalid1"], self.AS2,
                           as_path="2 101", filtered=True,
                           ext_comms=ext_comm_rpki_invalid)

    def test_045_rpki_invalid_prefix_length(self):
        """{}: RPKI, invalid prefix (bad length) received by rs"""

        if isinstance(self.rs, BIRDInstance):
            ext_comm_rpki_invalid = ["generic:0x43000000:0x2"]
        else:
            ext_comm_rpki_invalid = []

        self.receive_route(self.rs, self.DATA["AS101_roa_badlen"], self.AS1_1,
                           as_path="1 101", filtered=True,
                           ext_comms=ext_comm_rpki_invalid)
        self.receive_route(self.rs, self.DATA["AS101_roa_badlen"], self.AS2,
                           as_path="2 101", filtered=True,
                           ext_comms=ext_comm_rpki_invalid)

    def test_045_rpki_valid_prefix_propagated_to_clients(self):
        """{}: RPKI, valid prefix propagated to clients"""

        self.receive_route(self.AS3, self.DATA["AS101_roa_valid1"], self.rs)

    def test_045_rpki_invalid_prefixes_not_propagated_to_clients(self):
        """{}: RPKI, invalid prefix (bad ASN) not propagated to clients"""

        for pref_id in ("AS101_roa_invalid1", "AS101_roa_badlen"):
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(self.AS3, self.DATA[pref_id])

    def test_045_blackhole_with_roa(self):
        """{}: RPKI, blackhole request for a covered prefix"""

        self.receive_route(self.rs, self.DATA["AS101_roa_blackhole"], self.AS1_1, as_path="1 101",
                           std_comms=["65535:666"], lrg_comms=[])
        self.receive_route(self.rs, self.DATA["AS101_roa_blackhole"], self.AS2, as_path="2 101",
                           std_comms=["65535:666"], lrg_comms=[])
        for inst in (self.AS1_1, self.AS2):
            self.log_contains(self.rs, "blackhole filtering request from {{inst}} - ACCEPTING {}".format(
                self.DATA["AS101_roa_blackhole"]), {"inst": inst})

        next_hop = self.DATA["blackhole_IP"]

        self.receive_route(self.AS3, self.DATA["AS101_roa_blackhole"], self.rs,
                           next_hop=next_hop,
                           std_comms=["65535:666", "65535:65281"], lrg_comms=[])

    def test_050_prefixes_from_AS101_received_by_its_upstreams(self):
        """{}: prefixes from AS101 received by its upstreams"""
        self.receive_route(self.AS1_1, self.DATA["AS101_good1"], self.AS101)
        self.receive_route(self.AS1_2, self.DATA["AS101_good1"], self.AS101)
        self.receive_route(self.AS2, self.DATA["AS101_good1"], self.AS101)

    def test_051_prefixes_from_AS101_received_by_rs(self):
        """{}: prefixes from AS101 received by rs"""

        # rs should receive these prefixes that AS101 announces to AS1 and AS2.
        self.receive_route(self.rs, self.DATA["AS101_good1"], self.AS1_1, as_path="1 101", next_hop=self.AS1_1)
        self.receive_route(self.rs, self.DATA["AS101_good1"], self.AS2, as_path="2 101", next_hop=self.AS2)

        # AS101 peers with AS1_2 on the same network of rs
        # and AS1_2 has not 'next-hop-self' on the session with rs:
        # next-hop received by rs is the one of AS101, so the prefix
        # should be filtered by the rs.
        self.receive_route(self.rs, self.DATA["AS101_good1"], self.AS1_2,
                           as_path="1 101", next_hop=self.AS101,
                           filtered=True, reject_reason=5)

    def test_060_communities_as_seen_by_AS101_upstreams(self):
        """{}: bad communities as seen by AS101 upstreams"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2):
            self.receive_route(inst, self.DATA["AS101_bad_std_comm"], self.AS101, std_comms=["65530:0"])
            self.receive_route(inst, self.DATA["AS101_bad_lrg_comm"], self.AS101, lrg_comms=["999:65530:0"])
            self.receive_route(inst, self.DATA["AS101_other_s_comm"], self.AS101, std_comms=["888:0"])
            self.receive_route(inst, self.DATA["AS101_other_l_comm"], self.AS101, lrg_comms=["888:0:0"])
            self.receive_route(inst, self.DATA["AS101_bad_good_comms"], self.AS101, std_comms=["777:0", "65530:1"], lrg_comms=["777:0:0", "999:65530:1"])

    def test_061_bad_communities_scrubbed_by_rs_std(self):
        """{}: bad communities scrubbed by rs (std)"""

        self.receive_route(self.rs, self.DATA["AS101_bad_std_comm"], self.AS1_1, std_comms=[])
        self.receive_route(self.rs, self.DATA["AS101_bad_std_comm"], self.AS2, std_comms=[])

    def test_061_bad_communities_scrubbed_by_rs_lrg(self):
        """{}: bad communities scrubbed by rs (lrg)"""
        self.receive_route(self.rs, self.DATA["AS101_bad_lrg_comm"], self.AS1_1, lrg_comms=[])
        self.receive_route(self.rs, self.DATA["AS101_bad_lrg_comm"], self.AS2, lrg_comms=[])

    def test_062_other_communities_not_scrubbed_by_rs_std(self):
        """{}: other communities not scrubbed by rs (std)"""

        for inst in (self.AS1_1, self.AS2):
            self.receive_route(self.rs, self.DATA["AS101_other_s_comm"], inst, std_comms=["888:0"])
            self.receive_route(self.rs, self.DATA["AS101_bad_good_comms"], inst, std_comms=["777:0"])

    def test_062_other_communities_not_scrubbed_by_rs_lrg(self):
        """{}: other communities not scrubbed by rs (lrg)"""
        for inst in (self.AS1_1, self.AS2):
            self.receive_route(self.rs, self.DATA["AS101_other_l_comm"], inst, lrg_comms=["888:0:0"])
            self.receive_route(self.rs, self.DATA["AS101_bad_good_comms"], inst, lrg_comms=["777:0:0"])

    def test_070_blackhole_filtering_as_seen_by_rs_BLACKHOLE(self):
        """{}: blackhole filtering requests as seen by rs (BLACKHOLE)"""

        self.receive_route(self.rs, self.DATA["AS2_blackhole1"], self.AS2, next_hop=self.AS2, as_path="2",
                           std_comms=["65535:666"], lrg_comms=[])
        self.log_contains(self.rs, "blackhole filtering request from {AS2_1} - ACCEPTING " + self.DATA["AS2_blackhole1"], {"AS2_1": self.AS2})

    def test_070_blackhole_filtering_as_seen_by_rs_std_cust(self):
        """{}: blackhole filtering requests as seen by rs (std cust)"""

        self.receive_route(self.rs, self.DATA["AS2_blackhole2"], self.AS2, next_hop=self.AS2, as_path="2",
                           std_comms=["65534:0"], lrg_comms=[], ext_comms=[])
        self.log_contains(self.rs, "blackhole filtering request from {AS2_1} - ACCEPTING " + self.DATA["AS2_blackhole2"], {"AS2_1": self.AS2})

    def test_070_blackhole_filtering_as_seen_by_rs_lrg_cust(self):
        """{}: blackhole filtering requests as seen by rs (lrg cust)"""
        self.receive_route(self.rs, self.DATA["AS2_blackhole3"], self.AS2, next_hop=self.AS2, as_path="2",
                           std_comms=[], lrg_comms=["65534:0:0"])
        self.log_contains(self.rs, "blackhole filtering request from {AS2_1} - ACCEPTING " + self.DATA["AS2_blackhole3"], {"AS2_1": self.AS2})

    def test_071_blackholed_prefixes_as_seen_by_enabled_clients_BLACKHOLE(self):
        """{}: blackholed prefixes as seen by enabled clients (BLACKHOLE)"""
        for inst in (self.AS1_1, self.AS3, self.AS4):
            self.receive_route(inst, self.DATA["AS2_blackhole1"], self.rs, next_hop=self.DATA["blackhole_IP"],
                               std_comms=["65535:666", "65535:65281"], lrg_comms=[])

    def test_071_blackholed_prefixes_as_seen_by_enabled_clients_std_cust(self):
        """{}: blackholed prefixes as seen by enabled clients (std_cust)"""
        for inst in (self.AS1_1, self.AS3, self.AS4):
            self.receive_route(inst, self.DATA["AS2_blackhole2"], self.rs, next_hop=self.DATA["blackhole_IP"],
                               std_comms=["65535:666", "65535:65281"], lrg_comms=[])

    def test_071_blackholed_prefixes_as_seen_by_enabled_clients_lrg_cust(self):
        """{}: blackholed prefixes as seen by enabled clients (lrg_cust)"""
        for inst in (self.AS1_1, self.AS3, self.AS4):
            self.receive_route(inst, self.DATA["AS2_blackhole3"], self.rs, next_hop=self.DATA["blackhole_IP"],
                               std_comms=["65535:666", "65535:65281"], lrg_comms=[])

    def test_071_blackholed_prefixes_not_seen_by_not_enabled_clients(self):
        """{}: blackholed prefixes not seen by not enabled clients"""

        # AS1_2 not enabled to receive blackholed prefixes
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.AS1_2, self.DATA["AS2_blackhole1"])
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.AS1_2, self.DATA["AS2_blackhole2"])
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.AS1_2, self.DATA["AS2_blackhole3"])
        self.log_contains(self.rs, "client {{AS1_2}} not enabled to receive blackhole prefixes - NOT ANNOUNCING {pref} TO {{AS1_2}}".format(pref=self.DATA["AS2_blackhole1"]), {"AS1_2": self.AS1_2})
        self.log_contains(self.rs, "client {{AS1_2}} not enabled to receive blackhole prefixes - NOT ANNOUNCING {pref} TO {{AS1_2}}".format(pref=self.DATA["AS2_blackhole2"]), {"AS1_2": self.AS1_2})
        self.log_contains(self.rs, "client {{AS1_2}} not enabled to receive blackhole prefixes - NOT ANNOUNCING {pref} TO {{AS1_2}}".format(pref=self.DATA["AS2_blackhole3"]), {"AS1_2": self.AS1_2})

    def test_075_gshut_enabled_client(self):
        """{}: gshut by an enabled client"""

        prefix = self.DATA["AS103_gshut_1"]

        # AS103's prefix as seen by its upstreams, AS1 and AS2
        for inst in (self.AS1_1, self.AS1_2):
            self.receive_route(inst, prefix, as_path="101 103")
        self.receive_route(self.AS2, prefix, as_path="101 101 103")

        # prefix as seen by the route server (AS1 performed gshut)
        self.receive_route(self.rs, prefix, as_path="1 101 103",
                           other_inst=self.AS1_1,
                           local_pref=5, std_comms=["65535:0"])
        self.receive_route(self.rs, prefix, as_path="2 101 101 103",
                           other_inst=self.AS2,
                           local_pref=100, std_comms=[])

        # prefix as seen by other clients, via AS2 (longest path)
        self.receive_route(self.AS4, prefix, as_path="2 101 101 103",
                           next_hop=self.AS2, std_comms=[])

    def test_075_gshut_not_enabled_client(self):
        """{}: gshut by a not enabled client"""

        prefix = self.DATA["AS103_gshut_2"]

        # AS103's prefix as seen by its upstreams, AS1 and AS2
        for inst in (self.AS1_1, self.AS1_2):
            self.receive_route(inst, prefix, as_path="101 101 103")
        self.receive_route(self.AS2, prefix, as_path="101 103")

        # prefix as seen by the route server (AS2 tried gshut but not enabled)
        self.receive_route(self.rs, prefix, as_path="1 101 101 103",
                           other_inst=self.AS1_1,
                           local_pref=100, std_comms=[])
        self.receive_route(self.rs, prefix, as_path="2 101 103",
                           other_inst=self.AS2,
                           local_pref=100, std_comms=[])

        # prefix as seen by other clients, via AS2 (still best path)
        self.receive_route(self.AS4, prefix, as_path="2 101 103",
                           next_hop=self.AS2, std_comms=[])

    def test_080_control_communities_AS1_only(self):
        """{}: control communities, announce to AS1 only"""

        self.receive_route(self.AS1_1, self.DATA["AS3_cc_AS1only"], self.rs,
                           as_path="3", next_hop=self.AS3,
                           std_comms=[], lrg_comms=[])
        self.receive_route(self.AS1_2, self.DATA["AS3_cc_AS1only"], self.rs,
                           as_path="3", next_hop=self.AS3,
                           std_comms=[], lrg_comms=[])

        for inst in (self.AS2, self.AS4):
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(inst, self.DATA["AS3_cc_AS1only"])
        self.log_contains(self.rs, "route didn't pass control communities checks - NOT ANNOUNCING {} TO {{AS2}}".format(self.DATA["AS3_cc_AS1only"]), {"AS2": self.AS2})

    def test_080_control_communities_not_AS1(self):
        """{}: control communities, announce to all except AS1"""

        for inst in (self.AS2, self.AS4):
            self.receive_route(inst, self.DATA["AS3_cc_not_AS1"], self.rs,
                               as_path="3", next_hop=self.AS3,
                               std_comms=[], lrg_comms=[])

        for inst in (self.AS1_1, self.AS1_2):
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(inst, self.DATA["AS3_cc_not_AS1"])
            self.log_contains(self.rs, "route didn't pass control communities checks - NOT ANNOUNCING {} TO {{other_inst}}".format(self.DATA["AS3_cc_not_AS1"]), {"other_inst": inst})

    def test_080_control_communities_none(self):
        """{}: control communities, don't announce to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2, self.AS4):
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(inst, self.DATA["AS3_cc_none"])
            self.log_contains(self.rs, "route didn't pass control communities checks - NOT ANNOUNCING {} TO {{other_inst}}".format(self.DATA["AS3_cc_none"]), {"other_inst": inst})

    def test_081_control_communities_prepend1any(self):
        """{}: control communities, prepend once to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2, self.AS4):
            self.receive_route(inst, self.DATA["AS3_prepend1any"], self.rs, as_path="3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_081_control_communities_prepend2any(self):
        """{}: control communities, prepend twice to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2, self.AS4):
            self.receive_route(inst, self.DATA["AS3_prepend2any"], self.rs, as_path="3 3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_081_control_communities_prepend3any(self):
        """{}: control communities, prepend thrice to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2, self.AS4):
            self.receive_route(inst, self.DATA["AS3_prepend3any"], self.rs, as_path="3 3 3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_082_control_communities_prepend1_AS1(self):
        """{}: control communities, prepend once to AS1"""

        for inst in (self.AS1_1, self.AS1_2):
            self.receive_route(inst, self.DATA["AS3_prepend1_AS1"], self.rs, as_path="3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])
        for inst in (self.AS2, self.AS4):
            self.receive_route(inst, self.DATA["AS3_prepend1_AS1"], self.rs, as_path="3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_082_control_communities_prepend2_AS2(self):
        """{}: control communities, prepend twice to AS2"""

        self.receive_route(self.AS2, self.DATA["AS3_prepend2_AS2"], self.rs, as_path="3 3 3",
                           next_hop=self.AS3, std_comms=[], lrg_comms=[])
        for inst in (self.AS1_1, self.AS1_2, self.AS4):
            self.receive_route(inst, self.DATA["AS3_prepend2_AS2"], self.rs, as_path="3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_082_control_communities_prepend3_AS1_1_others(self):
        """{}: control communities, prepend thrice to AS1, once to others"""

        for inst in (self.AS1_1, self.AS1_2):
            self.receive_route(inst, self.DATA["AS3_prep3AS1_1any"], self.rs, as_path="3 3 3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])
        for inst in (self.AS2, self.AS4):
            self.receive_route(inst, self.DATA["AS3_prep3AS1_1any"], self.rs, as_path="3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_083_control_communities_AS3_noexport_to_any(self):
        """{}: control communities, NO_EXPORT to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2, self.AS4):
            self.receive_route(inst, self.DATA["AS3_noexport_any"], self.rs,
                               as_path="3", next_hop=self.AS3,
                               std_comms=["65535:65281"],
                               lrg_comms=[], ext_comms=[])
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.AS101, self.DATA["AS3_noexport_any"])

    def test_083_control_communities_AS3_noexport_to_AS1(self):
        """{}: control communities, NO_EXPORT to AS1"""

        pref = self.DATA["AS3_noexport_AS1"]
        for inst in (self.AS1_1, self.AS1_2):
            self.receive_route(inst, pref, self.rs, as_path="3", next_hop=self.AS3,
                               std_comms=["65535:65281"],
                               lrg_comms=[], ext_comms=[])
        self.receive_route(self.AS2, pref, self.rs, as_path="3 3 3 3", next_hop=self.AS3,
                           std_comms=[],
                           lrg_comms=[], ext_comms=[])
        self.receive_route(self.AS101, pref, as_path="2 3 3 3 3")
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.AS101, pref, as_path="1 3")

    def test_083_control_communities_AS3_rfc1997_noexport(self):
        """{}: control communities, RFC1997 NO_EXPORT"""

        pref = self.DATA["AS3_rfc1997_noexp"]
        for inst in (self.AS1_1, self.AS1_2, self.AS2, self.AS4):
            self.receive_route(inst, pref, self.rs, as_path="3",
                               next_hop=self.AS3, std_comms=["65535:65281"],
                               lrg_comms=[], ext_comms=[])
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.AS101, pref)

    def _test_084_AS1_1_and_AS1_2_only(self, pref):
        for inst in (self.AS1_1, self.AS1_2):
            self.receive_route(inst, pref, self.rs, as_path="4",
                               std_comms=[], lrg_comms=[], ext_comms=[])
        for inst in (self.AS2, self.AS3):
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(inst, pref)

    def test_084_control_communities_rtt_AS4_only_peers_lt_15(self):
        """{}: control communities, RTT, only peers <= 15 ms"""
        pref = self.DATA["AS4_rtt_1"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=["0:999", "64532:15"])
        self._test_084_AS1_1_and_AS1_2_only(pref)

    def test_084_control_communities_rtt_AS4_only_peers_lt_5(self):
        """{}: control communities, RTT, only peers <= 5 ms"""
        pref = self.DATA["AS4_rtt_2"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=["0:999", "64532:5"])
        self._test_084_AS1_1_and_AS1_2_only(pref)

    def test_084_control_communities_rtt_AS4_not_peers_gt_15(self):
        """{}: control communities, RTT, not peers > 15 ms"""
        pref = self.DATA["AS4_rtt_3"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=["64531:15"])
        self._test_084_AS1_1_and_AS1_2_only(pref)

    def test_084_control_communities_rtt_AS4_not_peers_gt_5(self):
        """{}: control communities, RTT, not peers > 5 ms"""
        pref = self.DATA["AS4_rtt_4"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=["64531:5"])
        self._test_084_AS1_1_and_AS1_2_only(pref)

    def test_084_control_communities_rtt_AS4_not_peers_gt_5_but_AS3(self):
        """{}: control communities, RTT, not peers > 5 ms + AS3"""
        pref = self.DATA["AS4_rtt_5"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=["65501:3", "64531:5"])
        for inst in (self.AS1_1, self.AS1_2, self.AS3):
            self.receive_route(inst, pref, self.rs,
                               std_comms=[], lrg_comms=[], ext_comms=[])
        for inst in [self.AS2]:
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(inst, pref)

    def test_084_control_communities_rtt_AS4_not_peers_lt_5_gt_100(self):
        """{}: control communities, RTT, not peers <= 5 and > 100 ms"""
        pref = self.DATA["AS4_rtt_6"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=["64530:5", "64531:100"])
        for inst in [self.AS2]:
            self.receive_route(inst, pref, self.rs,
                               std_comms=[], lrg_comms=[], ext_comms=[])
        for inst in [self.AS1_1, self.AS1_2, self.AS3]:
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(inst, pref)

    def test_084_control_communities_rtt_AS4_blackhole_not_to_peers_gt_20(self):
        """{}: control communities, RTT, blackhole, not peers > 20 ms"""
        expected_bh_next_hop = self.DATA["blackhole_IP"]

        pref = self.DATA["AS4_rtt_7"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=["65535:666", "64531:20"])
        for inst in [self.AS1_1, self.AS2]:
            self.receive_route(inst, pref, self.rs,
                               next_hop=expected_bh_next_hop,
                               std_comms=["65535:666", "65535:65281"],
                               lrg_comms=[], ext_comms=[])
        for inst in [self.AS1_2, self.AS3]:
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(inst, pref)

    def test_085_control_communities_rtt_prep3x_gt_100_2x_gt_10(self):
        """{}: control communities, RTT, prepend 3x > 100 ms, 2x > 10 ms"""
        pref = self.DATA["AS4_rtt_8"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=["64539:100", "64538:10"])
        for inst in [self.AS1_1, self.AS1_2]:
            self.receive_route(inst, pref, self.rs, as_path="4",
                               std_comms=[], lrg_comms=[], ext_comms=[])
        self.receive_route(self.AS2, pref, self.rs, as_path="4 4 4",
                            std_comms=[], lrg_comms=[], ext_comms=[])
        self.receive_route(self.AS3, pref, self.rs, as_path="999 4 4 4 4",
                            std_comms=[], lrg_comms=[], ext_comms=[])

    def test_085_control_communities_rtt_prep3x_lt_5_2x_lt_20_1x_any(self):
        """{}: control communities, RTT, prepend 3x <= 5 ms, 2x <= 20 ms, 1x any"""
        pref = self.DATA["AS4_rtt_9"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=["64536:5", "64535:20", "65521:65521"])
        for inst in [self.AS1_1, self.AS1_2]:
            self.receive_route(inst, pref, self.rs, as_path="4 4 4 4",
                               std_comms=[], lrg_comms=[], ext_comms=[])
        self.receive_route(self.AS2, pref, self.rs, as_path="4 4 4",
                            std_comms=[], lrg_comms=[], ext_comms=[])
        self.receive_route(self.AS3, pref, self.rs, as_path="999 4 4",
                            std_comms=[], lrg_comms=[], ext_comms=[])

    def test_085_control_communities_rtt_ext_comms_prep1x_gt_10_2x_gt_20(self):
        """{}: control communities, RTT, ext comms, prepend 1x > 10 ms, 2x > 20 ms"""
        if isinstance(self.rs, BIRDInstance):
            ext_comm_rpki_unknown = ["generic:0x43000000:0x1"]
        else:
            ext_comm_rpki_unknown = []
        pref = self.DATA["AS4_rtt_10"]
        self.receive_route(self.rs, pref, self.AS4,
                           std_comms=[],
                           ext_comms=ext_comm_rpki_unknown + ["rt:64537:10",
                                                              "rt:64538:20"])
        for inst in [self.AS1_1, self.AS1_2]:
            self.receive_route(inst, pref, self.rs, as_path="4",
                               std_comms=[], lrg_comms=[], ext_comms=[])
        self.receive_route(self.AS2, pref, self.rs, as_path="4 4",
                            std_comms=[], lrg_comms=[], ext_comms=[])
        self.receive_route(self.AS3, pref, self.rs, as_path="999 4 4 4",
                            std_comms=[], lrg_comms=[], ext_comms=[])

    def test_100_prefixes_received_by_clients_AS1_1(self):
        """{}: prefixes received by clients: AS1_1"""
        self.receive_route(self.AS1_1, self.DATA["AS2_good1"], self.rs, as_path="2", next_hop=self.AS2)
        self.receive_route(self.AS1_1, self.DATA["AS2_good2"], self.rs, as_path="2", next_hop=self.AS2)
        self.receive_route(self.AS1_1, self.DATA["AS2_nonclient_nexthop1"],
                           self.rs, as_path="2",
                           next_hop=self.DATA["AS2_nonclient_nexthop1_nh"])

    def test_100_prefixes_received_by_clients_AS1_2(self):
        """{}: prefixes received by clients: AS1_2"""

        self.receive_route(self.AS1_2, self.DATA["AS2_good1"], self.rs, as_path="2", next_hop=self.AS2)
        self.receive_route(self.AS1_2, self.DATA["AS2_good2"], self.rs, as_path="2", next_hop=self.AS2)
        self.receive_route(self.AS1_2, self.DATA["AS2_nonclient_nexthop1"],
                           self.rs, as_path="2",
                           next_hop=self.DATA["AS2_nonclient_nexthop1_nh"])

    def test_100_prefixes_received_by_clients_AS2(self):
        """{}: prefixes received by clients: AS2"""

        self.receive_route(self.AS2, self.DATA["AS1_good1"], self.rs, as_path="1", next_hop=self.AS1_1)
        self.receive_route(self.AS2, self.DATA["AS1_good2"], self.rs, as_path="1", next_hop=self.AS1_1)
        self.receive_route(self.AS2, self.DATA["AS1_good3"], self.rs, as_path="1", next_hop=self.AS1_1)

    def test_100_prefixes_received_by_clients_AS3(self):
        """{}: prefixes received by clients: AS3"""

        # AS3 has prepend_rs_as, so all the prefixes received from the rs
        # have AS_PATH "999 x"

        # prefix announced by AS1_2 only but with AS1_1 next-hop
        self.receive_route(self.AS3, self.DATA["AS1_good3"], self.rs, as_path="999 1", next_hop=self.AS1_1)

        # AS3 must receive prefixes from AS2
        self.receive_route(self.AS3, self.DATA["AS2_good1"], self.rs, as_path="999 2", next_hop=self.AS2)
        self.receive_route(self.AS3, self.DATA["AS2_good2"], self.rs, as_path="999 2", next_hop=self.AS2)

        # AS3 must receive prefixes from AS1 (this test only verifies
        # that the following prefixes reach AS3, without taking into account
        # AS_PATH nor NEXT_HOP; the "_with_ADD_PATH" version of this test
        # also verifies that these prefixes are received twice by AS3)
        for pref in ("AS101_good1", "AS101_bad_std_comm", "AS101_bad_lrg_comm",
                     "AS101_other_s_comm", "AS101_other_l_comm",
                     "AS101_bad_good_comms", "AS104_arin_1", "AS104_nicbr_1"):
            self.receive_route(self.AS3, self.DATA[pref], self.rs)

        for pref in ("AS101_roa_routeobj_1", "AS101_roa_routeobj_3"):
            self.receive_route(self.AS3, self.DATA[pref], self.rs)

    def test_100_prefixes_received_by_clients_AS3_with_ADD_PATH(self):
        """{}: prefixes received by clients: AS3 (with ADD-PATH)"""

        if isinstance(self.rs, OpenBGPDInstance):
            raise unittest.SkipTest("ADD-PATH not supported by OpenBGPD")

        # AS3 has prepend_rs_as, so all the prefixes received from the rs
        # have AS_PATH "999 x"

        # AS3 must receive prefixes from both AS1_1 and AS1_2 because the
        # session on the rs is configured with ADD-PATH
        self.receive_route(self.AS3, self.DATA["AS1_good1"], self.rs, as_path="999 1", next_hop=self.AS1_1)
        self.receive_route(self.AS3, self.DATA["AS1_good1"], self.rs, as_path="999 1", next_hop=self.AS1_2)
        self.receive_route(self.AS3, self.DATA["AS1_good2"], self.rs, as_path="999 1", next_hop=self.AS1_1)
        self.receive_route(self.AS3, self.DATA["AS1_good2"], self.rs, as_path="999 1", next_hop=self.AS1_2)

        # AS101 announces its prefixes to both AS1 (AS1_1 and AS1_2 clients) and AS2.
        # AS101 prefixes received by AS1_2 are rejected by rs because of next-hop-policy failure.
        # The other prefixes should be received twice by AS3 because ADD-PATH
        # is configured for the session on the rs.
        self.receive_route(self.AS3, self.DATA["AS101_good1"], self.rs, as_path="999 1 101", next_hop=self.AS1_1)
        self.receive_route(self.AS3, self.DATA["AS101_good1"], self.rs, as_path="999 2 101", next_hop=self.AS2)

        self.receive_route(self.AS3, self.DATA["AS101_bad_std_comm"], self.rs, as_path="999 1 101", next_hop=self.AS1_1)
        self.receive_route(self.AS3, self.DATA["AS101_bad_std_comm"], self.rs, as_path="999 2 101", next_hop=self.AS2)

        self.receive_route(self.AS3, self.DATA["AS101_bad_lrg_comm"], self.rs, as_path="999 1 101", next_hop=self.AS1_1)
        self.receive_route(self.AS3, self.DATA["AS101_bad_lrg_comm"], self.rs, as_path="999 2 101", next_hop=self.AS2)

        self.receive_route(self.AS3, self.DATA["AS101_other_s_comm"], self.rs, as_path="999 1 101", next_hop=self.AS1_1, std_comms=["888:0"])
        self.receive_route(self.AS3, self.DATA["AS101_other_s_comm"], self.rs, as_path="999 2 101", next_hop=self.AS2, std_comms=["888:0"])

        self.receive_route(self.AS3, self.DATA["AS101_other_l_comm"], self.rs, as_path="999 1 101", next_hop=self.AS1_1, lrg_comms=["888:0:0"])
        self.receive_route(self.AS3, self.DATA["AS101_other_l_comm"], self.rs, as_path="999 2 101", next_hop=self.AS2, lrg_comms=["888:0:0"])

        self.receive_route(self.AS3, self.DATA["AS101_bad_good_comms"], self.rs, as_path="999 1 101", next_hop=self.AS1_1,
                           std_comms=["777:0"], lrg_comms=["777:0:0"])
        self.receive_route(self.AS3, self.DATA["AS101_bad_good_comms"], self.rs, as_path="999 2 101", next_hop=self.AS2,
                           std_comms=["777:0"], lrg_comms=["777:0:0"])

    def test_900_reconfigure(self):
        """{}: reconfigure"""
        self.rs.reload_config()
        self.test_020_sessions_up()

class BasicScenario_TagRejectPolicy(LiveScenario_TagRejectPolicy):

    def test_042_bad_prefixes_received_by_rs_bogon_wrong_tag(self):
        """{}: bad prefixes received by rs: bogon (wrong tag)"""
        with six.assertRaisesRegex(self, AssertionError, "real reasons 2, expected reason 1."):
            self.receive_route(self.rs, self.DATA["bogon1"], self.AS1_1,
                               as_path="1", next_hop=self.AS1_1,
                               filtered=True, reject_reason=1)

    def test_042_bad_prefixes_received_by_rs_global_blacklist_wrong_tag(self):
        """{}: bad prefixes received by rs: global blacklist (wrong tag)"""
        with six.assertRaisesRegex(self, AssertionError, "real reasons 3, expected reason 1."):
            self.receive_route(self.rs, self.DATA["local1"], self.AS1_1,
                               as_path="1", next_hop=self.AS1_1,
                               filtered=True, reject_reason=1)

class BasicScenario_TagAndRejectRejectPolicy(LiveScenario_TagAndRejectRejectPolicy,
                                             BasicScenario_TagRejectPolicy):
    pass

class BasicScenarioBIRD(BasicScenario):
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
                                     target_version=cls.TARGET_VERSION,
                                     local_files=["footer{}".format(ip_ver) for ip_ver in ip_vers]),
                    "/etc/bird/bird.conf"
                )
            ] + cls._get_local_file(),
        )

class BasicScenarioBIRD2(BasicScenarioBIRD):
    __test__ = False

    TARGET_VERSION = "2.0.7"

    @classmethod
    def _get_local_file_name(cls):
        return "bird2_local_file"

class BasicScenarioOpenBGPD(BasicScenario_TagRejectPolicy, BasicScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = OpenBGPDConfigBuilder
    TARGET_VERSION = None

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

class BasicScenarioOpenBGPDPrevious(BasicScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = OpenBGPDPreviousInstance.BGP_SPEAKER_VERSION

class BasicScenarioOpenBGPDLatest(BasicScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = OpenBGPDLatestInstance.BGP_SPEAKER_VERSION

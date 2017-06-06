# Copyright (C) 2017 Pier Carlo Chiodi
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

import ipaddr
import unittest

from pierky.arouteserver.builder import OpenBGPDConfigBuilder, BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario, \
                                                      LiveScenario_TagRejectPolicy
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance, \
                                                          OpenBGPD60Instance
from pierky.arouteserver.tests.live_tests.bird import BIRDInstance

class BasicScenario(LiveScenario):
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

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1_1)
        self.session_is_up(self.rs, self.AS1_2)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS3)
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
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS1_good1"], self.AS2)
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS1_good2"], self.AS2)
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS2_good1"], self.AS1_1)
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.rs, self.DATA["AS2_good2"], self.AS1_1)

        # AS_PATH should match the expectations
        self.receive_route(self.rs, self.DATA["AS1_good1"], self.AS1_1, as_path="1")
        self.receive_route(self.rs, self.DATA["AS2_good1"], self.AS2, as_path="2")

        # NEXT_HOP should match the expectations
        self.receive_route(self.rs, self.DATA["AS1_good1"], self.AS1_1, as_path="1", next_hop=self.AS1_1)
        self.receive_route(self.rs, self.DATA["AS2_good1"], self.AS2, as_path="2", next_hop=self.AS2)

    def test_030_good_prefixes_received_by_rs_nonclient_nexthop(self):
        """{}: good prefixes received by rs: non-client NEXT_HOP"""

        self.receive_route(self.rs, self.DATA["AS2_nonclient_nexthop1"],
                           as_path="2",
                           next_hop=self.DATA["AS2_nonclient_nexthop1_nh"])

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

        ip_ver = ipaddr.IPNetwork(self.DATA["pref_len1"]).version

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
        if ipaddr.IPNetwork(self.DATA["Default_route"]).version == 4:
            msg = "prefix is bogon - REJECTING " + self.DATA["Default_route"]
        else:
            msg = "prefix is not in IPv6 Global Unicast space - REJECTING " + self.DATA["Default_route"]
        self.log_contains(self.rs, msg)

    def test_041_bad_prefixes_not_received_by_clients(self):
        """{}: bad prefixes not received by clients"""
        for prefix in (self.DATA["bogon1"],
                       self.DATA["local1"],
                       self.DATA["pref_len1"],
                       self.DATA["peer_as1"],
                       self.DATA["invalid_asn1"],
                       self.DATA["aspath_len1"],
                       self.DATA["AS2_nonclient_nexthop2"]):
            for inst in (self.AS2, self.AS3):
                with self.assertRaisesRegexp(AssertionError, "Routes not found."):
                    self.receive_route(inst, prefix)

        # Among the clients, only AS3 is expected to not see the 
        # following prefixes because AS1 and AS2
        # receive them on their session with AS101
        for prefix in (self.DATA["AS101_no_rset"],
                       self.DATA["AS102_no_asset"]):
            with self.assertRaisesRegexp(AssertionError, "Routes not found."):
                self.receive_route(self.AS3, prefix)

    def test_045_rpki_valid_prefix(self):
        """{}: RPKI, valid prefix received by rs"""
        if isinstance(self.rs, OpenBGPDInstance):
            raise unittest.SkipTest("RPKI not supported by OpenBGPD")

        self.receive_route(self.rs, self.DATA["AS101_roa_valid1"], self.AS1_1,
                           as_path="1 101")
        self.receive_route(self.rs, self.DATA["AS101_roa_valid1"], self.AS2,
                           as_path="2 101")

    def test_045_rpki_invalid_prefix_asn(self):
        """{}: RPKI, invalid prefix (bad ASN) received by rs"""
        if isinstance(self.rs, OpenBGPDInstance):
            raise unittest.SkipTest("RPKI not supported by OpenBGPD")

        self.receive_route(self.rs, self.DATA["AS101_roa_invalid1"], self.AS1_1,
                           as_path="1 101", filtered=True,
                           ext_comms=["generic:0x43000000:0x2"])
        self.receive_route(self.rs, self.DATA["AS101_roa_invalid1"], self.AS2,
                           as_path="2 101", filtered=True,
                           ext_comms=["generic:0x43000000:0x2"])

    def test_045_rpki_invalid_prefix_length(self):
        """{}: RPKI, invalid prefix (bad length) received by rs"""
        if isinstance(self.rs, OpenBGPDInstance):
            raise unittest.SkipTest("RPKI not supported by OpenBGPD")

        self.receive_route(self.rs, self.DATA["AS101_roa_badlen"], self.AS1_1,
                           as_path="1 101", filtered=True,
                           ext_comms=["generic:0x43000000:0x2"])
        self.receive_route(self.rs, self.DATA["AS101_roa_badlen"], self.AS2,
                           as_path="2 101", filtered=True,
                           ext_comms=["generic:0x43000000:0x2"])

    def test_045_rpki_valid_prefix_propagated_to_clients(self):
        """{}: RPKI, valid prefix propagated to clients"""
        if isinstance(self.rs, OpenBGPDInstance):
            raise unittest.SkipTest("RPKI not supported by OpenBGPD")

        self.receive_route(self.AS3, self.DATA["AS101_roa_valid1"], self.rs)

    def test_045_rpki_invalid_prefixes_not_propagated_to_clients(self):
        """{}: RPKI, invalid prefix (bad ASN) not propagated to clients"""
        if isinstance(self.rs, OpenBGPDInstance):
            raise unittest.SkipTest("RPKI not supported by OpenBGPD")

        for pref_id in ("AS101_roa_invalid1", "AS101_roa_badlen"):
            with self.assertRaisesRegexp(AssertionError, "Routes not found."):
                self.receive_route(self.AS3, self.DATA[pref_id])

    def test_045_blackhole_with_roa(self):
        """{}: RPKI, blackhole request for a covered prefix"""
        if isinstance(self.rs, OpenBGPDInstance):
            raise unittest.SkipTest("RPKI not supported by OpenBGPD")

        self.receive_route(self.rs, self.DATA["AS101_roa_blackhole"], self.AS1_1, as_path="1 101",
                           std_comms=["65535:666"], lrg_comms=[])
        self.receive_route(self.rs, self.DATA["AS101_roa_blackhole"], self.AS2, as_path="2 101",
                           std_comms=["65535:666"], lrg_comms=[])
        for inst in (self.AS1_1, self.AS2):
            self.log_contains(self.rs, "blackhole filtering request from {{inst}} - ACCEPTING {}".format(
                self.DATA["AS101_roa_blackhole"]), {"inst": inst})
        self.receive_route(self.AS3, self.DATA["AS101_roa_blackhole"], self.rs,
                           next_hop=self.DATA["blackhole_IP"],
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
        if isinstance(self.rs, OpenBGPD60Instance):
            raise unittest.SkipTest("Large comms not supported by OpenBGPD 6.0")

        self.receive_route(self.rs, self.DATA["AS101_bad_lrg_comm"], self.AS1_1, lrg_comms=[])
        self.receive_route(self.rs, self.DATA["AS101_bad_lrg_comm"], self.AS2, lrg_comms=[])

    def test_062_other_communities_not_scrubbed_by_rs_std(self):
        """{}: other communities not scrubbed by rs (std)"""

        for inst in (self.AS1_1, self.AS2):
            self.receive_route(self.rs, self.DATA["AS101_other_s_comm"], inst, std_comms=["888:0"])
            self.receive_route(self.rs, self.DATA["AS101_bad_good_comms"], inst, std_comms=["777:0"])

    def test_062_other_communities_not_scrubbed_by_rs_lrg(self):
        """{}: other communities not scrubbed by rs (lrg)"""
        if isinstance(self.rs, OpenBGPD60Instance):
            raise unittest.SkipTest("Large comms not supported by OpenBGPD 6.0")

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
                           std_comms=["65534:0"], lrg_comms=[])
        self.log_contains(self.rs, "blackhole filtering request from {AS2_1} - ACCEPTING " + self.DATA["AS2_blackhole2"], {"AS2_1": self.AS2})

    def test_070_blackhole_filtering_as_seen_by_rs_lrg_cust(self):
        """{}: blackhole filtering requests as seen by rs (lrg cust)"""
        if isinstance(self.rs, OpenBGPD60Instance):
            raise unittest.SkipTest("Large comms not supported by OpenBGPD 6.0")

        self.receive_route(self.rs, self.DATA["AS2_blackhole3"], self.AS2, next_hop=self.AS2, as_path="2",
                           std_comms=[], lrg_comms=["65534:0:0"])
        self.log_contains(self.rs, "blackhole filtering request from {AS2_1} - ACCEPTING " + self.DATA["AS2_blackhole3"], {"AS2_1": self.AS2})

    def test_071_blackholed_prefixes_as_seen_by_enabled_clients_BLACKHOLE(self):
        """{}: blackholed prefixes as seen by enabled clients (BLACKHOLE)"""
        if isinstance(self.rs, OpenBGPD60Instance) and ":" in self.DATA["AS2_blackhole1"]:
            # OpenBGPD < 6.1 bug: https://github.com/pierky/arouteserver/issues/3
            # fixed by https://github.com/openbsd/src/commit/f1385c8f4f9b9e193ff65d9f2039862d3e230a45
            raise unittest.SkipTest("Not working on OpenBGPD 6.0")

        for inst in (self.AS1_1, self.AS3):
            self.receive_route(inst, self.DATA["AS2_blackhole1"], self.rs, next_hop=self.DATA["blackhole_IP"],
                               std_comms=["65535:666", "65535:65281"], lrg_comms=[])

    def test_071_blackholed_prefixes_as_seen_by_enabled_clients_std_cust(self):
        """{}: blackholed prefixes as seen by enabled clients (std_cust)"""
        if isinstance(self.rs, OpenBGPD60Instance) and ":" in self.DATA["AS2_blackhole1"]:
            # OpenBGPD < 6.1 bug: https://github.com/pierky/arouteserver/issues/3
            # fixed by https://github.com/openbsd/src/commit/f1385c8f4f9b9e193ff65d9f2039862d3e230a45
            raise unittest.SkipTest("Not working on OpenBGPD 6.0")

        for inst in (self.AS1_1, self.AS3):
            self.receive_route(inst, self.DATA["AS2_blackhole2"], self.rs, next_hop=self.DATA["blackhole_IP"],
                               std_comms=["65535:666", "65535:65281"], lrg_comms=[])

    def test_071_blackholed_prefixes_as_seen_by_enabled_clients_lrg_cust(self):
        """{}: blackholed prefixes as seen by enabled clients (lrg_cust)"""
        if isinstance(self.rs, OpenBGPD60Instance):
            raise unittest.SkipTest("Large comms not supported by OpenBGPD 6.0")

        for inst in (self.AS1_1, self.AS3):
            self.receive_route(inst, self.DATA["AS2_blackhole3"], self.rs, next_hop=self.DATA["blackhole_IP"],
                               std_comms=["65535:666", "65535:65281"], lrg_comms=[])

    def test_071_blackholed_prefixes_triggered_via_unsupported_lrg_comms(self):
        """{}: blackholed prefixes triggered via unsupported lrg comms"""
        if not isinstance(self.rs, OpenBGPD60Instance):
            # Test valid only for BGP daemons that don't support large comms
            raise unittest.SkipTest("Large comms are supported here")

        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS1_1, self.DATA["AS2_blackhole3"])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS3, self.DATA["AS2_blackhole3"])

    def test_071_blackholed_prefixes_not_seen_by_not_enabled_clients(self):
        """{}: blackholed prefixes not seen by not enabled clients"""

        # AS1_2 not enabled to receive blackholed prefixes
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS1_2, self.DATA["AS2_blackhole1"])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS1_2, self.DATA["AS2_blackhole2"])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS1_2, self.DATA["AS2_blackhole3"])
        self.log_contains(self.rs, "client {{AS1_2}} not enabled to receive blackhole prefixes - NOT ANNOUNCING {pref} TO {{AS1_2}}".format(pref=self.DATA["AS2_blackhole1"]), {"AS1_2": self.AS1_2})
        self.log_contains(self.rs, "client {{AS1_2}} not enabled to receive blackhole prefixes - NOT ANNOUNCING {pref} TO {{AS1_2}}".format(pref=self.DATA["AS2_blackhole2"]), {"AS1_2": self.AS1_2})
        self.log_contains(self.rs, "client {{AS1_2}} not enabled to receive blackhole prefixes - NOT ANNOUNCING {pref} TO {{AS1_2}}".format(pref=self.DATA["AS2_blackhole3"]), {"AS1_2": self.AS1_2})

    def test_080_control_communities_AS1_only(self):
        """{}: control communities, announce to AS1 only"""

        self.receive_route(self.AS1_1, self.DATA["AS3_cc_AS1only"], self.rs,
                           as_path="3", next_hop=self.AS3,
                           std_comms=[], lrg_comms=[])
        self.receive_route(self.AS1_2, self.DATA["AS3_cc_AS1only"], self.rs,
                           as_path="3", next_hop=self.AS3,
                           std_comms=[], lrg_comms=[])

        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS2, self.DATA["AS3_cc_AS1only"])
        self.log_contains(self.rs, "route didn't pass control communities checks - NOT ANNOUNCING {} TO {{AS2}}".format(self.DATA["AS3_cc_AS1only"]), {"AS2": self.AS2})

    def test_080_control_communities_not_AS1(self):
        """{}: control communities, announce to all except AS1"""

        self.receive_route(self.AS2, self.DATA["AS3_cc_not_AS1"], self.rs,
                           as_path="3", next_hop=self.AS3,
                           std_comms=[], lrg_comms=[])

        for inst in (self.AS1_1, self.AS1_2):
            with self.assertRaisesRegexp(AssertionError, "Routes not found."):
                self.receive_route(inst, self.DATA["AS3_cc_not_AS1"])
            self.log_contains(self.rs, "route didn't pass control communities checks - NOT ANNOUNCING {} TO {{other_inst}}".format(self.DATA["AS3_cc_not_AS1"]), {"other_inst": inst})

    def test_080_control_communities_none(self):
        """{}: control communities, don't announce to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2):
            with self.assertRaisesRegexp(AssertionError, "Routes not found."):
                self.receive_route(inst, self.DATA["AS3_cc_none"])
            self.log_contains(self.rs, "route didn't pass control communities checks - NOT ANNOUNCING {} TO {{other_inst}}".format(self.DATA["AS3_cc_none"]), {"other_inst": inst})

    def test_081_control_communities_prepend1any(self):
        """{}: control communities, prepend once to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2):
            self.receive_route(inst, self.DATA["AS3_prepend1any"], self.rs, as_path="3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_081_control_communities_prepend2any(self):
        """{}: control communities, prepend twice to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2):
            self.receive_route(inst, self.DATA["AS3_prepend2any"], self.rs, as_path="3 3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_081_control_communities_prepend3any(self):
        """{}: control communities, prepend thrice to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2):
            self.receive_route(inst, self.DATA["AS3_prepend3any"], self.rs, as_path="3 3 3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_082_control_communities_prepend1_AS1(self):
        """{}: control communities, prepend once to AS1"""

        for inst in (self.AS1_1, self.AS1_2):
            self.receive_route(inst, self.DATA["AS3_prepend1_AS1"], self.rs, as_path="3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])
        self.receive_route(self.AS2, self.DATA["AS3_prepend1_AS1"], self.rs, as_path="3",
                           next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_082_control_communities_prepend2_AS2(self):
        """{}: control communities, prepend twice to AS2"""

        self.receive_route(self.AS2, self.DATA["AS3_prepend2_AS2"], self.rs, as_path="3 3 3",
                           next_hop=self.AS3, std_comms=[], lrg_comms=[])
        for inst in (self.AS1_1, self.AS1_2):
            self.receive_route(inst, self.DATA["AS3_prepend2_AS2"], self.rs, as_path="3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_082_control_communities_prepend3_AS1_1_others(self):
        """{}: control communities, prepend thrice to AS1, once to others"""

        for inst in (self.AS1_1, self.AS1_2):
            self.receive_route(inst, self.DATA["AS3_prep3AS1_1any"], self.rs, as_path="3 3 3 3",
                               next_hop=self.AS3, std_comms=[], lrg_comms=[])
        self.receive_route(self.AS2, self.DATA["AS3_prep3AS1_1any"], self.rs, as_path="3 3",
                           next_hop=self.AS3, std_comms=[], lrg_comms=[])

    def test_083_control_communities_AS3_noexport_to_any(self):
        """{}: control communities, NO_EXPORT to any"""

        for inst in (self.AS1_1, self.AS1_2, self.AS2):
            self.receive_route(inst, self.DATA["AS3_noexport_any"], self.rs,
                               as_path="3", next_hop=self.AS3,
                               std_comms=["65535:65281"],
                               lrg_comms=[], ext_comms=[])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
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
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS101, pref, as_path="1 3")

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
                     "AS101_bad_good_comms"):
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

class BasicScenario_TagRejectPolicy(LiveScenario_TagRejectPolicy):

    def test_042_bad_prefixes_received_by_rs_bogon_wrong_tag(self):
        """{}: bad prefixes received by rs: bogon (wrong tag)"""
        with self.assertRaisesRegexp(AssertionError, "real reasons 2, expected reason 1."):
            self.receive_route(self.rs, self.DATA["bogon1"], self.AS1_1,
                               as_path="1", next_hop=self.AS1_1,
                               filtered=True, reject_reason=1)

    def test_042_bad_prefixes_received_by_rs_global_blacklist_wrong_tag(self):
        """{}: bad prefixes received by rs: global blacklist (wrong tag)"""
        with self.assertRaisesRegexp(AssertionError, "real reasons 3, expected reason 1."):
            self.receive_route(self.rs, self.DATA["local1"], self.AS1_1,
                               as_path="1", next_hop=self.AS1_1,
                               filtered=True, reject_reason=1)

class BasicScenarioBIRD(BasicScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER,
                                        cfg_roas="roas{}.yml".format(cls.IP_VER),
                                        local_files=["footer{}".format(cls.IP_VER)]),
                    "/etc/bird/bird.conf"
                ),
                (
                    cls.use_static_file("bird_local_file.local{}".format(cls.IP_VER)),
                    "/etc/bird/footer{}.local".format(cls.IP_VER)
                )
            ],
        )

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

class BasicScenarioOpenBGPD60(BasicScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = "6.0"

class BasicScenarioOpenBGPD61(BasicScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = "6.1"

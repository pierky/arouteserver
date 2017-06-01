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

from pierky.arouteserver.builder import OpenBGPDConfigBuilder, BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario, \
                                                      LiveScenario_TagRejectPolicy
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPD60Instance
from pierky.arouteserver.tests.live_tests.bird import BIRDInstance

class TagASSetScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    CONFIG_BUILDER_CLASS = None

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
                "AS5",
                cls.DATA["AS5_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS5.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
        ]

    def set_instance_variables(self):
        self.rs = self._get_instance_by_name("rs")
        self.AS1 = self._get_instance_by_name("AS1")
        self.AS2 = self._get_instance_by_name("AS2")
        self.AS4 = self._get_instance_by_name("AS4")
        self.AS5 = self._get_instance_by_name("AS5")
        
    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS4)
        self.session_is_up(self.rs, self.AS5)

class TagASSetScenario_WithAS_SETs(object):

    AS_SET = {
        "AS1": [1],
        "AS-AS2": [2],
        "AS-AS4": [4],
        "AS-AS5": [5],
    }
    R_SET = {
        "AS1": [
            "AS1_allowed_prefixes"
        ],
        "AS-AS2": [
            "AS2_allowed_prefixes"
        ],
        "AS-AS4": [
            "AS4_allowed_prefixes"
        ],
        "AS-AS5": [
            "AS5_allowed_prefixes"
        ]
    }

    def _set_lrg_comms(self, lst):
        if isinstance(self.rs, OpenBGPD60Instance):
            return []
        return lst

    def test_030_AS2_prefix_ok_origin_ok(self):
        """{}: AS2 prefix ok origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS2_pref_ok_origin_ok1"], self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64514"],
                           lrg_comms=lrg_comms)

    def test_030_AS2_prefix_ko_origin_ok(self):
        """{}: AS2 prefix ko origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS2_pref_ko_origin_ok1"], self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64514"],
                           lrg_comms=lrg_comms)

    def test_030_AS2_prefix_ok_origin_ko(self):
        """{}: AS2 prefix ok origin ko"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS3_pref_ok_origin_ko1"], self.AS2, as_path="2 3", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64515"],
                           lrg_comms=lrg_comms)

    def test_030_AS2_prefix_ko_origin_ko(self):
        """{}: AS2 prefix ko origin ko"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS3_pref_ko_origin_ko1"], self.AS2, as_path="2 3", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64515"],
                           lrg_comms=lrg_comms)

    def test_040_AS4_prefix_ok_origin_ok(self):
        """{}: AS4 prefix ok origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS4_pref_ok_origin_ok1"], self.AS4, as_path="4", next_hop=self.AS4,
                           std_comms=["999:64512", "999:64514"],
                           lrg_comms=lrg_comms)

    def test_040_AS4_prefix_ko_origin_ok(self):
        """{}: AS4 prefix ko origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS4_pref_ko_origin_ok1"], self.AS4, as_path="4", next_hop=self.AS4,
                           std_comms=["999:64513", "999:64514"],
                           lrg_comms=lrg_comms)

    def test_040_AS4_origin_filtered(self):
        """{}: AS4 route filtered (origin ko)"""
        self.receive_route(self.rs, self.DATA["AS3_pref_ok_origin_ko2"],
                           self.AS4, as_path="4 3", next_hop=self.AS4,
                           filtered=True, reject_reason=9)

    def test_040_AS4_prefix_origin_filtered(self):
        """{}: AS4 route filtered (prefix ko, origin ko)"""
        self.receive_route(self.rs, self.DATA["AS3_pref_ko_origin_ko1"],
                           self.AS4, as_path="4 3", next_hop=self.AS4,
                           filtered=True, reject_reason=9)

    def test_050_AS5_prefix_ok_origin_ok(self):
        """{}: AS5 prefix ok origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS5_pref_ok_origin_ok1"], self.AS5, as_path="5", next_hop=self.AS5,
                           std_comms=["999:64512", "999:64514"],
                           lrg_comms=lrg_comms)

    def test_050_AS5_prefix_filtered(self):
        """{}: AS5 route filtered (prefix ko)"""
        self.receive_route(self.rs, self.DATA["AS5_pref_ko_origin_ok1"],
                           self.AS5, as_path="5", next_hop=self.AS5,
                           filtered=True, reject_reason=12)

    def test_050_AS5_prefix_ok_origin_ko(self):
        """{}: AS5 prefix ok origin ko"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS3_pref_ok_origin_ko3"], self.AS5, as_path="5 3", next_hop=self.AS5,
                           std_comms=["999:64512", "999:64515"],
                           lrg_comms=lrg_comms)

    def test_050_AS5_origin_filtered(self):
        """{}: AS5 route filtered (prefix ko, origin ko)"""
        # AS5 is configured with prefix enforcement only, that's why
        # the reject reason should be 12 (prefix not in IRRDBs) and
        # not 9 (origin ASN not in IRRDBs).
        self.receive_route(self.rs, self.DATA["AS3_pref_ko_origin_ko1"],
                           self.AS5, as_path="5 3", next_hop=self.AS5,
                           filtered=True, reject_reason=12)

class TagASSetScenario_EmptyAS_SETs(object):

    AS_SET = {
        "AS1": [],
        "AS-AS2": [],
        "AS-AS4": [],
        "AS-AS5": [],
    }
    R_SET = {
        "AS1": [
        ],
        "AS-AS2": [
        ],
        "AS-AS4": [
        ],
        "AS-AS5": [
        ]
    }

    def _set_lrg_comms(self, lst):
        if isinstance(self.rs, OpenBGPD60Instance):
            return []
        return lst

    def test_030_AS2_no_enforcement(self):
        """{}: AS2 no enforcement, prefix and origin not in AS-SET"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515"])
        for pref in (self.DATA["AS2_pref_ok_origin_ok1"],
                     self.DATA["AS2_pref_ko_origin_ok1"],
                     self.DATA["AS3_pref_ok_origin_ko1"],
                     self.DATA["AS3_pref_ko_origin_ko1"]):
            self.receive_route(self.rs, pref, self.AS2, next_hop=self.AS2,
                            std_comms=["999:64513", "999:64515"],
                            lrg_comms=lrg_comms)

    def test_040_AS4_origin_enforcement(self):
        """{}: AS4 origin enforcement"""
        for pref in (self.DATA["AS4_pref_ok_origin_ok1"],
                     self.DATA["AS4_pref_ko_origin_ok1"],
                     self.DATA["AS3_pref_ok_origin_ko2"],
                     self.DATA["AS3_pref_ko_origin_ko1"]):
            self.receive_route(self.rs, pref, self.AS4, next_hop=self.AS4,
                               filtered=True, reject_reason=(9, 12))

    def test_050_AS4_prefix_enforcement(self):
        """{}: AS4 prefix enforcement"""
        for pref in (self.DATA["AS5_pref_ok_origin_ok1"],
                     self.DATA["AS5_pref_ko_origin_ok1"],
                     self.DATA["AS3_pref_ok_origin_ko3"],
                     self.DATA["AS3_pref_ko_origin_ko1"]):
            self.receive_route(self.rs, pref, self.AS5, next_hop=self.AS5,
                               filtered=True, reject_reason=(9, 12))

class TagASSetScenarioBIRD(TagASSetScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER),
                    "/etc/bird/bird.conf"
                )
            ]
        )

class TagASSetScenarioOpenBGPD(LiveScenario_TagRejectPolicy, TagASSetScenario):
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
                                     target_version=cls.TARGET_VERSION),
                    "/etc/bgpd.conf"
                )
            ]
        )

class TagASSetScenarioOpenBGPD60(TagASSetScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = "6.0"

class TagASSetScenarioOpenBGPD61(TagASSetScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = "6.1"

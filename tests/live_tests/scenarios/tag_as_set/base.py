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

from pierky.arouteserver.builder import OpenBGPDConfigBuilder, BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario, \
                                                      LiveScenario_TagRejectPolicy
from pierky.arouteserver.tests.live_tests.bird import BIRDInstance
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance, \
                                                          OpenBGPDPreviousInstance, \
                                                          OpenBGPDLatestInstance

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
            cls.CLIENT_INSTANCE_CLASS(
                "AS6",
                cls.DATA["AS6_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS6.j2"),
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
        self.AS6 = self._get_instance_by_name("AS6")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS4)
        self.session_is_up(self.rs, self.AS5)
        self.session_is_up(self.rs, self.AS6)

    def test_060_AS2_whitelist_wl_wl(self):
        """{}: AS2 white list, prefix WL, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS2_pref_wl_origin_wl"],
                           self.AS2, as_path="2 21", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS2_whitelist_wl_ko(self):
        """{}: AS2 white list, prefix WL, origin ko"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS2_pref_wl_origin_ko"],
                           self.AS2, as_path="2 3", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS2_whitelist_ko_wl(self):
        """{}: AS2 white list, prefix ko, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS2_pref_ko_origin_wl"],
                           self.AS2, as_path="2 21", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS4_whitelist_wl_wl(self):
        """{}: AS4 white list, prefix WL, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS4_pref_wl_origin_wl"],
                           self.AS4, as_path="4 41", next_hop=self.AS4,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS4_whitelist_ko_wl(self):
        """{}: AS4 white list, prefix ko, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS4_pref_ko_origin_wl"],
                           self.AS4, as_path="4 41", next_hop=self.AS4,
                           std_comms=["999:64513", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS4_whitelist_wl_ko(self):
        """{}: AS4 white list, prefix WL, origin ko"""
        self.receive_route(self.rs, self.DATA["AS4_pref_wl_origin_ko"],
                           self.AS4, as_path="4 3", next_hop=self.AS4,
                           ext_comms=[],
                           filtered=True)

    def test_060_AS4_route_whitelist_1(self):
        """{}: AS4 route white list, ok (exact)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515", "999:0:64517"])
        self.receive_route(self.rs, self.DATA["AS4_routewl_1"],
                           self.AS4, as_path="4 44", next_hop=self.AS4,
                           std_comms=["999:64513", "999:64515", "999:64517"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS4_route_whitelist_2(self):
        """{}: AS4 route white list, reject (more spec)"""
        self.receive_route(self.rs, self.DATA["AS4_routewl_2"],
                           self.AS4, as_path="4 44", next_hop=self.AS4,
                           ext_comms=[],
                           filtered=True)

    def test_060_AS4_route_whitelist_3(self):
        """{}: AS4 route white list, ok (more spec)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515", "999:0:64517"])
        self.receive_route(self.rs, self.DATA["AS4_routewl_3"],
                           self.AS4, as_path="4 43", next_hop=self.AS4,
                           std_comms=["999:64513", "999:64515", "999:64517"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS4_route_whitelist_4(self):
        """{}: AS4 route white list, reject (origin KO)"""
        self.receive_route(self.rs, self.DATA["AS4_routewl_4"],
                           self.AS4, as_path="4 45", next_hop=self.AS4,
                           ext_comms=[],
                           filtered=True)

    def test_060_AS4_route_whitelist_5(self):
        """{}: AS4 route white list, ok (origin any)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515", "999:0:64517"])
        self.receive_route(self.rs, self.DATA["AS4_routewl_5"],
                           self.AS4, as_path="4 45", next_hop=self.AS4,
                           std_comms=["999:64513", "999:64515", "999:64517"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS5_whitelist_wl_ko(self):
        """{}: AS5 white list, prefix WL, origin ko"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS5_pref_wl_origin_ko"],
                           self.AS5, as_path="5 3", next_hop=self.AS5,
                           std_comms=["999:64512", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS5_whitelist_wl_wl(self):
        """{}: AS5 white list, prefix WL, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS5_pref_wl_origin_wl"],
                           self.AS5, as_path="5 51", next_hop=self.AS5,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS5_whitelist_ko_wl(self):
        """{}: AS5 white list, prefix ko, origin WL"""
        self.receive_route(self.rs, self.DATA["AS5_pref_ko_origin_wl"],
                           self.AS5, as_path="5 51", next_hop=self.AS5,
                           ext_comms=[],
                           filtered=True)

    def test_070_AS6_roas_as_route_objects_1(self):
        """{}: AS6 RPKI ROAs as route objects: invalid origin ASN"""
        self.receive_route(self.rs, self.DATA["AS2_roa1"],
                           self.AS6, as_path="6 2", next_hop=self.AS6,
                           ext_comms=[],
                           filtered=True, reject_reason=9)

    def test_900_reconfigure(self):
        """{}: reconfigure"""
        self.rs.reload_config()
        self.test_020_sessions_up()

class TagASSetScenario_WithAS_SETs(object):

    AS_SET = {
        "AS1": [1],
        "AS-AS2": [2],
        "AS-AS4": [4],
        "AS-AS5_FROM_PDB": [5],
        "AS6": [6, 3]
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
        "AS-AS5_FROM_PDB": [
            "AS5_allowed_prefixes"
        ],
        "AS6": [
            "AS6_allowed_prefixes"
        ]
    }

    def _set_lrg_comms(self, lst):
        return lst

    def test_030_AS2_prefix_ok_origin_ok(self):
        """{}: AS2 prefix ok origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS2_pref_ok_origin_ok1"], self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_030_AS2_prefix_ko_origin_ok(self):
        """{}: AS2 prefix ko origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS2_pref_ko_origin_ok1"], self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_030_AS2_prefix_ok_origin_ko(self):
        """{}: AS2 prefix ok origin ko"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS3_pref_ok_origin_ko1"], self.AS2, as_path="2 3", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_030_AS2_prefix_ko_origin_ko(self):
        """{}: AS2 prefix ko origin ko"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS3_pref_ko_origin_ko1"], self.AS2, as_path="2 3", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_040_AS4_prefix_ok_origin_ok(self):
        """{}: AS4 prefix ok origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS4_pref_ok_origin_ok1"], self.AS4, as_path="4", next_hop=self.AS4,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_040_AS4_prefix_ko_origin_ok(self):
        """{}: AS4 prefix ko origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS4_pref_ko_origin_ok1"], self.AS4, as_path="4", next_hop=self.AS4,
                           std_comms=["999:64513", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_040_AS4_origin_filtered(self):
        """{}: AS4 route filtered (origin ko)"""
        self.receive_route(self.rs, self.DATA["AS3_pref_ok_origin_ko2"],
                           self.AS4, as_path="4 3", next_hop=self.AS4,
                           ext_comms=[],
                           filtered=True, reject_reason=9)

    def test_040_AS4_prefix_origin_filtered(self):
        """{}: AS4 route filtered (prefix ko, origin ko)"""
        self.receive_route(self.rs, self.DATA["AS3_pref_ko_origin_ko1"],
                           self.AS4, as_path="4 3", next_hop=self.AS4,
                           ext_comms=[],
                           filtered=True, reject_reason=9)

    def test_050_AS5_prefix_ok_origin_ok(self):
        """{}: AS5 prefix ok origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS5_pref_ok_origin_ok1"], self.AS5, as_path="5", next_hop=self.AS5,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_050_AS5_prefix_filtered(self):
        """{}: AS5 route filtered (prefix ko)"""
        self.receive_route(self.rs, self.DATA["AS5_pref_ko_origin_ok1"],
                           self.AS5, as_path="5", next_hop=self.AS5,
                           ext_comms=[],
                           filtered=True, reject_reason=12)

    def test_050_AS5_prefix_ok_origin_ko(self):
        """{}: AS5 prefix ok origin ko"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS3_pref_ok_origin_ko3"], self.AS5, as_path="5 3", next_hop=self.AS5,
                           std_comms=["999:64512", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_050_AS5_origin_filtered(self):
        """{}: AS5 route filtered (prefix ko, origin ko)"""
        # AS5 is configured with prefix enforcement only, that's why
        # the reject reason should be 12 (prefix not in IRRDBs) and
        # not 9 (origin ASN not in IRRDBs).
        self.receive_route(self.rs, self.DATA["AS3_pref_ko_origin_ko1"],
                           self.AS5, as_path="5 3", next_hop=self.AS5,
                           ext_comms=[],
                           filtered=True, reject_reason=12)

    def test_060_AS2_whitelist_wl_ok(self):
        """{}: AS2 white list, prefix WL, origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS2_pref_wl_origin_ok"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS2_whitelist_ok_wl(self):
        """{}: AS2 white list, prefix ok, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS2_pref_ok_origin_wl"],
                           self.AS2, as_path="2 21", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS4_whitelist_wl_ok(self):
        """{}: AS4 white list, prefix WL, origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS4_pref_wl_origin_ok"],
                           self.AS4, as_path="4", next_hop=self.AS4,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS4_whitelist_ok_wl(self):
        """{}: AS4 white list, prefix ok, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS4_pref_ok_origin_wl"],
                           self.AS4, as_path="4 41", next_hop=self.AS4,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS5_whitelist_wl_ok(self):
        """{}: AS5 white list, prefix WL, origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS5_pref_wl_origin_ok"],
                           self.AS5, as_path="5", next_hop=self.AS5,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS5_whitelist_ok_wl(self):
        """{}: AS5 white list, prefix ok, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS5_pref_ok_origin_wl"],
                           self.AS5, as_path="5 51", next_hop=self.AS5,
                           std_comms=["999:64512", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_070_AS6_roas_as_route_objects_2(self):
        """{}: AS6 RPKI ROAs as route objects: ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514", "999:0:64516"])
        self.receive_route(self.rs, self.DATA["AS3_roa2"],
                           self.AS6, as_path="6 3", next_hop=self.AS6,
                           std_comms=["999:64513", "999:64514", "999:64516"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_070_AS2_roas_as_route_objects_tag_only(self):
        """{}: AS2 RPKI ROAs as route objects: tag only (w/ prefix_validated_via_rpki_roas)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514", "999:0:64516"])
        self.receive_route(self.rs, self.DATA["AS2_roa2"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64514", "999:64516"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_080_AS6_arin_whois_db_1(self):
        """{}: AS6 ARIN Whois DB: ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514", "999:0:64518"])
        self.receive_route(self.rs, self.DATA["AS3_arin1"],
                           self.AS6, as_path="6 3", next_hop=self.AS6,
                           std_comms=["999:64513", "999:64514", "999:64518"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_080_AS2_arin_whois_db_tag_only(self):
        """{}: AS2 ARIN Whois DB: tag only (w/ prefix_validated_via_arin_whois_db_dump)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514", "999:0:64518"])
        self.receive_route(self.rs, self.DATA["AS2_arin1"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64514", "999:64518"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_090_AS2_roa_and_arin_tag_only(self):
        """{}: AS2 ROA + ARIN Whois DB: tag only (w/ comms [arin_whois_db_dump, rpki_roas])"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514", "999:0:64516", "999:0:64518"])
        self.receive_route(self.rs, self.DATA["AS2_roa3_arin2"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64514", "999:64516", "999:64518"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_090_AS6_roa_and_arin_enforced(self):
        """{}: AS6 ROA + ARIN Whois DB: enforce (w/ comms [arin_whois_db_dump, rpki_roas])"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514", "999:0:64516", "999:0:64518"])
        self.receive_route(self.rs, self.DATA["AS3_roa3_arin2"],
                           self.AS6, as_path="6 3", next_hop=self.AS6,
                           std_comms=["999:64513", "999:64514", "999:64516", "999:64518"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_090_AS2_pref_ok_orig_ok_roa_tag_only(self):
        """{}: AS2 prefix ok, origin ok, ROA: tag only (w/ prefix_validated_via_rpki_roas)"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514", "999:0:64516"])
        self.receive_route(self.rs, self.DATA["AS2_ok_ok_roa3"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64514", "999:64516"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_090_AS2_pref_ok_orig_ok_arin_tag_only(self):
        """{}: AS2 prefix ok, origin ok, ARIN: tag only (w/ prefix_validated_via_arin_whois_db_dump)"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514", "999:0:64518"])
        self.receive_route(self.rs, self.DATA["AS2_ok_ok_arin3"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64514", "999:64518"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_090_AS6_pref_ok_orig_ok_roa_arin_enforced(self):
        """{}: AS6 prefix ok, origin ok, ROA + ARIN: enforce (w/ comms [arin_whois_db_dump, rpki_roas])"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64514", "999:0:64516", "999:0:64518"])
        self.receive_route(self.rs, self.DATA["AS6_ok_ok_roa6_arin6"],
                           self.AS6, as_path="6", next_hop=self.AS6,
                           std_comms=["999:64512", "999:64514", "999:64516", "999:64518"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

class TagASSetScenario_EmptyAS_SETs(object):

    AS_SET = {
        "AS1": [],
        "AS-AS2": [],
        "AS-AS4": [],
        "AS-AS5_FROM_PDB": [],
        "AS6": []
    }
    R_SET = {
        "AS1": [
        ],
        "AS-AS2": [
        ],
        "AS-AS4": [
        ],
        "AS-AS5_FROM_PDB": [
        ],
        "AS6": [
        ]
    }

    def _set_lrg_comms(self, lst):
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
                            ext_comms=[],
                            lrg_comms=lrg_comms)

    def test_040_AS4_origin_enforcement(self):
        """{}: AS4 origin enforcement"""
        for pref in (self.DATA["AS4_pref_ok_origin_ok1"],
                     self.DATA["AS4_pref_ko_origin_ok1"],
                     self.DATA["AS3_pref_ok_origin_ko2"],
                     self.DATA["AS3_pref_ko_origin_ko1"]):
            self.receive_route(self.rs, pref, self.AS4, next_hop=self.AS4,
                               ext_comms=[],
                               filtered=True, reject_reason=(9, 12))

    def test_050_AS4_prefix_enforcement(self):
        """{}: AS4 prefix enforcement"""
        for pref in (self.DATA["AS5_pref_ok_origin_ok1"],
                     self.DATA["AS5_pref_ko_origin_ok1"],
                     self.DATA["AS3_pref_ok_origin_ko3"],
                     self.DATA["AS3_pref_ko_origin_ko1"]):
            self.receive_route(self.rs, pref, self.AS5, next_hop=self.AS5,
                               ext_comms=[],
                               filtered=True, reject_reason=(9, 12))

    def test_060_AS2_whitelist_wl_ok(self):
        """{}: AS2 white list, prefix WL, origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS2_pref_wl_origin_ok"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64512", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS2_whitelist_ok_wl(self):
        """{}: AS2 white list, prefix ok, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS2_pref_ok_origin_wl"],
                           self.AS2, as_path="2 21", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS4_whitelist_wl_ok(self):
        """{}: AS4 white list, prefix WL, origin ok"""
        self.receive_route(self.rs, self.DATA["AS4_pref_wl_origin_ok"],
                           self.AS4, as_path="4", next_hop=self.AS4,
                           ext_comms=[],
                           filtered=True)

    def test_060_AS4_whitelist_ok_wl(self):
        """{}: AS4 white list, prefix ok, origin WL"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64514"])
        self.receive_route(self.rs, self.DATA["AS4_pref_ok_origin_wl"],
                           self.AS4, as_path="4 41", next_hop=self.AS4,
                           std_comms=["999:64513", "999:64514"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS5_whitelist_wl_ok(self):
        """{}: AS5 white list, prefix WL, origin ok"""
        lrg_comms = self._set_lrg_comms(["999:0:64512", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS5_pref_wl_origin_ok"],
                           self.AS5, as_path="5", next_hop=self.AS5,
                           std_comms=["999:64512", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_060_AS5_whitelist_ok_wl(self):
        """{}: AS5 white list, prefix ok, origin WL"""
        self.receive_route(self.rs, self.DATA["AS5_pref_ok_origin_wl"],
                           self.AS5, as_path="5 51", next_hop=self.AS5,
                           ext_comms=[],
                           filtered=True)

    def test_070_AS6_roas_as_route_objects_2(self):
        """{}: AS6 RPKI ROAs as route objects: ko"""
        self.receive_route(self.rs, self.DATA["AS3_roa2"],
                           self.AS6, as_path="6 3", next_hop=self.AS6,
                           ext_comms=[],
                           filtered=True)

    def test_070_AS2_roas_as_route_objects_tag_only(self):
        """{}: AS2 RPKI ROAs as route objects: tag only (w/o prefix_validated_via_rpki_roas)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS2_roa2"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_080_AS6_arin_whois_db_1(self):
        """{}: AS6 ARIN Whois DB: ok (solely because of route white list)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515", "999:0:64517"])
        self.receive_route(self.rs, self.DATA["AS3_arin1"],
                           self.AS6, as_path="6 3", next_hop=self.AS6,
                           std_comms=["999:64513", "999:64515", "999:64517"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_080_AS2_arin_whois_db_tag_only(self):
        """{}: AS2 ARIN Whois DB: tag only (w/o prefix_validated_via_arin_whois_db_dump)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS2_arin1"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_090_AS2_roa_and_arin_tag_only(self):
        """{}: AS2 ROA + ARIN Whois DB: tag only (w/o comms [arin_whois_db_dump, rpki_roas])"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS2_roa3_arin2"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_090_AS6_roa_and_arin_enforced(self):
        """{}: AS6 ROA + ARIN Whois DB: enforced (rejected)"""
        self.receive_route(self.rs, self.DATA["AS3_roa3_arin2"],
                           self.AS6, as_path="6 3", next_hop=self.AS6,
                           ext_comms=[],
                           filtered=True)

    def test_090_AS2_pref_ok_orig_ok_roa_tag_only(self):
        """{}: AS2 prefix ok, origin ok, ROA: tag only (w/o prefix_validated_via_rpki_roas)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS2_ok_ok_roa3"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_090_AS2_pref_ok_orig_ok_arin_tag_only(self):
        """{}: AS2 prefix ok, origin ok, ARIN: tag only (w/o prefix_validated_via_arin_whois_db_dump)"""
        lrg_comms = self._set_lrg_comms(["999:0:64513", "999:0:64515"])
        self.receive_route(self.rs, self.DATA["AS2_ok_ok_arin3"],
                           self.AS2, as_path="2", next_hop=self.AS2,
                           std_comms=["999:64513", "999:64515"],
                           ext_comms=[],
                           lrg_comms=lrg_comms)

    def test_090_AS6_pref_ok_orig_ok_roa_arin_enforced(self):
        """{}: AS6 prefix ok, origin ok, ROA + ARIN: rejected"""
        self.receive_route(self.rs, self.DATA["AS6_ok_ok_roa6_arin6"],
                           self.AS6, as_path="6", next_hop=self.AS6,
                           ext_comms=[],
                           filtered=True)

class TagASSetScenarioBIRD(TagASSetScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    TARGET_VERSION = None
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
                )
            ]
        )

class TagASSetScenarioBIRD2(TagASSetScenarioBIRD):
    __test__ = False

    TARGET_VERSION = "2.0.7"

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

class TagASSetScenarioOpenBGPDPrevious(TagASSetScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = OpenBGPDPreviousInstance.BGP_SPEAKER_VERSION

class TagASSetScenarioOpenBGPDLatest(TagASSetScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = OpenBGPDLatestInstance.BGP_SPEAKER_VERSION

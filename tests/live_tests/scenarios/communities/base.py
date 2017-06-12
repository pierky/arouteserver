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

import unittest

from pierky.arouteserver.builder import OpenBGPDConfigBuilder, BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario, \
                                                      LiveScenario_TagRejectPolicy
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance, \
                                                          OpenBGPD60Instance
from pierky.arouteserver.tests.live_tests.bird import BIRDInstance

class BGPCommunitiesScenario(LiveScenario):
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
                cls.DATA["AS1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS1.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS2",
                cls.DATA["AS2_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS2.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS131073",
                cls.DATA["AS131073_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS131073.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            )
        ]

    def set_instance_variables(self):
        self.AS1 = self._get_instance_by_name("AS1")
        self.AS2 = self._get_instance_by_name("AS2")
        self.AS131073 = self._get_instance_by_name("AS131073")
        self.rs = self._get_instance_by_name("rs")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS131073)

    def test_031_only_to_AS1_std(self):
        """{}: announce to AS1 only (std)"""
        pref = self.DATA["AS2_only_to_AS1_s"]
        self.receive_route(self.rs, pref, self.AS2,
                           std_comms=["0:999", "999:1"],
                           ext_comms=[],
                           lrg_comms=[])
        self.receive_route(self.AS1, pref, self.rs,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS131073, pref)
        msg = ("route didn't pass control communities checks - "
               "NOT ANNOUNCING {} TO {{inst}}".format(pref))
        self.log_contains(self.rs, msg, {"inst": self.AS131073})

    def test_031_only_to_AS1_ext(self):
        """{}: announce to AS1 only (ext)"""
        pref = self.DATA["AS2_only_to_AS1_e"]
        self.receive_route(self.rs, pref, self.AS2,
                           std_comms=[],
                           ext_comms=["rt:0:999", "rt:999:1"],
                           lrg_comms=[])
        if isinstance(self.rs, OpenBGPDInstance):
            #TODO: don't check for ext_comms on OpenBGPD since
            #      it seems not possible to remove ext comms using
            #      wildcard, so ext comms scrubbing is not implemented
            self.receive_route(self.AS1, pref, self.rs,
                               std_comms=[], lrg_comms=[])
        else:
            self.receive_route(self.AS1, pref, self.rs,
                               std_comms=[], ext_comms=[], lrg_comms=[])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS131073, pref)
        msg = ("route didn't pass control communities checks - "
               "NOT ANNOUNCING {} TO {{inst}}".format(pref))
        self.log_contains(self.rs, msg, {"inst": self.AS131073})

    def test_031_only_to_AS1_lrg(self):
        """{}: announce to AS1 only (lrg)"""
        if isinstance(self.rs, OpenBGPD60Instance):
            raise unittest.SkipTest("Large comms not supported by OpenBGPD 6.0")

        pref = self.DATA["AS2_only_to_AS1_l"]
        self.receive_route(self.rs, pref, self.AS2,
                           std_comms=[],
                           ext_comms=[],
                           lrg_comms=["999:0:999", "999:999:1"])
        self.receive_route(self.AS1, pref, self.rs,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS131073, pref)
        msg = ("route didn't pass control communities checks - "
               "NOT ANNOUNCING {} TO {{inst}}".format(pref))
        self.log_contains(self.rs, msg, {"inst": self.AS131073})

    def test_032_only_to_AS131073_ext(self):
        """{}: announce to AS131073 only (ext)"""
        pref = self.DATA["AS2_only_to_AS131073_e"]
        self.receive_route(self.rs, pref, self.AS2,
                           std_comms=["0:999"],
                           ext_comms=["rt:999:131073"],
                           lrg_comms=[])
        if isinstance(self.rs, OpenBGPDInstance):
            #TODO: don't check for ext_comms on OpenBGPD since
            #      it seems not possible to remove ext comms using
            #      wildcard, so ext comms scrubbing is not implemented
            self.receive_route(self.AS131073, pref, self.rs,
                            std_comms=[], lrg_comms=[])
        else:
            self.receive_route(self.AS131073, pref, self.rs,
                            std_comms=[], ext_comms=[], lrg_comms=[])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS1, pref)
        msg = ("route didn't pass control communities checks - "
               "NOT ANNOUNCING {} TO {{inst}}".format(pref))
        self.log_contains(self.rs, msg, {"inst": self.AS1})

    def test_032_only_to_AS131073_lrg(self):
        """{}: announce to AS131073 only (lrg)"""
        if isinstance(self.rs, OpenBGPD60Instance):
            raise unittest.SkipTest("Large comms not supported by OpenBGPD 6.0")

        pref = self.DATA["AS2_only_to_AS131073_l"]
        self.receive_route(self.rs, pref, self.AS2,
                           std_comms=[],
                           ext_comms=[],
                           lrg_comms=["999:0:999", "999:999:131073"])
        if isinstance(self.rs, OpenBGPDInstance):
            #TODO: don't check for ext_comms on OpenBGPD since
            #      it seems not possible to remove ext comms using
            #      wildcard, so ext comms scrubbing is not implemented
            self.receive_route(self.AS131073, pref, self.rs,
                               std_comms=[], lrg_comms=[])
        else:
            self.receive_route(self.AS131073, pref, self.rs,
                               std_comms=[], ext_comms=[], lrg_comms=[])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS1, pref)
        msg = ("route didn't pass control communities checks - "
               "NOT ANNOUNCING {} TO {{inst}}".format(pref))
        self.log_contains(self.rs, msg, {"inst": self.AS1})

    def test_040_custom_bgp_community_std(self):
        """{}: custom BGP community (std)"""
        for inst in (self.AS2, self.AS131073):
            self.receive_route(inst, self.DATA["AS1_good1"], self.rs,
                               std_comms=["65501:65501"])

    def test_040_custom_bgp_community_ext(self):
        """{}: custom BGP community (ext)"""
        for inst in (self.AS2, self.AS131073):
            self.receive_route(inst, self.DATA["AS1_good1"], self.rs,
                               ext_comms=["rt:65501:65501"])

    def test_040_custom_bgp_community_lrg(self):
        """{}: custom BGP community (lrg)"""
        if isinstance(self.rs, OpenBGPD60Instance):
            raise unittest.SkipTest("Large comms not supported by OpenBGPD 6.0")
        for inst in (self.AS2, self.AS131073):
            self.receive_route(inst, self.DATA["AS1_good1"], self.rs,
                               lrg_comms=["999:65501:65501"])

    def test_041_custom_bgp_community_scrubbed_inbound(self):
        """{}: custom BGP community scrubbed"""
        self.receive_route(self.rs, self.DATA["AS2_bad_cust_comm1"], self.AS2,
                           std_comms=[])
        for inst in (self.AS1, self.AS131073):
            self.receive_route(inst, self.DATA["AS2_bad_cust_comm1"], self.rs,
                               std_comms=[])

class BGPCommunitiesScenarioBIRD(BGPCommunitiesScenario):
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

class BGPCommunitiesScenarioOpenBGPD(LiveScenario_TagRejectPolicy,
                                     BGPCommunitiesScenario):
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

class BGPCommunitiesScenarioOpenBGPD60(BGPCommunitiesScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = "6.0"

class BGPCommunitiesScenarioOpenBGPD61(BGPCommunitiesScenarioOpenBGPD):
    __test__ = False

    TARGET_VERSION = "6.1"

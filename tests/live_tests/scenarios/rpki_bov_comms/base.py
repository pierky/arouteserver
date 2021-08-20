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

from pierky.arouteserver.builder import BIRDConfigBuilder, OpenBGPDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance, \
                                                          OpenBGPDPreviousInstance, \
                                                          OpenBGPDLatestInstance

class RPKICustomBOVCommunitiesScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    IP_VER = None
    TARGET_VERSION = None

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder

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
            )
        ]

    def set_instance_variables(self):
        self.AS1 = self._get_instance_by_name("AS1")
        self.AS2 = self._get_instance_by_name("AS2")
        self.rs = self._get_instance_by_name("rs")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)

    def test_030_rpki_AS2_invalid_bad_asn(self):
        """{}: RPKI, AS2 invalid prefix, bad ASN"""
        prefix = self.DATA["AS2_invalid1"]

        # When 'reject_invalid' is False, OpenBGPD filters use an ext community
        # to track INVALID routes internally, that cannot be removed, otherwise
        # the only piece of information available to determine the need of not
        # announcing those routes to the clients would be lost.
        # That internal ext community is needed to keep the configurations
        # backward compatible with versions of OpenBGPD < 6.4, where the 'ovs'
        # attribute was not present.
        if isinstance(self.rs, OpenBGPDInstance):
            rpki_invalid_ext_comms = ["soo:65535:10"]
        else:
            rpki_invalid_ext_comms = []

        self.receive_route(self.rs, prefix, self.AS2, as_path="2",
                           std_comms=["64512:2"],
                           ext_comms=["rfc8097-invalid"] + rpki_invalid_ext_comms,
                           lrg_comms=[])

        for client in (self.AS1, ):
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(client, prefix, self.rs)

    def test_040_rpki_AS2_valid_1(self):
        """{}: RPKI, AS2 valid prefix, exact match"""
        prefix = self.DATA["AS2_valid1"]

        self.receive_route(self.rs, prefix, self.AS2, as_path="2 101",
                           std_comms=["64512:1"],
                           ext_comms=["rfc8097-valid"],
                           lrg_comms=[])

        for client in (self.AS1, ):
            self.receive_route(client, prefix, self.rs, as_path="2 101",
                               std_comms=[],
                               lrg_comms=[],
                               ext_comms=[])

    def test_900_reconfigure(self):
        """{}: reconfigure"""
        self.rs.reload_config()
        self.test_020_sessions_up()


class RPKICustomBOVCommunitiesScenario(RPKICustomBOVCommunitiesScenario):
    __test__ = False


class RPKICustomBOVCommunitiesScenario_BIRD2(RPKICustomBOVCommunitiesScenario):
    __test__ = False


class RPKICustomBOVCommunitiesScenario_OpenBGPDLatest(RPKICustomBOVCommunitiesScenario):
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
                                     target_version=cls.TARGET_VERSION or cls.RS_INSTANCE_CLASS.TARGET_VERSION),
                    "/etc/bgpd.conf"
                )
            ]
        )

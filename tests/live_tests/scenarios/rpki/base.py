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

from pierky.arouteserver.builder import BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance, \
                                                          OpenBGPDPreviousInstance, \
                                                          OpenBGPDLatestInstance

class RPKIINVALIDScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    IP_VER = None
    TARGET_VERSION = None

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder

    @classmethod
    def _get_local_files(cls):
        return [
            "header",
            "header{}".format(cls.IP_VER)
        ]

    @classmethod
    def _get_local_file_names(cls):
        return [
            (
                cls.use_static_file("bird_header.local"),
                "/etc/bird/header.local"
            ),
            (
                cls.use_static_file("bird_header{}.local".format(cls.IP_VER)),
                "/etc/bird/header{}.local".format(cls.IP_VER)
            )
        ]

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls.RS_INSTANCE_CLASS(
                "rs",
                cls.DATA["rs_IPAddress"],
                [
                    (
                        cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER,
                                         target_version=cls.TARGET_VERSION,
                                         local_files=cls._get_local_files(),
                                         hooks=[
                                             "announce_rpki_invalid_to_client",
                                             "post_announce_to_client"
                                         ]),
                        "/etc/bird/bird.conf"
                    )
                ] + cls._get_local_file_names()
            ),
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
                "AS3",
                cls.DATA["AS3_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS3.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS4",
                cls.DATA["AS4_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS4.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
        ]

    def set_instance_variables(self):
        self.AS1 = self._get_instance_by_name("AS1")
        self.AS2 = self._get_instance_by_name("AS2")
        self.AS3 = self._get_instance_by_name("AS3")
        self.AS4 = self._get_instance_by_name("AS4")
        self.rs = self._get_instance_by_name("rs")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS3)
        self.session_is_up(self.rs, self.AS4)

    def test_030_rpki_AS2_invalid_bad_asn(self):
        """{}: RPKI, AS2 invalid prefix, bad ASN"""
        prefix = self.DATA["AS2_invalid1"]
        self.receive_route(self.rs, prefix, self.AS2, as_path="2")
        self.receive_route(self.AS1, prefix, self.rs, as_path="2",
                           std_comms=["64512:2"], lrg_comms=[], ext_comms=[])
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.AS4, prefix, self.rs)

    def test_030_rpki_AS2_invalid_bad_len(self):
        """{}: RPKI, AS2 invalid prefix, bad length"""
        prefix = self.DATA["AS2_badlen"]
        self.receive_route(self.rs, prefix, self.AS2, as_path="2 101")
        self.receive_route(self.AS1, prefix, self.rs, as_path="2 101",
                           std_comms=["64512:2"], lrg_comms=[], ext_comms=[])
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.AS4, prefix, self.rs)

    def test_040_rpki_AS2_valid_1(self):
        """{}: RPKI, AS2 valid prefix, exact match"""
        prefix = self.DATA["AS2_valid1"]
        self.receive_route(self.rs, prefix, self.AS2, as_path="2 101")
        for inst in (self.AS1, self.AS4):
            self.receive_route(inst, prefix, self.rs, as_path="2 101",
                               std_comms=["64512:1"], lrg_comms=[], ext_comms=[])

    def test_040_rpki_AS2_valid_2(self):
        """{}: RPKI, AS2 valid prefix, sub prefix"""
        prefix = self.DATA["AS2_valid2"]
        self.receive_route(self.rs, prefix, self.AS2, as_path="2 101")
        for inst in (self.AS1, self.AS4):
            self.receive_route(inst, prefix, self.rs, as_path="2 101",
                               std_comms=["64512:1"], lrg_comms=[], ext_comms=[])

    def test_040_rpki_AS2_unknown_1(self):
        """{}: RPKI, AS2 unknown prefix"""
        prefix = self.DATA["AS2_unknown1"]
        self.receive_route(self.rs, prefix, self.AS2, as_path="2")
        for inst in (self.AS1, self.AS4):
            self.receive_route(inst, prefix, self.rs, as_path="2",
                               std_comms=["64512:3"], lrg_comms=[], ext_comms=[])

    def test_050_rpki_AS3_invalid_bad_asn(self):
        """{}: RPKI, AS3 invalid prefix, bad ASN"""
        prefix = self.DATA["AS3_invalid1"]
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.rs, prefix, self.AS3)
        self.log_contains(self.rs,
                          "RPKI, route is INVALID - REJECTING {}".format(
                              prefix))
        for inst in (self.AS1, self.AS4):
            with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                self.receive_route(inst, prefix, self.rs)

    def test_050_rpki_AS3_invalid_bad_len(self):
        """{}: RPKI, AS3 invalid prefix, bad length"""
        prefix = self.DATA["AS3_badlen"]
        with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
            self.receive_route(self.rs, prefix, self.AS3)
        self.log_contains(self.rs,
                          "RPKI, route is INVALID - REJECTING {}".format(
                              prefix))
        for inst in (self.AS1, self.AS4):
                with six.assertRaisesRegex(self, AssertionError, "Routes not found."):
                    self.receive_route(inst, prefix, self.rs)

    def test_060_rpki_AS3_valid_1(self):
        """{}: RPKI, AS3 valid prefix, exact match"""
        prefix = self.DATA["AS3_valid1"]
        self.receive_route(self.rs, prefix, self.AS3, as_path="3 103")
        for inst in (self.AS1, self.AS4):
            self.receive_route(inst, prefix, self.rs, as_path="3 103",
                               std_comms=["64512:1"], lrg_comms=[], ext_comms=[])

    def test_060_rpki_AS3_valid_2(self):
        """{}: RPKI, AS3 valid prefix, sub prefix"""
        prefix = self.DATA["AS3_valid2"]
        self.receive_route(self.rs, prefix, self.AS3, as_path="3 103")
        for inst in (self.AS1, self.AS4):
            self.receive_route(inst, prefix, self.rs, as_path="3 103",
                               std_comms=["64512:1"], lrg_comms=[], ext_comms=[])

    def test_060_rpki_AS3_unknown_1(self):
        """{}: RPKI, AS3 unknown prefix"""
        prefix = self.DATA["AS3_unknown1"]
        self.receive_route(self.rs, prefix, self.AS3, as_path="3")
        for inst in (self.AS1, self.AS4):
            self.receive_route(inst, prefix, self.rs, as_path="3",
                               std_comms=["64512:3"], lrg_comms=[], ext_comms=[])

    def test_900_reconfigure(self):
        """{}: reconfigure"""
        self.rs.reload_config()
        self.test_020_sessions_up()

class RPKIINVALIDScenario2(RPKIINVALIDScenario):
    __test__ = False

    TARGET_VERSION = "2.0.8"

    @classmethod
    def _get_local_files(cls):
        return [
            "header"
        ]

    @classmethod
    def _get_local_file_names(cls):
        return [
            (
                cls.use_static_file("bird2_header.local"),
                "/etc/bird/header.local"
            )
        ]

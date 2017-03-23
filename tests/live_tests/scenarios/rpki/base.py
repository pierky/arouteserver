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

from pierky.arouteserver.builder import BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario

class RPKIINVALIDScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    IP_VER = None

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls.RS_INSTANCE_CLASS(
                "rs",
                cls.DATA["rs_IPAddress"],
                [
                    (
                        cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER,
                                         cfg_roas="roas{}.yml".format(cls.IP_VER)),
                        "/etc/bird/bird.conf"
                    )
                ]
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

    def test_030_rpki_invalid_bad_asn(self):
        """{}: RPKI, invalid prefix, bad ASN"""
        prefix = self.DATA["AS2_invalid1"]
        self.receive_route(self.rs, prefix, self.AS2, as_path="2")
        self.receive_route(self.AS1, prefix, self.rs, as_path="2",
                           std_comms=["64512:2"], lrg_comms=[], ext_comms=[])

    def test_030_rpki_invalid_bad_len(self):
        """{}: RPKI, invalid prefix, bad lenght"""
        prefix = self.DATA["AS2_badlen"]
        self.receive_route(self.rs, prefix, self.AS2, as_path="2 101")
        self.receive_route(self.AS1, prefix, self.rs, as_path="2 101",
                           std_comms=["64512:2"], lrg_comms=[], ext_comms=[])

    def test_040_rpki_valid_1(self):
        """{}: RPKI, valid prefix, exact match"""
        prefix = self.DATA["AS2_valid1"]
        self.receive_route(self.rs, prefix, self.AS2, as_path="2 101")
        self.receive_route(self.AS1, prefix, self.rs, as_path="2 101",
                           std_comms=["64512:1"], lrg_comms=[], ext_comms=[])

    def test_040_rpki_valid_2(self):
        """{}: RPKI, valid prefix, sub prefix"""
        prefix = self.DATA["AS2_valid2"]
        self.receive_route(self.rs, prefix, self.AS2, as_path="2 101")
        self.receive_route(self.AS1, prefix, self.rs, as_path="2 101",
                           std_comms=["64512:1"], lrg_comms=[], ext_comms=[])


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

from ...base import LiveScenario

class TagASSetScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    IP_VER = None

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

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls.RS_INSTANCE_CLASS(
                "rs",
                cls.DATA["rs_IPAddress"],
                [
                    (
                        cls._build_rs_cfg("bird", "main.j2", "rs.conf"),
                        "/etc/bird/bird.conf"
                    )
                ],
                proto_name="the_rs"
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS1",
                cls.DATA["AS1_1_IPAddress"],
                [
                    (
                        cls._build_other_cfg("AS1.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
                client_id="AS1_1"
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS2",
                cls.DATA["AS2_1_IPAddress"],
                [
                    (
                        cls._build_other_cfg("AS2.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
                client_id="AS2_1"
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS4",
                cls.DATA["AS4_1_IPAddress"],
                [
                    (
                        cls._build_other_cfg("AS4.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
                client_id="AS4_1"
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS5",
                cls.DATA["AS5_1_IPAddress"],
                [
                    (
                        cls._build_other_cfg("AS5.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
                client_id="AS5_1"
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

    def test_030_AS2_prefix_ok_origin_ok(self):
        """{}: AS2 prefix ok origin ok"""
        self.receive_route_from(self.rs, self.DATA["AS2_pref_ok_origin_ok1"], self.AS2, as_path="2", next_hop=self.AS2,
                                std_comms=["999:64512", "999:64514"], lrg_comms=["999:0:64512", "999:0:64514"])

    def test_030_AS2_prefix_ko_origin_ok(self):
        """{}: AS2 prefix ko origin ok"""
        self.receive_route_from(self.rs, self.DATA["AS2_pref_ko_origin_ok1"], self.AS2, as_path="2", next_hop=self.AS2,
                                std_comms=["999:64513", "999:64514"], lrg_comms=["999:0:64513", "999:0:64514"])

    def test_030_AS2_prefix_ok_origin_ko(self):
        """{}: AS2 prefix ok origin ko"""
        self.receive_route_from(self.rs, self.DATA["AS3_pref_ok_origin_ko1"], self.AS2, as_path="2 3", next_hop=self.AS2,
                                std_comms=["999:64512", "999:64515"], lrg_comms=["999:0:64512", "999:0:64515"])

    def test_030_AS2_prefix_ko_origin_ko(self):
        """{}: AS2 prefix ko origin ok"""
        self.receive_route_from(self.rs, self.DATA["AS3_pref_ko_origin_ko1"], self.AS2, as_path="2 3", next_hop=self.AS2,
                                std_comms=["999:64513", "999:64515"], lrg_comms=["999:0:64513", "999:0:64515"])


    def test_040_AS4_prefix_ok_origin_ok(self):
        """{}: AS4 prefix ok origin ok"""
        self.receive_route_from(self.rs, self.DATA["AS4_pref_ok_origin_ok1"], self.AS4, as_path="4", next_hop=self.AS4,
                                std_comms=["999:64512", "999:64514"], lrg_comms=["999:0:64512", "999:0:64514"])

    def test_040_AS4_prefix_ko_origin_ok(self):
        """{}: AS4 prefix ko origin ok"""
        self.receive_route_from(self.rs, self.DATA["AS4_pref_ko_origin_ok1"], self.AS4, as_path="4", next_hop=self.AS4,
                                std_comms=["999:64513", "999:64514"], lrg_comms=["999:0:64513", "999:0:64514"])

    def test_040_AS4_prefix_ok_origin_ko(self):
        """{}: AS4 prefix ok origin ko"""
        self.receive_route_from(self.rs, self.DATA["AS3_pref_ok_origin_ko2"], self.AS4, as_path="4 3", next_hop=self.AS4, filtered=True)

    def test_040_AS4_prefix_ko_origin_ko(self):
        """{}: AS4 prefix ko origin ok"""
        self.receive_route_from(self.rs, self.DATA["AS3_pref_ko_origin_ko1"], self.AS4, as_path="4 3", next_hop=self.AS4, filtered=True)


    def test_050_AS5_prefix_ok_origin_ok(self):
        """{}: AS5 prefix ok origin ok"""
        self.receive_route_from(self.rs, self.DATA["AS5_pref_ok_origin_ok1"], self.AS5, as_path="5", next_hop=self.AS5,
                                std_comms=["999:64512", "999:64514"], lrg_comms=["999:0:64512", "999:0:64514"])

    def test_050_AS5_prefix_ko_origin_ok(self):
        """{}: AS5 prefix ko origin ok"""
        self.receive_route_from(self.rs, self.DATA["AS5_pref_ko_origin_ok1"], self.AS5, as_path="5", next_hop=self.AS5, filtered=True)

    def test_050_AS5_prefix_ok_origin_ko(self):
        """{}: AS5 prefix ok origin ko"""
        self.receive_route_from(self.rs, self.DATA["AS3_pref_ok_origin_ko3"], self.AS5, as_path="5 3", next_hop=self.AS5,
                                std_comms=["999:64512", "999:64515"], lrg_comms=["999:0:64512", "999:0:64515"])

    def test_050_AS5_prefix_ko_origin_ko(self):
        """{}: AS5 prefix ko origin ok"""
        self.receive_route_from(self.rs, self.DATA["AS3_pref_ko_origin_ko1"], self.AS5, as_path="5 3", next_hop=self.AS5, filtered=True)

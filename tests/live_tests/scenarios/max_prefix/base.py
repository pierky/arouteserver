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

import os

from pierky.arouteserver.tests.live_tests.base import LiveScenario

class MaxPrefixScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    IP_VER = None

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls.RS_INSTANCE_CLASS(
                "rs",
                cls.DATA["rs_IPAddress"],
                [
                    (
                        cls.build_rs_cfg("bird", "main.j2", "rs.conf"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
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
                "AS3",
                cls.DATA["AS3_1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS3.j2"),
                        "/etc/bird/bird.conf"
                    )
                ],
            ),
        ]

    def set_instance_variables(self):
        self.rs = self._get_instance_by_name("rs")
        self.AS1 = self._get_instance_by_name("AS1")
        self.AS2 = self._get_instance_by_name("AS2")
        self.AS3 = self._get_instance_by_name("AS3")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS3)

    def test_030_blocked_sessions(self):
        """{}: log is populated"""
        log_tpl = "Protocol {{inst}} hits route import limit ({limit}), action: block"

        log = log_tpl.format(limit=4)
        self.log_contains(self.rs, log, {"inst": self.AS1})

        log = log_tpl.format(limit=3)
        self.log_contains(self.rs, log, {"inst": self.AS2})

        log = log_tpl.format(limit=2)
        self.log_contains(self.rs, log, {"inst": self.AS3})

    def _get_routes_from(self, asn, include_filtered=False):
        routes = []
        for prefix_num in (1,2,3,4,5):
            routes.extend(
                self.rs.get_routes(
                    self.DATA["AS{}_pref{}".format(asn, prefix_num)],
                    include_filtered=include_filtered
                )
            )
        return routes

    def test_030_count_received_prefixes_AS1(self):
        """{}: number of prefixes received by rs from AS1"""

        self.assertEqual(len(self._get_routes_from(1)), 4)
        self.assertEqual(len(self._get_routes_from(1, include_filtered=True)), 5)

    def test_031_count_received_prefixes_AS2(self):
        """{}: number of prefixes received by rs from AS2"""

        self.assertEqual(len(self._get_routes_from(2)), 3)
        self.assertEqual(len(self._get_routes_from(2, include_filtered=True)), 5)

    def test_032_count_received_prefixes_AS3(self):
        """{}: number of prefixes received by rs from AS3"""

        self.assertEqual(len(self._get_routes_from(3)), 2)
        self.assertEqual(len(self._get_routes_from(3, include_filtered=True)), 5)


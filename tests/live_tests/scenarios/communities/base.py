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

from pierky.arouteserver.tests.live_tests.base import LiveScenario

class BGPCommunitiesScenario(LiveScenario):
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

    def test_020_only_to_AS1_std(self):
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

    def test_021_only_to_AS1_ext(self):
        """{}: announce to AS1 only (ext)"""
        pref = self.DATA["AS2_only_to_AS1_e"]
        self.receive_route(self.rs, pref, self.AS2,
                           std_comms=[],
                           ext_comms=["rt:0:999", "rt:999:1"],
                           lrg_comms=[])
        self.receive_route(self.AS1, pref, self.rs,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS131073, pref)
        msg = ("route didn't pass control communities checks - "
               "NOT ANNOUNCING {} TO {{inst}}".format(pref))
        self.log_contains(self.rs, msg, {"inst": self.AS131073})

    def test_022_only_to_AS1_lrg(self):
        """{}: announce to AS1 only (lrg)"""
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

    def test_030_only_to_AS131073_ext(self):
        """{}: announce to AS131073 only (ext)"""
        pref = self.DATA["AS2_only_to_AS131073_e"]
        self.receive_route(self.rs, pref, self.AS2,
                           std_comms=["0:999"],
                           ext_comms=["rt:999:131073"],
                           lrg_comms=[])
        self.receive_route(self.AS131073, pref, self.rs,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS1, pref)
        msg = ("route didn't pass control communities checks - "
               "NOT ANNOUNCING {} TO {{inst}}".format(pref))
        self.log_contains(self.rs, msg, {"inst": self.AS1})

    def test_031_only_to_AS131073_lrg(self):
        """{}: announce to AS131073 only (lrg)"""
        pref = self.DATA["AS2_only_to_AS131073_l"]
        self.receive_route(self.rs, pref, self.AS2,
                           std_comms=[],
                           ext_comms=[],
                           lrg_comms=["999:0:999", "999:999:131073"])
        self.receive_route(self.AS131073, pref, self.rs,
                           std_comms=[], ext_comms=[], lrg_comms=[])
        with self.assertRaisesRegexp(AssertionError, "Routes not found."):
            self.receive_route(self.AS1, pref)
        msg = ("route didn't pass control communities checks - "
               "NOT ANNOUNCING {} TO {{inst}}".format(pref))
        self.log_contains(self.rs, msg, {"inst": self.AS1})


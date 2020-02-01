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

from pierky.arouteserver.builder import BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario
from pierky.arouteserver.tests.live_tests.bird import BIRDInstance

class BIRD2RPKIRTRScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    TARGET_VERSION = "2.0.7"
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
                ),
                (
                    cls.use_static_file("rpki_rtr_config.local"),
                    "/etc/bird/rpki_rtr_config.local"
                )
            ]
        )

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls._setup_rs_instance()
        ]

    def set_instance_variables(self):
        self.rs = self._get_instance_by_name("rs")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

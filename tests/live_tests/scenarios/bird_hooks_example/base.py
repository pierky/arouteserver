# Copyright (C) 2017-2023 Pier Carlo Chiodi
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

class BIRDHooksExampleScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    CONFIG_BUILDER_CLASS = BIRDConfigBuilder

    AS_SET = {
        "AS3333": [3333],
        "AS10745": [10745],
    }
    R_SET = {
        "AS10745": [
            "AS10745_allowed_prefixes"
        ],
        "AS3333": [
            "AS3333_allowed_prefixes"
        ],
    }

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

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER,
                                     hooks=["pre_receive_from_client",
                                            "post_receive_from_client",
                                            "pre_announce_to_client",
                                            "post_announce_to_client",
                                            "scrub_communities_in",
                                            "scrub_communities_out",
                                            "apply_blackhole_filtering_policy",
                                            "route_can_be_announced_to",
                                            "announce_rpki_invalid_to_client"],
                                     local_files=["header"]),
                    "/etc/bird/bird.conf"
                ),
                (
                    cls.use_static_file("header.local"),
                    "/etc/bird/header.local"
                )
            ]
        )

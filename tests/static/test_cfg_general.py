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
import unittest

import yaml

from .cfg_base import TestConfigParserBase 
from pierky.arouteserver.config.general import ConfigParserGeneral
from pierky.arouteserver.errors import ConfigError


class TestConfigParserGeneral(TestConfigParserBase):

    FILE_PATH = "config.d/general.yml"
    CONFIG_PARSER_CLASS = ConfigParserGeneral
    SHORT_DESCR = "General config parser"

    VALID_STD_COMMS = ("65534:666", "1:1", "0:0", "1:0", "65534:65535", "rs_as:1")
    VALID_LRG_COMMS = ("65535:666:0", "1:1:1", "0:0:0", "1:0:65535", "4294967295:4294967295:4294967295", "rs_as:1:2")
    VALID_EXT_COMMS = ("rt:1:0", "rt:65535:666", "ro:65535:666", "rt:rs_as:3")

    def test_valid_cfg(self):
        """{}: valid configuration"""
        self._contains_err()

    def test_unknown_statement(self):
        """{}: unknown statement"""
        self.cfg["test"] = "test"
        self._contains_err("Unknown statement at 'cfg' level: 'test'.")

    def test_rs_as(self):
        """{}: rs_as"""
        self.assertEqual(self.cfg["rs_as"], 999)
        for asn in (-1, 0, "test"):
            self.cfg["rs_as"] = asn
            self._contains_err("Error parsing 'rs_as' at 'cfg' level - Invalid ASN: {}".format(str(asn)))

        for asn in (1, 65535, 4294967295): 
            self.cfg["rs_as"] = asn
            self._contains_err()

        self._test_mandatory(self.cfg, "rs_as")

    def test_router_id(self):
        """{}: router_id"""
        self.assertEqual(self.cfg["router_id"], "192.0.2.2")
        for v in ("1.0.0.1", "10.0.0.1"):
            self.cfg["router_id"] = v
            self._contains_err()
        for v in ("10.0.0.1/24", "fe80::1", "2001:db8::1", "test"):
            self.cfg["router_id"] = v
            self._contains_err("Error parsing 'router_id' at 'cfg' level - Invalid IPv4 address: {}.".format(v))
        self._test_mandatory(self.cfg, "router_id")

    def test_prepend_rs_as(self):
        """{}: prepend_rs_as"""
        self.assertEqual(self.cfg["prepend_rs_as"], False)
        self._test_bool_val(self.cfg, "prepend_rs_as")
        self._test_mandatory(self.cfg, "prepend_rs_as", has_default=True)

    def test_path_hiding(self):
        """{}: path_hiding"""
        self._test_bool_val(self.cfg, "path_hiding")
        self._test_optional(self.cfg, "path_hiding")

    def test_passive(self):
        """{}: passive"""
        self.assertEqual(self.cfg["passive"], True)
        self._test_bool_val(self.cfg, "passive")
        self._test_mandatory(self.cfg, "passive", has_default=True)

    def test_gtsm(self):
        """{}: gtsm"""
        self.assertEqual(self.cfg["gtsm"], False)
        self._test_bool_val(self.cfg, "gtsm")
        self._test_mandatory(self.cfg, "gtsm", has_default=True)

    def test_add_path(self):
        """{}: add_path"""
        self.assertEqual(self.cfg["add_path"], False)
        self._test_bool_val(self.cfg, "add_path")
        self._test_mandatory(self.cfg, "add_path", has_default=True)

    def test_next_hop_policy(self):
        """{}: next_hop.policy"""
        self.assertEqual(self.cfg["filtering"]["next_hop"]["policy"], "strict")
        self._test_option(self.cfg["filtering"]["next_hop"], "policy", ("strict", "same-as"))
        self._test_mandatory(self.cfg["filtering"]["next_hop"], "policy", has_default=True)

    def test_next_hop_policy(self):
        """{}: next_hop_policy (pre v0.6.0 format)"""

        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  filtering:\n"
            "    next_hop_policy: 'same-as'\n"
        )
        self.cfg.parse()
        self._contains_err()

        self.assertEqual(self.cfg["filtering"]["next_hop"]["policy"], "same-as")

    def test_ipv4_pref_len(self):
        """{}: ipv4_pref_len"""
        self.assertEqual(self.cfg["filtering"]["ipv4_pref_len"]["min"], 8)
        self.assertEqual(self.cfg["filtering"]["ipv4_pref_len"]["max"], 24)
        self.cfg["filtering"]["ipv4_pref_len"]["max"] = 32
        self._test_ip_min_max_len(self.cfg["filtering"], "ipv4_pref_len", "min", 4, (0, 1, 32), (-1, 33, "a"))

        self.cfg["filtering"]["ipv4_pref_len"]["min"] = 0
        self._test_ip_min_max_len(self.cfg["filtering"], "ipv4_pref_len", "max", 4, (0, 1, 32), (-1, 33, "a"))

        for pair in ((0, 32), (31, 32), (32, 32)):
            self.cfg["filtering"]["ipv4_pref_len"]["min"] = pair[0]
            self.cfg["filtering"]["ipv4_pref_len"]["max"] = pair[1]
            self._contains_err()
        for pair in ((10, 5), (32, 0)):
            self.cfg["filtering"]["ipv4_pref_len"]["min"] = pair[0]
            self.cfg["filtering"]["ipv4_pref_len"]["max"] = pair[1]
            self._contains_err("Error parsing 'ipv4_pref_len' at 'cfg.filtering' level - In the IPv4 min/max length, the value of 'min' must be <= the value of 'max'.")

    def test_ipv6_pref_len(self):
        """{}: ipv6_pref_len"""
        self.assertEqual(self.cfg["filtering"]["ipv6_pref_len"]["min"], 12)
        self.assertEqual(self.cfg["filtering"]["ipv6_pref_len"]["max"], 48)
        self.cfg["filtering"]["ipv6_pref_len"]["max"] = 128
        self._test_ip_min_max_len(self.cfg["filtering"], "ipv6_pref_len", "min", 6, (0, 1, 32, 64, 128), (-1, 129, "a"))

        self.cfg["filtering"]["ipv6_pref_len"]["min"] = 0
        self._test_ip_min_max_len(self.cfg["filtering"], "ipv6_pref_len", "max", 6, (0, 1, 32, 64, 128), (-1, 129, "a"))

        for pair in ((0, 64), (32, 48), (32, 32), (128, 128)):
            self.cfg["filtering"]["ipv6_pref_len"]["min"] = pair[0]
            self.cfg["filtering"]["ipv6_pref_len"]["max"] = pair[1]
            self._contains_err()
        for pair in ((10, 5), (32, 0), (128, 0), (128, 64)):
            self.cfg["filtering"]["ipv6_pref_len"]["min"] = pair[0]
            self.cfg["filtering"]["ipv6_pref_len"]["max"] = pair[1]
            self._contains_err("Error parsing 'ipv6_pref_len' at 'cfg.filtering' level - In the IPv6 min/max length, the value of 'min' must be <= the value of 'max'.")

    def test_global_black_list_pref(self):
        """{}: global_black_list_pref"""

        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  filtering:\n"
            "    global_black_list_pref:\n"
            "      - prefix: 192.0.2.0\n"
            "        length: 24\n"
            "        comment: 'Local network'\n"
        )
        self.cfg.parse()
        self._contains_err()

        self.assertEqual(self.cfg["filtering"]["global_black_list_pref"][0],
                         {
                             "prefix": "192.0.2.0",
                             "length": 24,
                             "comment": "Local network",
                             "exact": False,
                             "ge": None,
                             "le": None,
                             "max_length": 32
                         })
        self._test_optional(self.cfg["filtering"], "global_black_list_pref")

    def test_max_as_path_len(self):
        """{}: max_as_path_len"""
        self.assertEqual(self.cfg["filtering"]["max_as_path_len"], 32)
        for v in (0, 65):
            self.cfg["filtering"]["max_as_path_len"] = v
            self._contains_err("Error parsing 'max_as_path_len' at 'cfg.filtering' level - Invalid max_as_path_len: must be an integer between 1 and 64.")
        for v in (1, 64, 32):
            self.cfg["filtering"]["max_as_path_len"] = v
            self._contains_err()
        self._test_mandatory(self.cfg["filtering"], "max_as_path_len", has_default=True)

    def test_reject_invalid_as_in_as_path(self):
        """{}: reject_invalid_as_in_as_path"""
        self.assertEqual(self.cfg["filtering"]["reject_invalid_as_in_as_path"], True)
        self._test_bool_val(self.cfg["filtering"], "reject_invalid_as_in_as_path")
        self._test_mandatory(self.cfg["filtering"], "reject_invalid_as_in_as_path", has_default=True)

    def test_tag_as_set(self):
        """{}: tag_as_set"""
        self.assertEqual(self.cfg["filtering"]["irrdb"]["tag_as_set"], True)
        self._test_bool_val(self.cfg["filtering"]["irrdb"], "tag_as_set")
        self._test_mandatory(self.cfg["filtering"]["irrdb"], "tag_as_set", has_default=True)

    def test_enforce_origin_in_as_set(self):
        """{}: enforce_origin_in_as_set"""
        self.assertEqual(self.cfg["filtering"]["irrdb"]["enforce_origin_in_as_set"], True)
        self._test_bool_val(self.cfg["filtering"]["irrdb"], "enforce_origin_in_as_set")
        self._test_mandatory(self.cfg["filtering"]["irrdb"], "enforce_origin_in_as_set", has_default=True)

    def test_enforce_prefix_in_as_set(self):
        """{}: enforce_prefix_in_as_set"""
        self.assertEqual(self.cfg["filtering"]["irrdb"]["enforce_prefix_in_as_set"], True)
        self._test_bool_val(self.cfg["filtering"]["irrdb"], "enforce_prefix_in_as_set")
        self._test_mandatory(self.cfg["filtering"]["irrdb"], "enforce_prefix_in_as_set", has_default=True)

    def test_allow_longer_prefixes(self):
        """{}: allow_longer_prefixes"""
        self.assertEqual(self.cfg["filtering"]["irrdb"]["allow_longer_prefixes"], False)
        self._test_bool_val(self.cfg["filtering"]["irrdb"], "allow_longer_prefixes")
        self._test_mandatory(self.cfg["filtering"]["irrdb"], "allow_longer_prefixes", has_default=True)

    def test_rpki_enabled(self):
        """{}: rpki, enabled"""
        self.assertEqual(self.cfg["filtering"]["rpki"]["enabled"], False)
        self._test_bool_val(self.cfg["filtering"]["rpki"], "enabled")
        self._test_mandatory(self.cfg["filtering"]["rpki"], "enabled", has_default=True)

    def test_rpki_reject_invalid(self):
        """{}: rpki, reject_invalid"""
        self.assertEqual(self.cfg["filtering"]["rpki"]["reject_invalid"], True)
        self._test_bool_val(self.cfg["filtering"]["rpki"], "reject_invalid")
        self._test_optional(self.cfg["filtering"]["rpki"], "reject_invalid")

    def test_reject_policy(self):
        """{}: reject_policy"""
        self.assertEqual(self.cfg["filtering"]["reject_policy"]["policy"], "reject")
        self._test_option(self.cfg["filtering"]["reject_policy"], "policy", ("reject", "tag"))
        self._test_mandatory(self.cfg["filtering"]["reject_policy"], "policy", has_default=True)

    def test_blackhole_announce_to_client(self):
        """{}: blackhole_filtering, announce_to_client"""
        self.assertEqual(self.cfg["blackhole_filtering"]["announce_to_client"], True)
        self._test_bool_val(self.cfg["blackhole_filtering"], "announce_to_client")

    def test_blackhole_filtering_policy_ipv4(self):
        """{}: blackhole_filtering, policy_ipv4"""
        self.load_config(file_name="{}/test_cfg_general_blackhole_filtering.yml".format(os.path.dirname(__file__)))
        self.assertEqual(self.cfg["blackhole_filtering"]["policy_ipv4"], "propagate-unchanged")

        self.cfg["blackhole_filtering"]["rewrite_next_hop_ipv4"] = "192.0.2.1"
        self._test_option(self.cfg["blackhole_filtering"], "policy_ipv4", ("propagate-unchanged", "rewrite-next-hop"))
        self._test_optional(self.cfg["blackhole_filtering"], "policy_ipv4")

        self.cfg["blackhole_filtering"]["rewrite_next_hop_ipv4"] = ""
        self.cfg["blackhole_filtering"]["policy_ipv4"] = "propagate-unchanged"
        self._contains_err()
        self.cfg["blackhole_filtering"]["policy_ipv4"] = "rewrite-next-hop"
        self._contains_err("Since blackhole_filtering.policy_ipv4 is 'rewrite_next_hop', an IPv4 address must be provided in 'rewrite_next_hop_ipv4'.")

    def test_blackhole_filtering_policy_ipv6(self):
        """{}: blackhole_filtering, policy_ipv6"""
        self.load_config(file_name="{}/test_cfg_general_blackhole_filtering.yml".format(os.path.dirname(__file__)))
        self.assertEqual(self.cfg["blackhole_filtering"]["policy_ipv6"], "propagate-unchanged")

        self.cfg["blackhole_filtering"]["rewrite_next_hop_ipv6"] = "fe80::1"
        self._test_option(self.cfg["blackhole_filtering"], "policy_ipv6", ("propagate-unchanged", "rewrite-next-hop"))
        self._test_optional(self.cfg["blackhole_filtering"], "policy_ipv6")

        self.cfg["blackhole_filtering"]["rewrite_next_hop_ipv6"] = ""
        self.cfg["blackhole_filtering"]["policy_ipv6"] = "propagate-unchanged"
        self._contains_err()
        self.cfg["blackhole_filtering"]["policy_ipv6"] = "rewrite-next-hop"
        self._contains_err("Since blackhole_filtering.policy_ipv6 is 'rewrite_next_hop', an IPv6 address must be provided in 'rewrite_next_hop_ipv6'.")

    def test_blackhole_filtering_ipv4(self):
        """{}: blackhole_filtering, rewrite_next_hop, ipv4"""
        self.load_config(file_name="{}/test_cfg_general_blackhole_filtering.yml".format(os.path.dirname(__file__)))
        for ip in ("127.0.0.1", "192.168.0.1", "192.0.2.1", "12.34.56.78"):
            self.cfg["blackhole_filtering"]["rewrite_next_hop_ipv4"] = ip
            self._contains_err()
        for ip in ("10.0.0.1/24", "a", "fe80::1"):
            self.cfg["blackhole_filtering"]["rewrite_next_hop_ipv4"] = ip
            self._contains_err("Error parsing 'rewrite_next_hop_ipv4' at 'cfg.blackhole_filtering' level - Invalid IPv4 address: {}.".format(ip))
        self._test_optional(self.cfg["blackhole_filtering"], "rewrite_next_hop_ipv4")

    def test_blackhole_filtering_ipv6(self):
        """{}: blackhole_filtering, rewrite_next_hop, ipv6"""
        self.load_config(file_name="{}/test_cfg_general_blackhole_filtering.yml".format(os.path.dirname(__file__)))
        for ip in ("fe80::1", "2001:DB8::1"):
            self.cfg["blackhole_filtering"]["rewrite_next_hop_ipv6"] = ip
            self._contains_err()
        for ip in ("10.0.0.1/24", "a"):
            self.cfg["blackhole_filtering"]["rewrite_next_hop_ipv6"] = ip
            self._contains_err("Error parsing 'rewrite_next_hop_ipv6' at 'cfg.blackhole_filtering' level - Invalid IPv6 address: {}.".format(ip))
        self._test_optional(self.cfg["blackhole_filtering"], "rewrite_next_hop_ipv6")

    def test_communities_std(self):
        """{}: standard BGP communities"""


        self.cfg["communities"]["blackholing"] = {}
        for c in self.VALID_STD_COMMS:
            self.cfg["communities"]["blackholing"]["std"] = c
            self._contains_err()
        for c in ("65536:666", "-1:-1", "0:-1", "65535:65536", "1", "1:1:1", "rt:1:0") + self.VALID_LRG_COMMS + self.VALID_EXT_COMMS:
            self.cfg["communities"]["blackholing"]["std"] = c
            self._contains_err("Invalid BGP standard community: {};".format(c))
        for c in ("65534:peer_as", "peer_as:1"):
            self.cfg["communities"]["blackholing"]["std"] = c
            self._contains_err("'peer_as' macro not allowed")

        c = "65535:1"
        self.cfg["communities"]["blackholing"]["std"] = c
        self._contains_err("range 65535:x is reserved")

        self.cfg["communities"]["blackholing"]["std"] = self.VALID_STD_COMMS[0]
        self._test_optional(self.cfg["communities"]["blackholing"], "std")

    def test_communities_lrg(self):
        """{}: large BGP communities"""

        for c in self.VALID_LRG_COMMS:
            self.cfg["communities"]["blackholing"]["lrg"] = c
            self._contains_err()
        for c in ("4294967296:1:1", "-1:0:0") + self.VALID_STD_COMMS + self.VALID_EXT_COMMS:
            self.cfg["communities"]["blackholing"]["lrg"] = c
            self._contains_err("Invalid BGP large community: {};".format(c))
        for c in ("1:65535:peer_as", "peer_as:1:1", "1:peer_as:2"):
            self.cfg["communities"]["blackholing"]["lrg"] = c
            self._contains_err("'peer_as' macro not allowed")
        self.cfg["communities"]["blackholing"]["lrg"] = self.VALID_LRG_COMMS[0]
        self._test_optional(self.cfg["communities"]["blackholing"], "lrg")

    def test_communities_ext(self):
        """{}: extended BGP communities"""

        for c in self.VALID_EXT_COMMS:
            self.cfg["communities"]["blackholing"]["ext"] = c
            self._contains_err()
        for c in ("x:1:0", "ro:-1:0") + self.VALID_STD_COMMS + self.VALID_LRG_COMMS:
            self.cfg["communities"]["blackholing"]["ext"] = c
            self._contains_err("Invalid BGP extended community: {};".format(c))
        for c in ("rt:65535:peer_as", "ro:peer_as:1"):
            self.cfg["communities"]["blackholing"]["ext"] = c
            self._contains_err("'peer_as' macro not allowed")
        self._test_optional(self.cfg["communities"]["blackholing"], "ext")

    def test_mandatory_peer_as_communities(self):
        """{}: communities that need peer_as macro"""

        for comm in ("announce_to_peer", "do_not_announce_to_peer",
                     "prepend_once_to_peer", "prepend_twice_to_peer",
                     "prepend_thrice_to_peer", "add_noexport_to_peer",
                     "add_noadvertise_to_peer"):
            for c in self.VALID_STD_COMMS:
                self.cfg["communities"][comm]["std"] = c
                self._contains_err("'peer_as' macro is mandatory in this community")
            self.cfg["communities"][comm]["std"] = None
            for c in self.VALID_LRG_COMMS:
                self.cfg["communities"][comm]["lrg"] = c
                self._contains_err("'peer_as' macro is mandatory in this community")
            self.cfg["communities"][comm]["lrg"] = None
            for c in self.VALID_EXT_COMMS:
                self.cfg["communities"][comm]["ext"] = c
                self._contains_err("'peer_as' macro is mandatory in this community")
            self.cfg["communities"][comm]["ext"] = None

    def test_mandatory_dyn_val_communities(self):
        """{}: communities that need dyn_val macro"""

        comm = "reject_cause"
        for c in self.VALID_STD_COMMS:
            self.cfg["communities"][comm]["std"] = c
            self._contains_err("'dyn_val' macro is mandatory in this community")
        self.cfg["communities"][comm]["std"] = None
        for c in self.VALID_LRG_COMMS:
            self.cfg["communities"][comm]["lrg"] = c
            self._contains_err("'dyn_val' macro is mandatory in this community")
        self.cfg["communities"][comm]["lrg"] = None
        for c in self.VALID_EXT_COMMS:
            self.cfg["communities"][comm]["ext"] = c
            self._contains_err("'dyn_val' macro is mandatory in this community")
        self.cfg["communities"][comm]["ext"] = None

    def test_reject_cause_community_with_no_reject_policy(self):
        """{}: reject_cause can be set only with 'tag' reject_policy"""
        self.cfg["communities"]["reject_cause"]["std"] = "0:dyn_val"
        self._contains_err("The 'reject_cause' community can be set only if 'reject_policy.policy' is 'tag'.")

        self.cfg["filtering"]["reject_policy"]["policy"] = "tag"
        self._contains_err()

    def test_peer_as_usage_in_communities(self):
        """{}: peer_as macro usage in communities"""

        comm = "announce_to_peer"

        self.cfg["communities"][comm]["std"] = "rs_as:peer_as"
        self._contains_err()
        self.cfg["communities"][comm]["std"] = None

        self.cfg["communities"][comm]["std"] = "peer_as:rs_as"
        self._contains_err("'peer_as' macro can be used only in the last part of the value")
        self.cfg["communities"][comm]["std"] = None

        self.cfg["communities"][comm]["lrg"] = "rs_as:rs_as:peer_as"
        self._contains_err()
        self.cfg["communities"][comm]["lrg"] = None

        self.cfg["communities"][comm]["lrg"] = "peer_as:rs_as:0"
        self._contains_err("'peer_as' macro can be used only in the last part of the value")
        self.cfg["communities"][comm]["lrg"] = None

        self.cfg["communities"][comm]["lrg"] = "rs_as:peer_as:0"
        self._contains_err("'peer_as' macro can be used only in the last part of the value")
        self.cfg["communities"][comm]["lrg"] = None

    def test_dyn_val_usage_in_communities(self):
        """{}: dyn_val macro usage in communities"""

        comm = "reject_cause"

        self.cfg["filtering"]["reject_policy"]["policy"] = "tag"

        self.cfg["communities"][comm]["std"] = "rs_as:dyn_val"
        self._contains_err()
        self.cfg["communities"][comm]["std"] = None

        self.cfg["communities"][comm]["std"] = "dyn_val:rs_as"
        self._contains_err("'dyn_val' macro can be used only in the last part of the value")
        self.cfg["communities"][comm]["std"] = None

        self.cfg["communities"][comm]["lrg"] = "rs_as:rs_as:dyn_val"
        self._contains_err()
        self.cfg["communities"][comm]["lrg"] = None

        self.cfg["communities"][comm]["lrg"] = "dyn_val:rs_as:0"
        self._contains_err("'dyn_val' macro can be used only in the last part of the value")
        self.cfg["communities"][comm]["lrg"] = None

        self.cfg["communities"][comm]["lrg"] = "rs_as:dyn_val:0"
        self._contains_err("'dyn_val' macro can be used only in the last part of the value")
        self.cfg["communities"][comm]["lrg"] = None

    def test_custom_communities_valid(self):
        """{}: custom communities: valid"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
        ]
        yaml_lines = tpl + [
            "  custom_communities:",
            "    test1:",
            "      std: '1:1'",
            "    test2:",
            "      lrg: '2:2:2'",
            "    test3:",
            "      std: '3:3'",
            "      lrg: '3:3:3'",
            "      ext: 'rt:3:3'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err()

    def test_custom_communities_reserved(self):
        """{}: custom communities: reserved name"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
        ]
        yaml_lines = tpl + [
            "  custom_communities:",
            "    blackholing:",
            "      std: '1:1'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("The custom community name 'blackholing' collides with a built-in community with the same name.")

    def test_custom_communities_invalid(self):
        """{}: custom communities: invalid"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
        ]
        yaml_lines = tpl + [
            "  custom_communities:",
            "    test1:",
            "      std: peer_as"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Error parsing 'std' at 'cfg.custom_communities.test1' level - Invalid BGP standard community: peer_as; it must be in the x:x format")

        yaml_lines = tpl + [
            "  custom_communities:",
            "    test1:",
            "      std: '1:peer_as'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Error parsing 'std' at 'cfg.custom_communities.test1' level - Invalid BGP standard community: 1:peer_as")

    def test_duplicate_communities(self):
        """{}: duplicate communities"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  communities:",
            "    prefix_present_in_as_set:",
            "      std: '999:1'",
            "    prefix_not_present_in_as_set:",
            "      lrg: 'rs_as:2:2'",
        ]
        yaml_lines = tpl + [
            "    origin_present_in_as_set:",
            "      std: 'rs_as:1'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("The 'prefix_present_in_as_set.std' community's value (999:1) has already been used for another community.")

        yaml_lines = tpl + [
            "    origin_present_in_as_set:",
            "      lrg: '999:2:2'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("The 'prefix_not_present_in_as_set.lrg' community's value (999:2:2) has already been used for another community.")

        yaml_lines = tpl + [
            "  custom_communities:",
            "    test:",
            "      std: '999:1'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("The 'test.std' community's value (999:1) has already been used for another community.")

    def test_overlapping_communities_internal(self):
        """{}: overlapping communities, internal"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  communities:",
            "    reject_cause:",
            "      std: 1:dyn_val"
        ]

        # internal/outbound (prefix_not_present_in_as_set)
        yaml_lines = tpl + [
            "    prefix_not_present_in_as_set:",
            "      std: '1:1'",
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Community 'reject_cause' and 'prefix_not_present_in_as_set' overlap: 1:dyn_val / 1:1. Internal communities can't have overlapping values with any other community.")

        # internal/inbound (do_not_announce_to_peer)
        yaml_lines = tpl + [
            "    do_not_announce_to_peer:",
            "      std: '1:peer_as'",
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Community 'reject_cause' and 'do_not_announce_to_peer' overlap: 1:dyn_val / 1:peer_as. Internal communities can't have overlapping values with any other community.")

        # internal/custom
        yaml_lines = tpl + [
            "  custom_communities:",
            "    test:",
            "      std: '1:0'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Community 'reject_cause' and 'test' overlap: 1:dyn_val / 1:0. Internal communities can't have overlapping values with any other community.")

    def test_overlapping_communities_out_in(self):
        """{}: overlapping communities, outbound/inbound"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  communities:"
        ]

        # prefix_not_present_in_as_set: outbound
        # do_not_announce_to_peer: inbound
        yaml_lines = tpl + [
            "    prefix_not_present_in_as_set:",
            "      std: '0:1'",
            "    do_not_announce_to_peer:",
            "      std: '0:peer_as'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Community 'do_not_announce_to_peer' and 'prefix_not_present_in_as_set' overlap: 0:peer_as / 0:1. Inbound communities and outbound communities can't have overlapping values, otherwise they might be scrubbed.")

        # Same as above, but with 0 in the prefix_not_present_in_as_set comm.
        # No errors because 'peer_as' can't be 0.
        yaml_lines = tpl + [
            "    prefix_not_present_in_as_set:",
            "      std: '0:0'",
            "    do_not_announce_to_peer:",
            "      std: '0:peer_as'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err()

        # Same as above, but with 'rs_as' in the prefix_not_present_in_as_set comm.
        # No errors because 'peer_as' can't be the route server's ASN itself.
        yaml_lines = tpl + [
            "    prefix_not_present_in_as_set:",
            "      std: '0:rs_as'",
            "    do_not_announce_to_peer:",
            "      std: '0:peer_as'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err()

        # Same as above, but with a private ASN in the prefix_not_present_in_as_set comm.
        # No errors because 'peer_as' can't be a private ASN.
        yaml_lines = tpl + [
            "    prefix_not_present_in_as_set:",
            "      std: '0:65501'",
            "    do_not_announce_to_peer:",
            "      std: '0:peer_as'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err()

        # Testing with allow_private_asns=False...
        with self.assertRaises(ConfigError):
            self.cfg.check_overlapping_communities(allow_private_asns=False)
        exp_err_msg_found = False
        for line in self.logger_handler.msgs:
            if "Community 'do_not_announce_to_peer' and 'prefix_not_present_in_as_set' overlap: 0:peer_as / 0:65501. Inbound communities and outbound communities can't have overlapping values, otherwise they might be scrubbed." in line:
                exp_err_msg_found = True
                break

        if not exp_err_msg_found:
            self.fail("Expected error message not found")

    def test_overlapping_communities_in_in(self):
        """{}: overlapping communities, inbound/inbound"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  communities:"
        ]

        # blackholing: inbound
        # do_not_announce_to_peer: inbound
        yaml_lines = tpl + [
            "    blackholing:",
            "      std: '0:666'",
            "    do_not_announce_to_peer:",
            "      std: '0:peer_as'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Community 'blackholing' and 'do_not_announce_to_peer' overlap: 0:666 / 0:peer_as. Inbound communities can't have overlapping values, otherwise their meaning could be uncertain.")

        # Same as above, but with 0 in the last part of blackholing
        # No errors because 'peer_as' can't be 0.
        yaml_lines = tpl + [
            "    blackholing:",
            "      std: '0:0'",
            "    do_not_announce_to_peer:",
            "      std: '0:peer_as'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err()

        # Same as above, but with rs_as in the last part of blackholing
        # No errors because 'peer_as' can't be the route server's ASN itself.
        yaml_lines = tpl + [
            "    blackholing:",
            "      std: '0:rs_as'",
            "    do_not_announce_to_peer:",
            "      std: '0:peer_as'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err()

        # Same as above, but with a private ASN in the last part of
        # blackholing community.
        yaml_lines = tpl + [
            "    blackholing:",
            "      std: '0:65501'",
            "    do_not_announce_to_peer:",
            "      std: '0:peer_as'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err()

        # Testing with allow_private_asns=False...
        with self.assertRaises(ConfigError):
            self.cfg.check_overlapping_communities(allow_private_asns=False)
        exp_err_msg_found = False
        for line in self.logger_handler.msgs:
            if "Community 'blackholing' and 'do_not_announce_to_peer' overlap: 0:65501 / 0:peer_as. Inbound communities can't have overlapping values, otherwise" in line:
                exp_err_msg_found = True
                break

        if not exp_err_msg_found:
            self.fail("Expected error message not found")

    def test_overlapping_communities_in_cust(self):
        """{}: overlapping communities, inbound/custom"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  communities:"
        ]

        # Custom community overlaps
        yaml_lines = tpl + [
            "    do_not_announce_to_peer:",
            "      std: '1:peer_as'",
            "  custom_communities:",
            "    test1:",
            "      std: '1:1'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Community 'do_not_announce_to_peer' and 'test1' overlap: 1:peer_as / 1:1. Inbound communities and custom communities can't have overlapping values, otherwise they might be scrubbed.")

        # Private ASNs
        yaml_lines = tpl + [
            "    do_not_announce_to_peer:",
            "      std: '1:peer_as'",
            "  custom_communities:",
            "    test1:",
            "      std: '1:65501'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err()

        # Testing with allow_private_asns=False...
        with self.assertRaises(ConfigError):
            self.cfg.check_overlapping_communities(allow_private_asns=False)
        exp_err_msg_found = False
        for line in self.logger_handler.msgs:
            if "Community 'do_not_announce_to_peer' and 'test1' overlap: 1:peer_as / 1:65501. Inbound communities and custom communities can't have overlapping values, otherwise they might be scrubbed." in line:
                exp_err_msg_found = True
                break

        if not exp_err_msg_found:
            self.fail("Expected error message not found")

    def test_max_pref_action(self):
        """{}: max_prefix action"""
        self.assertEqual(self.cfg["filtering"]["max_prefix"]["action"], None)
        self._test_option(self.cfg["filtering"]["max_prefix"], "action", ("shutdown", "restart", "block", "warning"))
        self._test_optional(self.cfg["filtering"]["max_prefix"], "action")

    def test_max_pref_peeringdb(self):
        """{}: max_prefix PeeringDB"""
        self.assertEqual(self.cfg["filtering"]["max_prefix"]["peering_db"], True)
        self._test_bool_val(self.cfg["filtering"]["max_prefix"], "peering_db")
        self._test_optional(self.cfg["filtering"]["max_prefix"], "peering_db")

    def test_max_pref_general_limit_ipv4(self):
        """{}: max_prefix general_limit_ipv4"""
        self.assertEqual(self.cfg["filtering"]["max_prefix"]["general_limit_ipv4"], 170000)
        self._test_optional(self.cfg["filtering"]["max_prefix"], "general_limit_ipv4")

    def test_max_pref_general_limit_ipv6(self):
        """{}: max_prefix general_limit_ipv6"""
        self.assertEqual(self.cfg["filtering"]["max_prefix"]["general_limit_ipv6"], 12000)
        self._test_optional(self.cfg["filtering"]["max_prefix"], "general_limit_ipv6")

    def test_transit_free_action(self):
        """{}: transit free, action"""
        self.assertEqual(self.cfg["filtering"]["transit_free"]["action"], None)
        self._test_option(self.cfg["filtering"]["transit_free"], "action", ("reject", "warning"))
        self._test_optional(self.cfg["filtering"]["transit_free"], "action")

    def test_transit_free_asns(self):
        """{}: transit free, ASNs list"""
        self.assertEqual(self.cfg["filtering"]["transit_free"]["asns"], [174, 209, 286, 701, 1239, 1299, 2828, 2914, 3257, 3320, 3356, 3549, 5511, 6453, 6461, 6762, 6830, 7018, 12956])
        self._test_optional(self.cfg["filtering"]["transit_free"], "asns")

        cfg = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  filtering:",
            "    transit_free:",
        ]
        self.load_config(yaml="\n".join(cfg + [
            "      action: reject"
        ]))
        self._contains_err()
        self.assertEqual(self.cfg["filtering"]["transit_free"]["action"], "reject")

        self.load_config(yaml="\n".join(cfg + [
            "      action: test"
        ]))
        self._contains_err("Error parsing 'action' at 'cfg.filtering.transit_free' level - Invalid option for 'action':")

        self.load_config(yaml="\n".join(cfg + [
            "      action: reject",
            "      asns: '1, 2, 3, 4'"
        ]))
        self._contains_err()
        self.assertEqual(self.cfg["filtering"]["transit_free"]["action"], "reject")
        self.assertEqual(self.cfg["filtering"]["transit_free"]["asns"], [1,2,3,4])

        self.load_config(yaml="\n".join(cfg + [
            "      action: reject",
            "      asns: '1, 2, 3, 4a'"
        ]))
        self._contains_err("Error parsing 'asns' at 'cfg.filtering.transit_free' level - Invalid ASN:  4a.")

    def test_default_values(self):
        """{}: minimal config"""
        self.load_config(yaml="cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2"
        )
        self.cfg.parse()
        self._contains_err()

        exp_res = {
            "rs_as": 999,
            "router_id": "192.0.2.2",
            "prepend_rs_as": False,
            "path_hiding": True,
            "passive": True,
            "gtsm": False,
            "add_path": False,
            "filtering": {
                "next_hop": {
                    "policy": "strict"
                },
                "global_black_list_pref": None,
                "ipv4_pref_len": {
                    "min": 8,
                    "max": 24
                },
                "ipv6_pref_len": {
                    "min": 12,
                    "max": 48
                },
                "max_as_path_len": 32,
                "reject_invalid_as_in_as_path": True,
                "reject_policy": {
                    "policy": "reject"
                },
                "transit_free": {
                    "action": None,
                    "asns": None
                },
                "irrdb": {
                    "tag_as_set": True,
                    "enforce_origin_in_as_set": True,
                    "enforce_prefix_in_as_set": True,
                    "allow_longer_prefixes": False
                },
                "rpki": {
                    "enabled": False,
                    "reject_invalid": True,
                },
                "max_prefix": {
                    "action": None,
                    "restart_after": 15,
                    "peering_db": True,
                    "general_limit_ipv4": 170000,
                    "general_limit_ipv6": 12000
                },
            },
            "blackhole_filtering": {
                "policy_ipv4": None,
                "policy_ipv6": None,
                "rewrite_next_hop_ipv4": None,
                "rewrite_next_hop_ipv6": None,
                "announce_to_client": True,
                "add_noexport": True,
            }
        }

        self.maxDiff = None
        del self.cfg["communities"]
        del self.cfg["custom_communities"]
        self.assertMultiLineEqual(
            yaml.safe_dump(self.cfg.cfg, default_flow_style=False),
            yaml.safe_dump({"cfg": exp_res}, default_flow_style=False)
        )

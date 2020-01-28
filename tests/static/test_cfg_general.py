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

try:
    import mock
except ImportError:
    import unittest.mock as mock
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

    def test_next_hop_policy_pre_0_6_0(self):
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

    def test_use_rpki_roas_as_route_objects_enabled(self):
        """{}: use_rpki_roas_as_route_objects.enabled"""
        self.assertEqual(self.cfg["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]["enabled"], False)
        self._test_bool_val(self.cfg["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"], "enabled")
        self._test_mandatory(self.cfg["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"], "enabled", has_default=True)

    def test_use_rpki_roas_source(self):
        """{}: rpki_roas.source"""
        self.assertEqual(self.cfg["rpki_roas"]["source"], "ripe-rpki-validator-cache")
        self._test_option(self.cfg["rpki_roas"], "source", ("ripe-rpki-validator-cache","rtr"))
        self._test_mandatory(self.cfg["rpki_roas"], "source", has_default=True)

    def use_arin_whois_db_dump_enabled(self):
        """{}: use_arin_whois_db_dump.enabled"""
        self.assertEqual(self.cfg["filtering"]["irrdb"]["use_arin_whois_db_dump"]["enabled"], False)
        self._test_bool_val(self.cfg["filtering"]["irrdb"]["use_arin_whois_db_dump"], "enabled")
        self._test_mandatory(self.cfg["filtering"]["irrdb"]["use_arin_whois_db_dump"], "enabled", has_default=True)

    def use_registrobr_whois_db_dump_enabled(self):
        """{}: use_registrobr_whois_db_dump.enabled"""
        self.assertEqual(self.cfg["filtering"]["irrdb"]["use_registrobr_whois_db_dump"]["enabled"], False)
        self._test_bool_val(self.cfg["filtering"]["irrdb"]["use_registrobr_whois_db_dump"], "enabled")
        self._test_mandatory(self.cfg["filtering"]["irrdb"]["use_registrobr_whois_db_dump"], "enabled", has_default=True)

    def test_rpki_enabled(self):
        """{}: rpki_bgp_origin_validation, enabled"""
        self.assertEqual(self.cfg["filtering"]["rpki_bgp_origin_validation"]["enabled"], False)
        self._test_bool_val(self.cfg["filtering"]["rpki_bgp_origin_validation"], "enabled")
        self._test_mandatory(self.cfg["filtering"]["rpki_bgp_origin_validation"], "enabled", has_default=True)

    def test_rpki_reject_invalid(self):
        """{}: rpki_bgp_origin_validation, reject_invalid"""
        self.assertEqual(self.cfg["filtering"]["rpki_bgp_origin_validation"]["reject_invalid"], True)
        self._test_bool_val(self.cfg["filtering"]["rpki_bgp_origin_validation"], "reject_invalid")
        self._test_optional(self.cfg["filtering"]["rpki_bgp_origin_validation"], "reject_invalid")

    def test_reject_policy(self):
        """{}: reject_policy"""
        self.assertEqual(self.cfg["filtering"]["reject_policy"]["policy"], "reject")
        self._contains_err()

        self.cfg["communities"]["reject_cause"]["std"] = "65520:dyn_val"
        self.cfg["filtering"]["reject_policy"]["policy"] = "tag"
        self._contains_err()

        del self.cfg["communities"]["reject_cause"]["std"]
        self.cfg["filtering"]["reject_policy"]["policy"] = "tag"
        self._contains_err("The 'reject_cause' community must be configured when 'reject_policy.policy' is 'tag'.")

        self._test_option(self.cfg["filtering"]["reject_policy"], "policy", ())

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

    def test_graceful_shutdown(self):
        """{}: graceful shutdown"""
        self.assertEqual(self.cfg["graceful_shutdown"]["enabled"], False)
        self._test_bool_val(self.cfg["graceful_shutdown"], "enabled")

    def test_rfc1997_wellknown_communities(self):
        """{}: RFC1997 well-known communities"""
        self.assertEqual(self.cfg["rfc1997_wellknown_communities"]["policy"], "pass")
        self._test_option(self.cfg["rfc1997_wellknown_communities"], "policy", ("rfc1997", "pass"))

    def test_rtt_thresholds_str(self):
        """{}: RTT thresholds as comma separated string"""
        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  rtt_thresholds: '1, 2, 3'"
        )
        self._contains_err()

    def test_rtt_thresholds_int(self):
        """{}: RTT thresholds as list of int"""
        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  rtt_thresholds: 1, 2, 3"
        )
        self._contains_err()

    def test_rtt_thresholds_empty(self):
        """{}: RTT thresholds, empty"""

        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  rtt_thresholds: "
        )
        self._contains_err()

    def test_rtt_thresholds_invalid(self):
        """{}: RTT thresholds, invalid values"""
        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  rtt_thresholds: 1, 2a, 3"
        )
        self._contains_err("RTT thresholds list items must be positive integers:  2a")

    def test_rtt_thresholds_order(self):
        """{}: RTT thresholds, out of order"""
        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  rtt_thresholds: 3, 2, 1"
        )
        self._contains_err("RTT thresholds list items must be provided in ascending order: 2 < 3")

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

        for comm in ("reject_cause", "rejected_route_announced_by",
                     "do_not_announce_to_peers_with_rtt_lower_than",
                     "do_not_announce_to_peers_with_rtt_higher_than",
                     "announce_to_peers_with_rtt_lower_than",
                     "announce_to_peers_with_rtt_higher_than",
                     "prepend_once_to_peers_with_rtt_lower_than",
                     "prepend_twice_to_peers_with_rtt_lower_than",
                     "prepend_thrice_to_peers_with_rtt_lower_than",
                     "prepend_once_to_peers_with_rtt_higher_than",
                     "prepend_twice_to_peers_with_rtt_higher_than",
                     "prepend_thrice_to_peers_with_rtt_higher_than"):
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

    def test_rejected_route_announced_by_with_no_reject_policy(self):
        """{}: rejected_route_announced_by can be set only with 'tag' reject_policy"""
        self.cfg["communities"]["reject_cause"]["std"] = "65520:dyn_val"
        self.cfg["communities"]["rejected_route_announced_by"]["std"] = "0:dyn_val"
        self._contains_err("The 'rejected_route_announced_by' community can be set only if 'reject_policy.policy' is 'tag'.")

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
        # It must work, peer_as can't be a private ASN; moreover
        # also on OpenBGPD (where inbound communities are scrubbed
        # using a wildcard) when the 'x:peer_as' community is
        # deleted also the 'x:<asn>' is.
        self.cfg.check_overlapping_communities(allow_private_asns=False)
        self._contains_err()

    def test_overlapping_communities_in_in_dyn_val(self):
        """{}: overlapping communities, inbound/inbound (dyn_val)"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  communities:"
        ]

        # blackholing: inbound
        # do_not_announce_to_peers_with_rtt_lower_than: inbound with dyn_val
        yaml_lines = tpl + [
            "    blackholing:",
            "      std: '0:666'",
            "    do_not_announce_to_peers_with_rtt_lower_than:",
            "      std: '0:dyn_val'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Community 'blackholing' and 'do_not_announce_to_peers_with_rtt_lower_than' overlap: 0:666 / 0:dyn_val. Inbound communities can't have overlapping values, otherwise their meaning could be uncertain.")

        # do_not_announce_to_peer: inbound with peer_as
        # do_not_announce_to_peers_with_rtt_lower_than: inbound with dyn_val
        yaml_lines = tpl + [
            "    do_not_announce_to_peer:",
            "      std: '0:peer_as'",
            "    do_not_announce_to_peers_with_rtt_lower_than:",
            "      std: '0:dyn_val'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Community 'do_not_announce_to_peer' and 'do_not_announce_to_peers_with_rtt_lower_than' overlap: 0:peer_as / 0:dyn_val. Inbound communities can't have overlapping values, otherwise their meaning could be uncertain.")

    def test_overlapping_communities_out_in_dyn_val(self):
        """{}: overlapping communities, outbound/inbound (dyn_val)"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  communities:"
        ]

        # prefix_not_present_in_as_set: outbound
        # do_not_announce_to_peers_with_rtt_lower_than: inbound with dyn_val
        yaml_lines = tpl + [
            "    prefix_not_present_in_as_set:",
            "      std: '0:1'",
            "    do_not_announce_to_peers_with_rtt_lower_than:",
            "      std: '0:dyn_val'"
        ]
        self.load_config(yaml="\n".join(yaml_lines))
        self._contains_err("Community 'do_not_announce_to_peers_with_rtt_lower_than' and 'prefix_not_present_in_as_set' overlap: 0:dyn_val / 0:1. Inbound communities and outbound communities can't have overlapping values, otherwise they might be scrubbed.")

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

    def test_rtt_based_communities_without_rtt_thresholds(self):
        """{}: RTT-based communities without RTT thresholds"""
        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  communities:",
            "    do_not_announce_to_peers_with_rtt_lower_than:",
            "      std: '0:dyn_val'"
        ]
        self.load_config(yaml="\n".join(tpl))
        self._contains_err("Some RTT-based functions are configured but the RTT thresholds list is empty.")

        tpl = [
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  rtt_thresholds: 1, 2",
            "  communities:",
            "    do_not_announce_to_peers_with_rtt_lower_than:",
            "      std: '0:dyn_val'"
        ]
        self.load_config(yaml="\n".join(tpl))
        self._contains_err()

    def test_max_pref_action(self):
        """{}: max_prefix action"""
        self.assertEqual(self.cfg["filtering"]["max_prefix"]["action"], None)
        self._test_option(self.cfg["filtering"]["max_prefix"], "action", ("shutdown", "restart", "block", "warning"))
        self._test_optional(self.cfg["filtering"]["max_prefix"], "action")

    def test_max_pref_peeringdb(self):
        """{}: max_prefix PeeringDB"""
        self.assertEqual(self.cfg["filtering"]["max_prefix"]["peering_db"], {
            "enabled": True,
            "increment": {
                "absolute": 100,
                "relative": 15
            }
        })
        self._test_bool_val(self.cfg["filtering"]["max_prefix"]["peering_db"], "enabled")
        self._test_optional(self.cfg["filtering"]["max_prefix"]["peering_db"], "enabled")

    def test_max_pref_peeringdb_pre_0_13_0(self):
        """{}: max_prefix PeeringDB (pre v0.13.0 format)"""

        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  filtering:\n"
            "    max_prefix:\n"
            "      peering_db: True\n"
        )
        self.cfg.parse()
        self._contains_err()

        self.assertEqual(self.cfg["filtering"]["max_prefix"]["peering_db"]["enabled"], True)
        self.assertEqual(self.cfg["filtering"]["max_prefix"]["peering_db"]["increment"]["absolute"], 100)
        self.assertEqual(self.cfg["filtering"]["max_prefix"]["peering_db"]["increment"]["relative"], 15)

        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: 192.0.2.2\n"
            "  filtering:\n"
            "    max_prefix:\n"
            "      peering_db: False\n"
        )
        self.cfg.parse()
        self._contains_err()

        self.assertEqual(self.cfg["filtering"]["max_prefix"]["peering_db"]["enabled"], False)

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

    def test_never_via_route_servers_peering_db(self):
        """{}: never via route-servers, peering_db"""
        self.assertEqual(self.cfg["filtering"]["never_via_route_servers"]["peering_db"], True)
        self._test_bool_val(self.cfg["filtering"]["never_via_route_servers"], "peering_db")

    def test_never_via_route_servers_asns(self):
        """{}: never via route-servers, asns"""
        self.assertEqual(self.cfg["filtering"]["never_via_route_servers"]["asns"], None)
        self._test_optional(self.cfg["filtering"]["never_via_route_servers"], "asns")

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
                "never_via_route_servers": {
                    "peering_db": True,
                    "asns": None
                },
                "irrdb": {
                    "tag_as_set": True,
                    "enforce_origin_in_as_set": True,
                    "enforce_prefix_in_as_set": True,
                    "allow_longer_prefixes": False,
                    "peering_db": False,
                    "use_rpki_roas_as_route_objects": {
                        "enabled": False,
                    },
                    "use_arin_bulk_whois_data": {
                        "enabled": False,
                        "source": "http://irrexplorer.nlnog.net/static/dumps/arin-whois-originas.json.bz2"
                    },
                    "use_registrobr_bulk_whois_data": {
                        "enabled": False,
                        "source": "ftp://ftp.registro.br/pub/numeracao/origin/nicbr-asn-blk-latest.txt"
                    },
                },
                "rpki_bgp_origin_validation": {
                    "enabled": False,
                    "reject_invalid": True,
                },
                "max_prefix": {
                    "action": None,
                    "restart_after": 15,
                    "peering_db": {
                        "enabled": True,
                        "increment": {
                            "absolute": 100,
                            "relative": 15
                        }
                    },
                    "general_limit_ipv4": 170000,
                    "general_limit_ipv6": 12000
                },
            },
            "rtt_thresholds": None,
            "rpki_roas": {
                "source": "ripe-rpki-validator-cache",
                "ripe_rpki_validator_url": [
                    "https://rpki-validator.ripe.net/api/export.json",
                    "https://rpki.gin.ntt.net/api/export.json"
                ],
                "allowed_trust_anchors": [
                    "APNIC RPKI Root",
                    "AfriNIC RPKI Root",
                    "LACNIC RPKI Root",
                    "RIPE NCC RPKI Root",
                    "apnic",
                    "afrinic",
                    "lacnic",
                    "ripe"
                ]
            },
            "blackhole_filtering": {
                "policy_ipv4": None,
                "policy_ipv6": None,
                "rewrite_next_hop_ipv4": None,
                "rewrite_next_hop_ipv6": None,
                "announce_to_client": True,
                "add_noexport": True,
            },
            "graceful_shutdown": {
                "enabled": False,
                "local_pref": 0
            },
            "rfc1997_wellknown_communities": {
                "policy": "pass"
            }
        }

        self.maxDiff = None
        del self.cfg["communities"]
        del self.cfg["custom_communities"]
        self.assertMultiLineEqual(
            yaml.safe_dump(self.cfg.cfg, default_flow_style=False),
            yaml.safe_dump({"cfg": exp_res}, default_flow_style=False)
        )

    def test_distrib_config(self):
        """{}: distributed config"""
        self.load_config(file_name="config.d/general.yml")
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
                    "asns": [174, 209, 286, 701, 1239, 1299, 2828, 2914, 3257, 3320, 3356, 3549, 5511, 6453, 6461, 6762, 6830, 7018, 12956]
                },
                "never_via_route_servers": {
                    "peering_db": True,
                    "asns": None
                },
                "irrdb": {
                    "tag_as_set": True,
                    "enforce_origin_in_as_set": True,
                    "enforce_prefix_in_as_set": True,
                    "allow_longer_prefixes": False,
                    "peering_db": False,
                    "use_rpki_roas_as_route_objects": {
                        "enabled": False,
                    },
                    "use_arin_bulk_whois_data": {
                        "enabled": False,
                        "source": "http://irrexplorer.nlnog.net/static/dumps/arin-whois-originas.json.bz2"
                    },
                    "use_registrobr_bulk_whois_data": {
                        "enabled": False,
                        "source": "ftp://ftp.registro.br/pub/numeracao/origin/nicbr-asn-blk-latest.txt"
                    }
                },
                "rpki_bgp_origin_validation": {
                    "enabled": False,
                    "reject_invalid": True,
                },
                "max_prefix": {
                    "action": None,
                    "restart_after": 15,
                    "peering_db": {
                        "enabled": True,
                        "increment": {
                            "absolute": 100,
                            "relative": 15
                        }
                    },
                    "general_limit_ipv4": 170000,
                    "general_limit_ipv6": 12000
                },
            },
            "rtt_thresholds": [5, 10, 15, 20, 30, 50, 100, 200, 500],
            "rpki_roas": {
                "source": "ripe-rpki-validator-cache",
                "ripe_rpki_validator_url": [
                    "https://rpki-validator.ripe.net/api/export.json",
                    "https://rpki.gin.ntt.net/api/export.json"
                ],
                "allowed_trust_anchors": [
                    "APNIC RPKI Root",
                    "AfriNIC RPKI Root",
                    "LACNIC RPKI Root",
                    "RIPE NCC RPKI Root",
                    "apnic",
                    "afrinic",
                    "lacnic",
                    "ripe"
                ]
            },
            "blackhole_filtering": {
                "policy_ipv4": None,
                "policy_ipv6": None,
                "rewrite_next_hop_ipv4": None,
                "rewrite_next_hop_ipv6": None,
                "announce_to_client": True,
                "add_noexport": True,
            },
            "graceful_shutdown": {
                "enabled": False,
                "local_pref": 0
            },
            "rfc1997_wellknown_communities": {
                "policy": "pass"
            }
        }

        self.maxDiff = None
        del self.cfg["communities"]
        del self.cfg["custom_communities"]
        self.assertMultiLineEqual(
            yaml.safe_dump(self.cfg.cfg, default_flow_style=False),
            yaml.safe_dump({"cfg": exp_res}, default_flow_style=False)
        )

    def test_deprecated_rpki_validation(self):
        """{}: deprecated syntax, RPKI Origin Validation"""
        cfg = {
            "cfg": {
                "rs_as": 999,
                "router_id": "192.0.2.2",
                "filtering": {
                    "rpki": {
                        "enabled": True
                    }
                }
            }
        }
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err()
        self.assertEqual(self.cfg.cfg["cfg"]["filtering"]["rpki_bgp_origin_validation"]["enabled"], True)

        cfg["cfg"]["filtering"]["rpki_bgp_origin_validation"] = {}
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err("A conflict due to a deprecated syntax exists: filtering.rpki and filtering.rpki_bgp_origin_validation are both configured.")

    def test_deprecated_ripe_rpki_validator_url(self):
        """{}: deprecated syntax, RPKI ROAs cache - multiple URLs"""
        cfg = {
            "cfg": {
                "rs_as": 999,
                "router_id": "192.0.2.2",
                "rpki_roas": {
                    "ripe_rpki_validator_url": "Foo"
                }
            }
        }
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err()
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["source"], "ripe-rpki-validator-cache")
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["ripe_rpki_validator_url"], ["Foo"])

    def test_deprecated_rpki_roas_source_rtrlib(self):
        """{}: deprecated syntax, RPKI ROAs source: rtrlib"""
        cfg = {
            "cfg": {
                "rs_as": 999,
                "router_id": "192.0.2.2",
                "filtering": {
                    "irrdb": {
                        "use_rpki_roas_as_route_objects": {
                            "enabled": True
                        }
                    },
                },
                "rpki_roas": {
                    "source": "rtrlib"
                }
            }
        }
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err()
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["source"], "rtr")

    def test_deprecated_rpki_roas_source(self):
        """{}: deprecated syntax, RPKI ROAs source"""
        cfg = {
            "cfg": {
                "rs_as": 999,
                "router_id": "192.0.2.2",
                "filtering": {
                    "irrdb": {
                        "use_rpki_roas_as_route_objects": {
                            "enabled": True
                        }
                    },
                    "rpki": {
                        "enabled": True
                    }
                }
            }
        }
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err()
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["source"], "rtr")

        cfg["cfg"]["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]["source"] = "ripe-rpki-validator-cache"
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err("A deprecated syntax triggered an issue with the configuration of RPKI BGP Origin Validation (filtering.rpki) and ROAs-as-route-objects (filtering.irrdb.rpki_roas_as_route_objects). The former uses RTR as source for ROAs, while the latter is configured to use the RIPE RPKI Validator")

        del cfg["cfg"]["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]["source"]
        cfg["cfg"]["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]["enabled"] = False
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err()
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["source"], "rtr")

        cfg["cfg"]["filtering"]["rpki"]["enabled"] = False
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err()
        self.assertTrue("rpki_roas" not in self.cfg.cfg)

        cfg["cfg"]["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]["enabled"] = True
        cfg["cfg"]["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]["source"] = "ripe-rpki-validator-cache"
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err()
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["source"], "ripe-rpki-validator-cache")

        cfg["cfg"]["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]["ripe_rpki_validator_url"] = "Foo"
        cfg["cfg"]["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]["allowed_trust_anchors"] = ["bar"]
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err()
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["source"], "ripe-rpki-validator-cache")
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["ripe_rpki_validator_url"], ["Foo"])
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["allowed_trust_anchors"], ["bar"])

        cfg["cfg"]["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]["ripe_rpki_validator_url"] = ["Foo", "Bar"]
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err()
        self.assertEqual(self.cfg.cfg["cfg"]["rpki_roas"]["ripe_rpki_validator_url"], ["Foo", "Bar"])

        cfg["cfg"]["rpki_roas"] = {}
        self.load_config(yaml=yaml.dump(cfg))
        self._contains_err("A conflict due to a deprecated syntax exists: please check rpki_roas, filtering.rpki and filtering.irrdb.rpki_roas_as_route_objects.")

    @mock.patch.dict(os.environ, {"ROUTER_ID": "192.0.2.1"})
    def test_env_vars_ok(self):
        """{}: environment variables: ok"""

        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: ${ROUTER_ID}\n"
        )
        self.cfg.parse()
        self._contains_err()

        self.assertEqual(self.cfg["router_id"], "192.0.2.1")

    @mock.patch.dict(os.environ, {"ROUTER_ID": "192.0.2.1"})
    def test_env_vars_missing(self):
        """{}: environment variables: ok"""

        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: ${ROUTER_ID}\n"
            "  filtering:\n"
            "    global_black_list_pref: ${GLOBAL_BLACK_LIST_PREF}\n"
        )
        self.cfg.parse()
        self._contains_err()

        self.assertEqual(self.cfg["router_id"], "192.0.2.1")
        self.assertEqual(self.cfg["filtering"]["global_black_list_pref"], None)

    @mock.patch.dict(os.environ, {"ROUTER_ID": "192.0.2.1"})
    def test_env_vars_corrupted(self):
        """{}: environment variables: corrupted"""

        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: ${ROUTER_ID\n"
        )
        self._contains_err("Invalid IPv4 address: ${ROUTER_ID")

    @mock.patch.dict(os.environ, {"ROUTER_ID": "192.0.2.1", "BAD_ESCAPE": r"\u"})
    def test_env_vars_bad_escape(self):
        """{}: environment variables: ok (bad escape)"""

        self.cfg._load_from_yaml(
            "cfg:\n"
            "  rs_as: 999\n"
            "  router_id: ${ROUTER_ID}\n"
            "  filtering:\n"
            "    global_black_list_pref: ${GLOBAL_BLACK_LIST_PREF}\n"
        )
        self.cfg.parse()
        self._contains_err()

        self.assertEqual(self.cfg["router_id"], "192.0.2.1")
        self.assertEqual(self.cfg["filtering"]["global_black_list_pref"], None)

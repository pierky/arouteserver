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

import logging

from .base import ConfigParserBase
from .validators import *
from ..errors import ConfigError, ARouteServerError


class ConfigParserGeneral(ConfigParserBase):

    ROOT = "cfg"

    COMMUNITIES_SCHEMA = {
        "origin_present_in_as_set": { "type": "outbound" },
        "origin_not_present_in_as_set": { "type": "outbound" },
        "prefix_present_in_as_set": { "type": "outbound" },
        "prefix_not_present_in_as_set": { "type": "outbound" },
        "roa_valid": { "type": "outbound" },
        "roa_invalid": { "type": "outbound" },
        "roa_unknown": { "type": "outbound" },

        "blackholing": { "type": "inbound" },
        "do_not_announce_to_any": { "type": "inbound" },
        "do_not_announce_to_peer": { "type": "inbound", "peer_as": True },
        "announce_to_peer": { "type": "inbound", "peer_as": True },
        "prepend_once_to_any": { "type": "inbound" },
        "prepend_twice_to_any": { "type": "inbound" },
        "prepend_thrice_to_any": { "type": "inbound" },
    }

    def parse(self):
        """
        Contents of cfg dict is updated/normalized by validators.
        """

        errors = False

        schema = {
            "cfg": {
                "rs_as": ValidatorASN(),
                "router_id": ValidatorIPv4Addr(mandatory=True),
                "prepend_rs_as": ValidatorBool(default=False),                      # Done
                "path_hiding": ValidatorBool(default=True),                         # Done, not tested
                "passive": ValidatorBool(default=True),                             # Done
                "gtsm": ValidatorBool(default=False),
                "add_path": ValidatorBool(default=False),                           # Done
                "filtering": {
                    "next_hop_policy": ValidatorOption("next_hop_policy",
                                                       ("strict", "same-as"),
                                                       default="strict"),           # Done
                    "ipv4_pref_len": ValidatorIPMinMaxLen(4,
                                                          default={"min": 8,
                                                                   "max": 24}),     # Done
                    "ipv6_pref_len": ValidatorIPMinMaxLen(6,
                                                          default={"min": 12,
                                                                   "max": 48}),     # Done, not tested
                    "global_black_list_pref": ValidatorListOf(
                        ValidatorPrefixListEntry, mandatory=False,
                    ),                                                              # Done
                    "max_as_path_len": ValidatorMaxASPathLen(default=32),           # Done
                    "reject_invalid_as_in_as_path": ValidatorBool(default=True),    # Done
                    "transit_free": {
                        "action": ValidatorOption("action",
                                                  ("reject", "warning"),
                                                  mandatory=False,
                                                  default="reject"),
                        "asns": ValidatorASNList(mandatory=False)
                    },
                    "rpsl": {
                        "enforce_origin_in_as_set": ValidatorBool(default=True),    # Done
                        "enforce_prefix_in_as_set": ValidatorBool(default=True),    # Done
                        "tag_as_set": ValidatorBool(default=True)                   # Done
                    },
                    "rpki": {
                        "enabled": ValidatorBool(default=False),                    # MISSING
                        "reject_invalid": ValidatorBool(mandatory=True,
                                                        default=True),              # MISSING
                    },
                    "max_prefix": {                                                 # MISSING
                        "peering_db": ValidatorBool(default=True),
                        "general_limit_ipv4": ValidatorUInt(default=170000),
                        "general_limit_ipv6": ValidatorUInt(default=12000),
                        "action": ValidatorOption(
                            "action",
                            ("shutdown", "restart", "block", "warning"),
                            mandatory=False,
                            default="shutdown"
                        )
                    },
                },
                "blackhole_filtering": {                                        # Done
                    "announce_to_client": ValidatorBool(                        # Done
                        mandatory=True, default=True
                    ),
                    "policy_ipv4": ValidatorOption(                             # Done
                        "policy_ipv4",
                        ("propagate-unchanged", "rewrite-next-hop"),
                        mandatory=False),
                    "policy_ipv6": ValidatorOption(                             # Done, not tested
                        "policy_ipv6",
                        ("propagate-unchanged", "rewrite-next-hop"),
                        mandatory=False),
                    "rewrite_next_hop_ipv4": ValidatorIPv4Addr(mandatory=False),# Done
                    "rewrite_next_hop_ipv6": ValidatorIPv6Addr(mandatory=False),# Done, not tested
                },
                "control_communities": ValidatorBool(default=True),                 # Done
                "communities": {
                }
            }
        }

        if "rs_as" in self.cfg["cfg"]:
            rs_as_macro = self.cfg["cfg"]["rs_as"]
        else:
            rs_as_macro = None

        for comm in self.COMMUNITIES_SCHEMA:
            peer_as = self.COMMUNITIES_SCHEMA[comm].get("peer_as", False)

            schema["cfg"]["communities"][comm] = {
                "std": ValidatorCommunityStd(rs_as_macro, mandatory=False,
                                             peer_as_macro_needed=peer_as),
                "lrg": ValidatorCommunityLrg(rs_as_macro, mandatory=False,
                                             peer_as_macro_needed=peer_as),
                "ext": ValidatorCommunityExt(rs_as_macro, mandatory=False,
                                             peer_as_macro_needed=peer_as),
            }

        try:
            ConfigParserBase.validate(schema, self.cfg)
        except ARouteServerError as e:
            errors = True
            if str(e):
                logging.error(str(e))
            raise ConfigError()

        # Warning: missing global black list.
        if not self.cfg["cfg"]["filtering"].get("global_black_list_pref"):
            logging.warning("The 'filtering.global_black_list_pref' option is "
                            "missing or empty. It is strongly suggested to "
                            "provide at least the list of local IPv4/IPv6 "
                            "networks here.")

        # If blackhole filtering policy = "rewrite-next-hop", then
        # blackhole next-hops must be provided.
        for ip_ver in (4, 6):
            bh = self.cfg["cfg"]["blackhole_filtering"]
            if not bh:
                continue
            policy = bh["policy_ipv{}".format(ip_ver)]
            if policy == "rewrite-next-hop":
                if not bh["rewrite_next_hop_ipv{}".format(ip_ver)]:
                    errors = True
                    logging.error(
                        "Since blackhole_filtering.policy_ipv{v} is "
                        "'rewrite_next_hop', an IPv{v} address must "
                        "be provided in "
                        "'rewrite_next_hop_ipv{v}'.".format(
                            v=ip_ver
                        )
                    )

        # Duplicate communities?
        unique_communities = []
        for comm_tag in self.cfg["cfg"]["communities"]:
            comm = self.cfg["cfg"]["communities"][comm_tag]
            for fmt in ("std", "lrg", "ext"):
                if comm[fmt]:
                    if comm[fmt] in unique_communities:
                        errors = True
                        logging.error(
                            "The '{}.{}' community's value ({}) "
                            "has already been used for another "
                            "community.".format(comm_tag, fmt, comm[fmt])
                        )
                    else:
                        unique_communities.append(comm[fmt])

        # Overlapping communities?
        #TODO: improve! When peer_as matches a value in the
        # range 64512..65534 / 4200000000..4294967294 it
        # should be fine, because a peer's ASN can't be in that
        # range. It should be tuned on the communities scrubbing
        # functions on BIRD templates too.

        def communities_overlap(communities, comm1_tag, comm2_tag,
                                allow_private_asns=False):
            comm1 = communities[comm1_tag]
            comm2 = communities[comm2_tag]
            rs_as = self.cfg["cfg"]["rs_as"]

            err_msg = ("Community '{comm1_tag}' and '{comm2_tag}' "
                       "overlap: {comm1_val} / {comm2_val}.")

            for fmt in ("std", "lrg", "ext"):
                if not comm1[fmt]:
                    continue
                if not comm2[fmt]:
                    continue
                comm1_val = comm1[fmt]
                comm2_val = comm2[fmt]
                comm1_parts = comm1_val.split(":")
                comm2_parts = comm2_val.split(":")
                part_idx = 0
                for part_idx in range(len(comm1_parts)):
                    part1 = comm1_parts[part_idx]
                    part2 = comm2_parts[part_idx]
                    try:
                        not_peer_as = None
                        if part1 == "peer_as":
                            not_peer_as = int(part2)
                        if part2 == "peer_as":
                            not_peer_as = int(part1)
                        if not_peer_as is not None:
                            if not_peer_as == rs_as:
                                continue
                            if not_peer_as == 0:
                                continue
                            if allow_private_asns:
                                if not_peer_as >= 64512 and not_peer_as <= 65534:
                                    continue
                                if not_peer_as >= 4200000000 and not_peer_as <= 4294967294:
                                    continue
                            raise ConfigError()
                    except ConfigError:
                        raise ConfigError(err_msg.format(
                            comm1_tag=comm1_tag, comm2_tag=comm2_tag,
                            comm1_val=comm1_val, comm2_val=comm2_val)
                        )
                    if part1 != part2:
                        break

        outbound_communities = sorted(
            [c for c in self.COMMUNITIES_SCHEMA
             if self.COMMUNITIES_SCHEMA[c]["type"] == "outbound"]
        )
        inbound_communities = sorted(
            [c for c in self.COMMUNITIES_SCHEMA
             if self.COMMUNITIES_SCHEMA[c]["type"] == "inbound"]
        )

        for comm1_tag in inbound_communities:
            for comm2_tag in outbound_communities:
                if comm1_tag == comm2_tag:
                    continue
                try:
                    communities_overlap(
                        self.cfg["cfg"]["communities"], comm1_tag, comm2_tag
                    )
                except ConfigError as e:
                    errors = True
                    logging.error(str(e) + " " +
                        "Inbound communities and outbound communities "
                        "can't have overlapping values, otherwise they "
                        "might be scrubbed.")

        for comm1_tag in inbound_communities:
            for comm2_tag in inbound_communities:
                if comm1_tag == comm2_tag:
                    continue
                try:
                    communities_overlap(
                        self.cfg["cfg"]["communities"], comm1_tag, comm2_tag,
                        allow_private_asns=True
                    )
                except ConfigError as e:
                    errors = True
                    logging.error(str(e) + " " +
                        "Inbound communities can't have overlapping values, "
                        "otherwise their meaning could be uncertain.")

        if errors:
            raise ConfigError()

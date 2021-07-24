#!/usr/bin/env python

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

import sys
import re

RE_COMMENT = re.compile("^\s+#\s+([^\s].*)")
RE_COMMENT_EMPTY_LINE = re.compile("^\s+#\s*$")

class CfgStatement(object):

    def __init__(self, name, **kwargs):
        self.kwargs = kwargs

        self.name = name

        self.hide = kwargs.get("hide", False)

        self.statement_value = None
        self.commented = False
        self.keys = []
        self.title_description = kwargs.get("t", None)
        self.group = kwargs.get("g", None)
        self.body = None
        self.bullet_list = False

        self.pre_comment = kwargs.get("pre_comment", False)
        self.post_comment = kwargs.get("post_comment", False)

        self.previous_statement = None
        self.sub_statements = kwargs.get("sub", [])

        self.group_with_previous = kwargs.get("group_with_previous", None)

        self.statement_pattern = re.compile(
            kwargs.get("statement_pattern",
                       "^\s+(#?)({}):\s*(.*)$".format(self.name))
        )

    def debug(self, s):
        return
        print("{} - {}".format(self.name, s))

    def __repr__(self):
        return self.name

    def get_next_line(self):
        line = self.f.readline()
        if not line:
            raise ValueError("EOF")
        line = line.rstrip()
        return line

    def process_statement_cfg_line(self, line=None):
        match = self.statement_pattern.match(line or self.get_next_line())
        try:
            if not match:
                raise ValueError("Pattern not found, looking for {}".format(
                    self.statement_pattern.pattern
                ))
            if not match.group(2) == self.name:
                raise ValueError("'{}' expected, '{}' found".format(
                    self.name, match.group(2)
                ))
        except Exception as e:
            raise ValueError("Config statement mismatch: {}. "
                             "Processing line '{}'".format(str(e), line))

        self.commented = (match.group(1) == "#")

        self.statement_value = match.group(3)

        if self.name == "asns" and self.statement_value == ">":
            self.statement_value += "\n"
            self.statement_value += self.get_next_line() + "\n"
            self.statement_value += self.get_next_line() + "\n"
            self.statement_value += self.get_next_line() + "\n"
        elif self.name == "global_black_list_pref":
            self.statement_value += "\n"
            self.statement_value += self.get_next_line().replace("#", "") + "\n"
            self.statement_value += self.get_next_line().replace("#", "") + "\n"
            self.statement_value += self.get_next_line().replace("#", "") + "\n"

        self.debug("STATEMENT {}, COMMENTED {}".format(self.name, self.commented))
        return "STATEMENT {} {}".format(match.group(2), match.group(1) == "#")

    @staticmethod
    def expand_keys(keys):
        res = ""
        for key_idx in range(len(keys)):
            if key_idx > 0:
                if key_idx == len(keys) - 1:
                    res += " and "
                else:
                    res += ", "
            res += "``{}``".format(keys[key_idx])
        return res

    def build_result(self, indent_level):
        if self.hide:
            return ""

        if self.statement_value:
            self.body += "\n"
            self.body += "Example:\n"
            self.body += "\n"
            self.body += ".. code:: yaml\n"
            self.body += "\n"
            self.body += "   " + self.name + ": " + self.statement_value + "\n"
            self.body += "\n"

        lines = ["#", "-", "+", "~"]

        if self.title_description:
            res = self.title_description + ": " + self.expand_keys(self.keys) + "\n"
            res += (len(res) * lines[indent_level+1]) + "\n"
            res += "\n"
            res += self.body
        else:
            res = ""
            if self.group:
                res = self.group + "\n"
                res += (len(res) * lines[indent_level+1]) + "\n"
                res += "\n"

            res += "- {}".format(self.expand_keys(self.keys)) + ":\n"
            for line in self.body.split("\n"):
                if line.strip():
                    res += "  " + line + "\n"
                else:
                    res += "\n"

        if self.sub_statements:
            res += "\n"
            for sub_statement in self.sub_statements:
                if sub_statement.group_with_previous:
                    continue
                res += sub_statement.build_result(indent_level + 1) + "\n"

        return res

    def get_previous(self, name):
        if self.previous_statement.name == name:
            return self.previous_statement
        else:
            return self.previous_statement.get_previous(name)

    def parse(self, f):
        self.f = f

        self.keys = [self.name]
        self.body = ""

        self.debug("PARSE")

        if self.group_with_previous:
            if not self.previous_statement:
                raise ValueError("group_with_previous but no previous_statement")
            first_statement = self.get_previous(self.group_with_previous)
            first_statement.keys += [self.name]

        self.process_all()

        for sub_statement_idx in range(len(self.sub_statements)):
            if sub_statement_idx > 0:
                self.sub_statements[sub_statement_idx].previous_statement = self.sub_statements[sub_statement_idx - 1]

        for sub_statement in self.sub_statements:
            sub_statement.parse(f)

    def add_body_line(self, comment_raw):
        comment = comment_raw
        comment = re.sub("'([^\s]+)'", "**\\1**", comment)
        comment = re.sub("^Default: (.+)$", "Default: **\\1**", comment)

        if not comment.strip() and self.bullet_list:
            self.body += "\n\n"
            self.bullet_list = False
        elif comment.startswith("- "):
            self.body += "\n\n"
            self.bullet_list = True
            self.body += comment + "\n"
        elif self.bullet_list:
            self.body += "  " + comment + "\n"
        else:
            self.body += comment + "\n"

    def process_all(self):
        statement_found = False

        while True:
            line = self.get_next_line()

            self.debug("PROCESSING '{}'".format(line))

            if not line.strip():
                # empty line
                if statement_found:
                    break
                continue

            elif RE_COMMENT.match(line):
                # comment
                match = RE_COMMENT.match(line)
                comment = match.group(1).strip()

                self.add_body_line(comment)
                continue

            elif RE_COMMENT_EMPTY_LINE.match(line):
                # comment, empty line
                match = RE_COMMENT_EMPTY_LINE.match(line)
                comment = "\n"

                self.add_body_line(comment)
                continue

            elif self.statement_pattern.match(line):
                # current config statement
                self.process_statement_cfg_line(line=line)
                statement_found = True
                self.debug("STATEMENT FOUND")

                if not self.post_comment:
                    break

                continue

            elif line.strip().startswith("- ") or line.strip().startswith("#- "):
                continue

            else:
                raise ValueError("From {}, can't parse line: '{}'".format(self.name, line))

class CommCfgStatement(CfgStatement):

    def __init__(self, *args, **kwargs):
        CfgStatement.__init__(self, *args, **kwargs)
        self.sub_statements.append(CfgStatement("std", hide=True))
        self.sub_statements.append(CfgStatement("lrg", hide=True))
        self.sub_statements.append(CfgStatement("ext", hide=True))

CFG = CfgStatement("cfg", t="General options", statement_pattern="^()(cfg):()", sub=[
        CfgStatement("rs_as", pre_comment=True),
        CfgStatement("router_id", pre_comment=True),
        CfgStatement("prepend_rs_as", pre_comment=True),
        CfgStatement("path_hiding", pre_comment=True),
        CfgStatement("passive", pre_comment=True),
        CfgStatement("multihop", pre_comment=True),
        CfgStatement("gtsm", pre_comment=True),
        CfgStatement("add_path", pre_comment=True),
        CfgStatement("filtering", t="Filtering", sub=[
            CfgStatement("next_hop", t="NEXT_HOP", pre_comment=True, sub=[
                CfgStatement("policy", pre_comment=True)
            ]),
            CfgStatement("ipv4_pref_len", t="Prefix length", pre_comment=True, sub=[
                CfgStatement("min", hide=True),
                CfgStatement("max", hide=True)
            ]),
            CfgStatement("ipv6_pref_len", group_with_previous="ipv4_pref_len", sub=[
                CfgStatement("min"),
                CfgStatement("max")
            ]),
            CfgStatement("global_black_list_pref", t="Filtered prefixes", pre_comment=True),
            CfgStatement("max_as_path_len", t="Max AS_PATH length", pre_comment=True),
            CfgStatement("reject_invalid_as_in_as_path", t="Invalid ASNs in AS_PATH", pre_comment=True),
            CfgStatement("transit_free", t="Transit-free networks", post_comment=True, sub=[
                CfgStatement("action", pre_comment=True),
                CfgStatement("asns", pre_comment=True)
            ]),
            CfgStatement("never_via_route_servers", t="'Never via route-servers' networks", post_comment=True, sub=[
                CfgStatement("peering_db", pre_comment=True),
                CfgStatement("asns", pre_comment=True)
            ]),
            CfgStatement("irrdb", t="IRRDB filters", post_comment=True, sub=[
                CfgStatement("enforce_origin_in_as_set", pre_comment=True),
                CfgStatement("enforce_prefix_in_as_set", pre_comment=True),
                CfgStatement("allow_longer_prefixes", pre_comment=True),
                CfgStatement("tag_as_set", pre_comment=True),
                CfgStatement("peering_db", pre_comment=True),
                CfgStatement("use_rpki_roas_as_route_objects", post_comment=True, sub=[
                    CfgStatement("enabled", pre_comment=True),
                ]),
                CfgStatement("use_arin_bulk_whois_data", post_comment=True, sub=[
                    CfgStatement("enabled", pre_comment=True),
                    CfgStatement("source", pre_comment=True)
                ]),
                CfgStatement("use_registrobr_bulk_whois_data", post_comment=True, sub=[
                    CfgStatement("enabled", pre_comment=True),
                    CfgStatement("source", pre_comment=True)
                ]),
            ]),
            CfgStatement("rpki_bgp_origin_validation", t="RPKI BGP Origin Validation", sub=[
                CfgStatement("enabled", pre_comment=True),
                CfgStatement("reject_invalid", pre_comment=True)
            ]),
            CfgStatement("max_prefix", t="Max prefix", post_comment=True, sub=[
                CfgStatement("action", pre_comment=True),
                CfgStatement("restart_after", pre_comment=True),
                CfgStatement("count_rejected_routes", pre_comment=True),
                CfgStatement("peering_db", post_comment=True, sub = [
                    CfgStatement("enabled", pre_comment=True),
                    CfgStatement("increment", pre_comment=True, sub=[
                        CfgStatement("absolute", pre_comment=True),
                        CfgStatement("relative", pre_comment=True)
                    ]),
                ]),
                CfgStatement("general_limit_ipv4", pre_comment=True),
                CfgStatement("general_limit_ipv6", group_with_previous="general_limit_ipv4")
            ]),
            CfgStatement("reject_policy", t="Reject policy", sub=[
                CfgStatement("policy", pre_comment=True)
            ]),
        ]),
        CfgStatement("rpki_roas", t="RPKI ROAs", post_comment=True, sub=[
            CfgStatement("source", pre_comment=True),
            CfgStatement("ripe_rpki_validator_url", pre_comment=True),
            CfgStatement("allowed_trust_anchors", pre_comment=True),
            CfgStatement("ignore_cache_files_older_than", pre_comment=True)
        ]),
        CfgStatement("blackhole_filtering", t="Blackhole filtering", post_comment=True, sub=[
            CfgStatement("policy_ipv4", pre_comment=True),
            CfgStatement("policy_ipv6", group_with_previous="policy_ipv4"),
            CfgStatement("rewrite_next_hop_ipv4", pre_comment=True),
            CfgStatement("rewrite_next_hop_ipv6", group_with_previous="rewrite_next_hop_ipv4"),
            CfgStatement("announce_to_client", pre_comment=True),
            CfgStatement("add_noexport", pre_comment=True)
        ]),
        CfgStatement("graceful_shutdown", t="Graceful shutdown", post_comment=True, sub=[
            CfgStatement("enabled", pre_comment=True),
            CfgStatement("local_pref", pre_comment=True)
        ]),
        CfgStatement("rfc1997_wellknown_communities", t="RFC1997 well-known communities", post_comment=True, sub=[
            CfgStatement("policy", pre_comment=True)
        ]),
        CfgStatement("rtt_thresholds", t="RTT thresholds", pre_comment=True),
        CfgStatement("communities", t="BGP Communities", post_comment=True, sub=[

            CommCfgStatement("prefix_present_in_as_set", g="Prefix/origin AS present in client's AS-SET", pre_comment=True),
            CommCfgStatement("prefix_not_present_in_as_set", group_with_previous="prefix_present_in_as_set"),
            CommCfgStatement("origin_present_in_as_set", group_with_previous="prefix_present_in_as_set"),
            CommCfgStatement("origin_not_present_in_as_set", group_with_previous="prefix_present_in_as_set"),
            CommCfgStatement("prefix_validated_via_rpki_roas", group_with_previous="prefix_present_in_as_set"),
            CommCfgStatement("prefix_validated_via_arin_whois_db_dump", group_with_previous="prefix_present_in_as_set"),
            CommCfgStatement("prefix_validated_via_registrobr_whois_db_dump", group_with_previous="prefix_present_in_as_set"),
            CommCfgStatement("route_validated_via_white_list", group_with_previous="prefix_present_in_as_set"),

            CommCfgStatement("blackholing", g="Blackhole filtering", pre_comment=True),

            CommCfgStatement("do_not_announce_to_any", g="Propagation control", pre_comment=True),
            CommCfgStatement("do_not_announce_to_peer", pre_comment=True),
            CommCfgStatement("announce_to_peer", pre_comment=True),
            CommCfgStatement("do_not_announce_to_peers_with_rtt_lower_than", pre_comment=True),
            CommCfgStatement("do_not_announce_to_peers_with_rtt_higher_than", group_with_previous="do_not_announce_to_peers_with_rtt_lower_than"),
            CommCfgStatement("announce_to_peers_with_rtt_lower_than", pre_comment=True),
            CommCfgStatement("announce_to_peers_with_rtt_higher_than", group_with_previous="announce_to_peers_with_rtt_lower_than"),

            CommCfgStatement("prepend_once_to_any", g="Prepending", pre_comment=True),
            CommCfgStatement("prepend_twice_to_any", group_with_previous="prepend_once_to_any"),
            CommCfgStatement("prepend_thrice_to_any", group_with_previous="prepend_once_to_any"),

            CommCfgStatement("prepend_once_to_peer", pre_comment=True),
            CommCfgStatement("prepend_twice_to_peer", group_with_previous="prepend_once_to_peer"),
            CommCfgStatement("prepend_thrice_to_peer", group_with_previous="prepend_once_to_peer"),

            CommCfgStatement("prepend_once_to_peers_with_rtt_lower_than", pre_comment=True),
            CommCfgStatement("prepend_twice_to_peers_with_rtt_lower_than", group_with_previous="prepend_once_to_peers_with_rtt_lower_than"),
            CommCfgStatement("prepend_thrice_to_peers_with_rtt_lower_than", group_with_previous="prepend_once_to_peers_with_rtt_lower_than"),
            CommCfgStatement("prepend_once_to_peers_with_rtt_higher_than", group_with_previous="prepend_once_to_peers_with_rtt_lower_than"),
            CommCfgStatement("prepend_twice_to_peers_with_rtt_higher_than", group_with_previous="prepend_once_to_peers_with_rtt_lower_than"),
            CommCfgStatement("prepend_thrice_to_peers_with_rtt_higher_than", group_with_previous="prepend_once_to_peers_with_rtt_lower_than"),

            CommCfgStatement("add_noexport_to_any", g="NO_EXPORT / NO_ADVERTISE", pre_comment=True),
            CommCfgStatement("add_noadvertise_to_any", group_with_previous="add_noexport_to_any"),
            CommCfgStatement("add_noexport_to_peer", pre_comment=True),
            CommCfgStatement("add_noadvertise_to_peer", group_with_previous="add_noexport_to_peer"),

            CommCfgStatement("reject_cause", g="Reject cause", pre_comment=True),
            CommCfgStatement("rejected_route_announced_by", pre_comment=True)
        ]),
        CfgStatement("custom_communities", t="Custom BGP communities", sub=[
            CfgStatement("custom_community1_name", pre_comment=True)
        ])
    ])

def main():
    with open("config.d/general.yml", "r") as f:
        # Remove first block of comments.
        s = f.readline()
        while s.startswith("#"):
            s = f.readline()
        CFG.parse(f)
    res = CFG.build_result(0)
    with open("docs/GENERAL.rst", "w") as f:
        f.write(".. DO NOT EDIT: this file is automatically created by /utils/build_general.py\n")
        f.write("\n")
        f.write(".. include:: GENERAL.txt\n")
        f.write("\n")
        f.write(res)
main()

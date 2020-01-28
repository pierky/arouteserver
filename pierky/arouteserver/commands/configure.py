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

import argparse
from collections import OrderedDict
import os
from packaging import version
import sys
import textwrap
import yaml

from .base import ARouteServerCommand

from ..ask import Ask
from ..builder import OpenBGPDConfigBuilder
from ..config.program import program_config
from ..errors import ARouteServerError
from ..ipaddresses import IPNetwork

class ConfigureCommand(ARouteServerCommand):

    COMMAND_NAME = "configure"
    COMMAND_HELP = ("Initialize a working 'general.yml' file "
                    "with suggested route server's policies and "
                    "settings. "
                    "Examples can be found at "
                    "https://github.com/pierky/arouteserver/tree/"
                    "master/examples/auto-config")

    NEEDS_CONFIG = True

    def __init__(self, *args, **kwargs):
        ARouteServerCommand.__init__(self, *args, **kwargs)

        self.answers = {}
        self.notes = []
        self.preset_answers = {}

    @classmethod
    def add_arguments(cls, parser):
        super(ConfigureCommand, cls).add_arguments(parser)

        parser.add_argument(
            "-o", "--output",
            help="Output file. "
                 "By default, the general.yml file referenced by the "
                 "program configuration will be used. "
                 "Use '-' for stdout.",
            dest="output_file")

        parser.add_argument(
            "--preset-answer",
            nargs="+",
            help=argparse.SUPPRESS,
            dest="preset_answer"
        )

    def wr_text(self, s, title=None, dont_wrap=False):
        sys.stdout.write("\n")
        if title:
            sys.stdout.write(title + "\n")
            sys.stdout.write("=" * len(title) + "\n")
            sys.stdout.write("\n")
        if not s:
            return
        for line in s.split("\n"):
            if dont_wrap:
                sys.stdout.write(line)
            else:
                sys.stdout.write("\n".join(textwrap.wrap(line, width=80)))
            sys.stdout.write("\n")
        sys.stdout.write("\n")

    def add_answer(self, answer_id, ask_func, *args, **kwargs):
        if self.preset_answers:
            self.ask.next_answer = self.preset_answers[answer_id]

        answer_ok = False
        while not answer_ok:
            try:
                answer_ok, answer = ask_func(*args, raise_exc=True, **kwargs)
            except KeyboardInterrupt:
                raise ARouteServerError("Aborted!")
            if answer_ok:
                break
        self.answers[answer_id] = answer

    def ask_list_of_ip_prefixes(self, text, raise_exc=False):
        answer_given, v = self.ask.ask(text, None, None, raise_exc)
        if not answer_given:
            return False, None
        res = []
        for s in v.split(","):
            try:
                prefix = IPNetwork(s.strip())
                res.append("{}/{}".format(prefix.ip, prefix.prefixlen))
            except:
                print("Invalid input: a list of IP prefixes is expected. "
                      "'{}' is invalid.".format(s))
                return False, None
        return True, res

    #def ask_16bit_int(self, text, raise_exc=False):
    #    answer_given, v = self.ask.ask_int(text, None, None, raise_exc)
    #    if not answer_given:
    #        return False, None
    #    if v > 65535:
    #        print("Invalid input: a 16-bit integer is expected.")
    #        return False, None
    #    return True, v

    def collect_answers(self):
        if self.answers:
            return

        self.ask = Ask()

        self.wr_text(
            "Depending on the BGP daemon used for the route server "
            "some features may not be available.\n"
            "\n"
            "Details here:\n"
            "https://arouteserver.readthedocs.io/en/latest/"
            "CONFIG.html#caveats-and-limitations",
            title="BGP daemon"
        )
        self.add_answer("daemon", self.ask.ask,
            "Which BGP daemon will be used?",
            options=["bird", "openbgpd"]
        )

        if self.answers["daemon"] == "openbgpd":
            self.add_answer("version", self.ask.ask,
                "Which version?",
                options=OpenBGPDConfigBuilder.AVAILABLE_VERSION,
                default=OpenBGPDConfigBuilder.AVAILABLE_VERSION[-1]
            )

        self.wr_text(
            None, title="Router server's ASN"
        )
        self.add_answer("asn", self.ask.ask_int,
            "What's the ASN of the route server?"
        )

        if self.answers["asn"] > 65535:
            self.wr_text(
                "Since the ASN used for the route server is "
                "a 32-bit value, features and services offered "
                "to clients using BGP communities "
                "will be configured to use a placeholder 16 bit "
                "ASN: 65534",
                #"can be "
                #"automatically configured only if a 16-bit "
                #"placeholder ASN is also given "
                #"(with the exception of BGP Large Communities).",
                title="Place-holder 16-bit ASN for BGP communities"
            )
            #self.add_answer("comms_asn", self.ask_16bit_int,
            #    "16-bit ASN used for BGP communities"
            #)
            self.answers["comms_asn"] = 65534

        self.wr_text(
            None, title="Route server's BGP router-id"
        )
        self.add_answer("router_id", self.ask.ask_ipv4_addr,
            "Please enter the route server BGP router-id:"
        )

        self.wr_text(
            "A list of local IPv4/IPv6 networks must be provided "
            "here: routes announced by route server clients for "
            "these prefixes will be filtered out.",
            title="List of local networks"
        )
        self.add_answer("black_list", self.ask_list_of_ip_prefixes,
            "Please enter a comma-separated list of local networks:"
        )

        return self.answers

    def process_answers(self):

        def add_comm(name, std=None, lrg=None):
            if self.answers["asn"] > 65535:
                rs_as = self.answers["comms_asn"]
            else:
                rs_as = "rs_as"

            if name not in cfg["communities"]:
                cfg["communities"][name] = OrderedDict()

            if self.answers["daemon"] == "openbgpd":
                if version.parse(self.answers["version"]) > version.parse("6.0"):
                    communities = (
                        ("std", std),
                        ("lrg", lrg)
                    )
                else:
                    communities = (
                        ("std", std),
                    )
            else:
                communities = (
                    ("std", std),
                    ("ext", "rt:{}".format(std)),
                    ("lrg", lrg)
                )

            for comm_type, comm_val in communities:
                if comm_val:
                    cfg["communities"][name][comm_type] = \
                        comm_val.format(
                            rs_as=rs_as
                        )

        res = OrderedDict()
        res["cfg"] = OrderedDict()
        cfg = res["cfg"]

        cfg["rs_as"] = self.answers["asn"]

        cfg["router_id"] = self.answers["router_id"]

        if self.answers["daemon"] == "openbgpd":
            self.notes.append(
                "For OpenBGPD, path-hiding mitigation techniques are "
                "not implemented."
            )
            cfg["path_hiding"] = False

        cfg["filtering"] = OrderedDict()
        filtering = cfg["filtering"]

        filtering["next_hop"] = {"policy": "strict"}

        filtering["ipv4_pref_len"] = {"min": 8, "max": 24}
        filtering["ipv6_pref_len"] = {"min": 12, "max": 48}
        self.notes.append(
            "Accepted prefix lengths are 8-24 for IPv6 and 12-48 for IPv6."
        )

        filtering["global_black_list_pref"] = []
        for net in [IPNetwork(_) for _ in self.answers["black_list"]]:
            entry = OrderedDict()
            entry["prefix"] = str(net.ip)
            entry["length"] = net.prefixlen
            filtering["global_black_list_pref"].append(
                entry
            )

        filtering["max_as_path_len"] = 32

        filtering["reject_invalid_as_in_as_path"] = True

        filtering["transit_free"] = {
            "action": "reject",
            "asns": [174, 209, 286, 701, 1239, 1299, 2828, 2914,
                     3257, 3320, 3356, 3549, 5511, 6453, 6461,
                     6762, 6830, 7018, 12956]
        }
        filtering["never_via_route_servers"] = {
            "peering_db": True
        }
        self.notes.append(
            "Routes with 'transit-free networks' or "
            "'never via route-server' (PeeringDB) ASNs in the middle of "
            "AS_PATH are rejected."
        )

        filtering["irrdb"] = OrderedDict()
        irrdb = filtering["irrdb"]
        irrdb["enforce_origin_in_as_set"] = True
        irrdb["enforce_prefix_in_as_set"] = True
        irrdb["allow_longer_prefixes"] = True
        self.notes.append(
            "IRR-based filters are enabled; prefixes that are more specific "
            "of those registered are accepted."
        )
        irrdb["tag_as_set"] = True
        irrdb["peering_db"] = True
        self.notes.append(
            "PeeringDB is used to fetch AS-SETs for those clients that are "
            "not explicitly configured."
        )
        irrdb["use_rpki_roas_as_route_objects"] = {
            "enabled": True
        }
        self.notes.append(
            "RPKI ROAs are used as if they were route objects to further "
            "enrich IRR data."
        )
        irrdb["use_arin_bulk_whois_data"] = {
            "enabled": True
        }
        irrdb["use_registrobr_bulk_whois_data"] = {
            "enabled": True
        }
        self.notes.append(
            "ARIN Whois database dump is fetched from NLNOG to further "
            "enrich IRR data."
        )
        self.notes.append(
            "NIC.BR Whois database dump is fetched from Registro.br to further "
            "enrich IRR data."
        )

        filtering["rpki_bgp_origin_validation"] = OrderedDict()
        filtering["rpki_bgp_origin_validation"]["enabled"] = True
        filtering["rpki_bgp_origin_validation"]["reject_invalid"] = True
        self.notes.append(
            "RPKI BGP Origin Validation is enabled. INVALID routes are "
            "rejected."
        )

        filtering["max_prefix"] = {
            "action": "shutdown",
            "peering_db": {
                "enabled": True
            }
        }
        self.notes.append(
            "PeeringDB is used to fetch networks prefix count."
        )

        cfg["graceful_shutdown"] = {"enabled": False}
        if self.answers["daemon"] == "bird":
            cfg["graceful_shutdown"] = {"enabled": True}
        if self.answers["daemon"] == "openbgpd" and \
            version.parse(self.answers["version"]) >= version.parse("6.2"):
            cfg["graceful_shutdown"] = {"enabled": True}
        if cfg["graceful_shutdown"]["enabled"]:
            self.notes.append(
                "Routes tagged with the GRACEFUL_SHUTDOWN well-known "
                "community (65535:0) are processed accordingly to "
                "draft-ietf-grow-bgp-gshut."
            )

        cfg["rfc1997_wellknown_communities"] = {"policy": "pass"}

        cfg["communities"] = OrderedDict()

        add_comm("prefix_present_in_as_set",
                 "64512:11", "rs_as:64512:11")
        add_comm("prefix_not_present_in_as_set",
                 "64512:10", "rs_as:64512:10")
        add_comm("origin_present_in_as_set",
                 "64512:21", "rs_as:64512:21")
        add_comm("origin_not_present_in_as_set",
                 "64512:20", "rs_as:64512:20")
        add_comm("prefix_validated_via_rpki_roas",
                 "64512:31", "rs_as:64512:31")
        add_comm("route_validated_via_white_list",
                 "64512:41", "rs_as:64512:41")

        add_comm("do_not_announce_to_any",
                 "0:{rs_as}", "rs_as:0:0")
        add_comm("do_not_announce_to_peer",
                 "0:peer_as", "rs_as:0:peer_as")
        add_comm("announce_to_peer",
                 "{rs_as}:peer_as", "rs_as:1:peer_as")

        add_comm("prepend_once_to_any",
                 "65501:{rs_as}", "rs_as:101:0")
        add_comm("prepend_twice_to_any",
                 "65502:{rs_as}", "rs_as:102:0")
        add_comm("prepend_thrice_to_any",
                 "65503:{rs_as}", "rs_as:103:0")

        add_comm("prepend_once_to_peer",
                 "65511:peer_as", "rs_as:101:peer_as")
        add_comm("prepend_twice_to_peer",
                 "65512:peer_as", "rs_as:102:peer_as")
        add_comm("prepend_thrice_to_peer",
                 "65513:peer_as", "rs_as:103:peer_as")

        add_comm("add_noexport_to_peer",
                 "65281:peer_as", "rs_as:65281:peer_as")
        add_comm("add_noadvertise_to_peer",
                 "65282:peer_as", "rs_as:65282:peer_as")

        return res

    def configure_yml(self):

        def represent_ordereddict(dumper, data):
            value = []

            for item_key, item_value in data.items():
                node_key = dumper.represent_data(item_key)
                node_value = dumper.represent_data(item_value)

                value.append((node_key, node_value))

            return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)

        self.collect_answers()
        cfg = self.process_answers()

        yaml.add_representer(OrderedDict, represent_ordereddict)
        return yaml.dump(cfg, default_flow_style=False)

    def configure_dict(self):
        self.collect_answers()
        return self.process_answers()

    def run(self):
        self.preset_answers = {}
        if self.args.preset_answer:
            for key_val in self.args.preset_answer:
                if not key_val.strip():
                    continue
                preset_key = key_val.split("=")[0]
                preset_val = key_val.split("=")[1]
                self.preset_answers[preset_key] = preset_val

        dest = self.args.output_file
        if not dest:
            dest = program_config.get("cfg_general")

        if dest != "-":
            if os.path.exists(dest):
                _, yes_no = Ask().ask_yes_no(
                    "The file {} already exists; "
                    "it will be overwritten: "
                    "proceed anyway?".format(dest),
                    default="no"
                )
                if yes_no.lower() != "yes":
                    print("Aborted!")
                    return

        yml = self.configure_yml()

        msg = "\n\n"
        msg += "Route server policy definition file generated successfully!\n"
        msg += "===========================================================\n"
        msg += "\n"
        msg += "The content of the general configuration file "
        if dest == "-":
            msg += "follows.\n"
        else:
            msg += "will now be written to {}\n".format(dest)
        msg += "\n"
        msg += "Some notes:\n"
        msg += "\n"
        msg += " - "
        msg += "\n - ".join(self.notes)

        if dest == "-":
            msg = "# " + "\n# ".join([line for line in msg.split("\n")])
            self.wr_text(msg, dont_wrap=True)
            sys.stdout.write(yml)
        else:
            self.wr_text(msg)
            try:
                with open(dest, "w") as f:
                    f.write(yml)
            except Exception as e:
                raise ARouteServerError(
                    "An error occurred while writing the output "
                    "configuration to {} - {}".format(
                        dest, str(e)
                    )
                )

        return True

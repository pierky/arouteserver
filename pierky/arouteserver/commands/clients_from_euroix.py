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
import datetime
import sys
import yaml

from .base import ARouteServerCommand
from ..config.program import program_config
from ..config.clients import merge_clients
from ..euro_ix import EuroIXMemberList
from ..errors import ARouteServerError

class ClientsFromEuroIXCommand(ARouteServerCommand):

    COMMAND_NAME = "clients-from-euroix"
    COMMAND_HELP = ("Build a list of clients on the basis "
                    "of EURO-IX JSON file.")
    NEEDS_CONFIG = True

    @classmethod
    def add_arguments(cls, parser):
        super(ClientsFromEuroIXCommand, cls).add_arguments(parser)

        parser.add_argument(
            "--url",
            type=str,
            help="URL of the file that contains the Euro-IX JSON "
                 "member list. If this is not given, data is read "
                 "from the input file (arguments -i, --input).",
            dest="url")

        parser.add_argument(
            "-i", "--input",
            type=argparse.FileType('r'),
            help="Input file. Default: stdin.",
            default=sys.stdin,
            dest="input_file")

        parser.add_argument(
            "ixp_id",
            type=int,
            nargs="?",
            help="The numeric identifier used by the IX to identify the "
                 "infrastructure for which the list of clients is requested. "
                 "If not given, a list of IX's infrastructures will be "
                 "printed.")

        parser.add_argument(
            "--vlan-id",
            type=int,
            help="Only consider members that have a connection to the given "
                 "VLAN id. Please note: this is not necessarily the 802.1q "
                 "tag but, generally speaking, it is the numeric identifier "
                 "used by the IX to identify the VLAN in its Euro-IX JSON "
                 "file.",
            dest="vlan_id")

        parser.add_argument(
            "--routeserver-only",
            action="store_true",
            help="Exclude members whose "
                 "'ixp_list.[].vlan.[].ipv[4|6].routeserver' attribute "
                 "is false.",
            dest="routeserver_only")

        parser.add_argument(
            "--guess-custom-bgp-communities",
            nargs="+",
            choices=EuroIXMemberList.CUSTOM_COMMUNITIES,
            help="If set, clients will be configured to attach custom "
                 "informational BGP communities to the routes they "
                 "announce to the route server. These communities will "
                 "be guessed on the basis of the available attributes "
                 "from the Euro-IX JSON file (member type, switch ID, "
                 "city, ...).",
            dest="guess_custom_bgp_communities")


        parser.add_argument(
            "--merge-from-peeringdb",
            nargs="+",
            choices=EuroIXMemberList.INFO_FROM_PEERINGDB,
            help="Fetch missing information from PeeringDB if they are "
                 "not included in the Euro-IX JSON member list file.",
            dest="merge_from_peeringdb")

        parser.add_argument(
            "--merge-from-custom-file",
            help="Merge a custom set of client settings from "
                 "FILE into the clients generated from the "
                 "Euro-IX JSON file. Can be used to override "
                 "or enrich the clients which are automatically "
                 "built by this tool with some custom local "
                 "settings. For more info on how it works and "
                 "the syntax of the custom file, run this command "
                 "again with --help-merge-from-custom-file.",
            metavar="FILE",
            type=argparse.FileType('r'),
            dest="merge_from_custom_file")

        parser.add_argument(
            "--help-merge-from-custom-file",
            help="Prints additional info on how to use the "
                 "--merge-from-custom-file option.",
            action="store_true")

        parser.add_argument(
            "-o", "--output",
            type=argparse.FileType('w'),
            help="Output file. Default: stdout.",
            default=sys.stdout,
            dest="output_file")

    def run(self):
        if self.args.help_merge_from_custom_file:
            print(
                "\n"
                "When --merge-from-custom-file is used, a local "
                "YAML file is used to enrich the clients.yml file "
                "built using this command.\n"
                "This option can be used to handle local exceptions, "
                "to override settings or to add clients which are "
                "not included in the Euro-IX JSON used to built the "
                "original file.\n"
                "The format of the custom file must be the same of "
                "the regular clients.yml file; the 'ip' attribute "
                "of a client included inside the custom file is used "
                "to match the client on the original clients.yml "
                "build by this command. The content of the custom "
                "file is then merged into the definition of the "
                "original client.\n"
                "\n"
                "If a client is configured in the local custom file "
                "but is missing from the set of clients generated "
                "using the Euro-IX JSON file, then the local one is "
                "ignored, unless the 'add_if_missing' attribute is "
                "set to 'True': in that case, the custom client is "
                "added to the resulting clients.yml file.\n"
                "\n"
                "Example of a local custom file:\n"
                "\n"
                "clients:\n"
                "  - ip: 192.0.2.1\n"
                "    password: ""bgp_secret""\n"
                "  - ip: 192.0.2.2\n"
                "    cfg:\n"
                "      filtering:\n"
                "        irrdb:\n"
                "          as_sets:\n"
                "            - AS-TWO\n"
                "  - ip: 192.0.2.3\n"
                "    add_if_missing: True\n"
                "    asn: 3333\n"
            )
            return True

        euro_ix = EuroIXMemberList(self.args.url or self.args.input_file,
                                   program_config.get_dir("cache_dir"),
                                   program_config.get("cache_expiry"))

        if self.args.ixp_id:
            clients = euro_ix.get_clients(
                self.args.ixp_id, vlan_id=self.args.vlan_id,
                routeserver_only=self.args.routeserver_only,
                guess_custom_bgp_communities=self.args.guess_custom_bgp_communities,
                merge_from_peeringdb=self.args.merge_from_peeringdb)
            res = {"clients": clients}

            if self.args.merge_from_custom_file:
                try:
                    merge_clients(res, self.args.merge_from_custom_file)
                except ARouteServerError as e:
                    raise ARouteServerError(
                        "An error occurred while processing the custom "
                        "clients file provided via "
                        "--merge-from-custom-file: {}".format(e)
                    )

            comments = []
            comments.append("# Data fetched from {} at {} UTC".format(
                self.args.url or self.args.input_file.name,
                datetime.datetime.utcnow().isoformat()
            ))
            comments.append("# IXP ID: {}".format(self.args.ixp_id))
            if self.args.vlan_id:
                comments.append("# VLAN ID: {}".format(self.args.vlan_id))
            self.args.output_file.write("\n".join(comments) + "\n")
            yaml.safe_dump(res, self.args.output_file, default_flow_style=False)

            if self.args.guess_custom_bgp_communities and \
                euro_ix.unique_custom_communities:
                comments = []
                comments.append("# The following custom BGP communities must")
                comments.append("# be declared within the general.yml file:")
                comments.append("#  custom_communities:")
                for prefix in euro_ix.unique_custom_communities:
                    comms = euro_ix.unique_custom_communities[prefix]
                    if comms:
                        for comm in comms:
                            comments.append("#    {}:".format(comm))
                            comments.append("#      std:")
                            comments.append("#      ext:")
                            comments.append("#      lrg:")
                self.args.output_file.write("\n".join(comments) + "\n")
        else:
            euro_ix.print_infrastructure_list(self.args.output_file)

        return True

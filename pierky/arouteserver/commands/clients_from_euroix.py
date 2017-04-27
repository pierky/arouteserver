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

import argparse
import datetime
import sys
import yaml

from .base import ARouteServerCommand
from ..config.program import program_config
from ..errors import EuroIXError, EuroIXSchemaError
from ..euro_ix import EuroIXMemberList

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
            "-o", "--output",
            type=argparse.FileType('w'),
            help="Output file. Default: stdout.",
            default=sys.stdout,
            dest="output_file")

    def run(self):
        euro_ix = EuroIXMemberList(self.args.url or self.args.input_file)

        if self.args.ixp_id:
            clients = euro_ix.get_clients(
                self.args.ixp_id, vlan_id=self.args.vlan_id,
                routeserver_only=self.args.routeserver_only,
                guess_custom_bgp_communities=self.args.guess_custom_bgp_communities)
            res = {"clients": clients}

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

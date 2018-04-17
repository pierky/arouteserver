# Copyright (C) 2017-2018 Pier Carlo Chiodi
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
import sys
import yaml

from ..ask import Ask
from .base import ARouteServerCommand
from ..config.program import program_config
from ..peering_db import PeeringDBIXList, clients_from_peeringdb

class ClientsFromPeeringDBCommand(ARouteServerCommand):

    COMMAND_NAME = "clients-from-peeringdb"
    COMMAND_HELP = ("Build a list of clients and their AS-SET on the basis "
                    "of PeeringDB records.")
    NEEDS_CONFIG = True

    @classmethod
    def add_arguments(cls, parser):
        super(ClientsFromPeeringDBCommand, cls).add_arguments(parser)

        parser.add_argument(
            "-o", "--output",
            type=argparse.FileType('w'),
            help="Output file. Default: stdout.",
            default=sys.stdout,
            dest="output_file")

        parser.add_argument(
            "netixlanid",
            type=int,
            nargs="?",
            default=None,
            help="PeeringDB NetIX LAN ID. If not given, the IX-F database "
                 "will be used to show a list of IXPs.")

    def get_netixlanid(self):
        sys.stdout.write("Loading list of IXs... ")
        ix_list = PeeringDBIXList(
            cache_dir=program_config.get_dir("cache_dir"),
            cache_expiry=program_config.get("cache_expiry")
        )
        ix_list.load_data()
        sys.stdout.write("OK\n")

        print("")
        print("Select the IXP for which the clients list must be built")
        answer_given, text = Ask().ask("Enter the text to search for "
                                       "(IXP name, country, city):")
        if not answer_given:
            return None

        text = text.lower()

        print("{:>7}  {}".format("ID", "IXP description"))

        found = False
        for ixp in ix_list.ixp_list:
            if text in ixp["city"].lower() or \
                text in ixp["country"].lower() or \
                text in ixp["full_name"].lower() or \
                text in ixp["short_name"].lower():

                found = True

                print("{:>7}  {}, {}, {} ({})".format(
                    ixp["peeringdb_handle"],
                    ixp["country"].encode("ascii", "replace").decode("utf-8"),
                    ixp["city"].encode("ascii", "replace").decode("utf-8"),
                    ixp["full_name"].encode("ascii", "replace").decode("utf-8"),
                    ixp["short_name"].encode("ascii", "replace").decode("utf-8")
                ))

        if not found:
            print("No IXP found using '{}'".format(text))
            return False

        print("")
        answer_given, id = Ask().ask_int("Enter the ID of the IXP you want to use "
                                         "to build the clients list:")

        if not answer_given:
            return None

        return id

    def run(self):
        netixlanid = self.args.netixlanid
        if not netixlanid:
            netixlanid = self.get_netixlanid()
        if not netixlanid:
            return False

        sys.stderr.write("Building clients list from "
                         "PeeringDB Net IX LAN ID {}...\n".format(netixlanid))

        data = clients_from_peeringdb(
            netixlanid,
            program_config.get_dir("cache_dir")
        )
        yaml.safe_dump(data, self.args.output_file, default_flow_style=False)

        return True

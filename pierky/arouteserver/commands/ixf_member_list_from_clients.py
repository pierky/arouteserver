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
import datetime
import json
import logging
import os
import sys

from .base import ARouteServerCommand
from ..config.asns import ConfigParserASNS
from ..config.clients import ConfigParserClients
from ..config.program import program_config
from ..errors import ARouteServerError, MissingFileError

class IXFMemberListFromClientsCommand(ARouteServerCommand):

    COMMAND_NAME = "ixf-member-export"
    COMMAND_HELP = ("Build an IX-F Member Export JSON file "
                    "from the clients.")
    NEEDS_CONFIG = True

    @classmethod
    def add_arguments(cls, parser):
        super(IXFMemberListFromClientsCommand, cls).add_arguments(parser)

        parser.add_argument(
            "shortname",
            help="Short name of the IXP.")

        parser.add_argument(
            "--clients",
            help="Route server clients configuration file. "
                 "Default: the one set in the program configuration "
                 "file will be used.",
            metavar="FILE",
            dest="cfg_clients")

        parser.add_argument(
            "--ixp_id",
            type=int,
            default=0,
            help="The numeric identifier used by the IX to identify the "
                 "infrastructure for which the list of clients is generated. "
                 "Default: 0",
            dest="ixp_id")

        parser.add_argument(
            "--vlan-id",
            type=int,
            default=0,
            help="The VLAN ID used to set the connection_list.vlan_list "
                 "objects within the generated file. "
                 "Please note: this is not necessarily the 802.1q "
                 "tag but, generally speaking, it is the numeric identifier "
                 "used by the IX to identify the VLAN in its IX-F Member "
                 "Export JSON file.",
            dest="vlan_id")

        parser.add_argument(
            "-o", "--output",
            type=argparse.FileType('w'),
            help="Output file. Default: stdout.",
            default=sys.stdout,
            dest="output_file")

    @staticmethod
    def get_member_list(asns, clients, ixp_id, vlan_id):
        members = {}
        for client in clients:
            asn = str(client["asn"])
            if asn not in members:
                members[asn] = {"vlan_list": []}

            if client["description"]:
                members[asn]["descr"] = client["description"]

            vlan_obj = OrderedDict()
            vlan_obj["vlan_id"] = vlan_id

            ipv4_ipv6 = "ipv6" if ":" in client["ip"] else "ipv4"

            vlan_obj[ipv4_ipv6] = {"address": client["ip"]}

            max_pref = client["cfg"]["filtering"]["max_prefix"][
                "limit_{}".format(ipv4_ipv6)]

            if max_pref:
                vlan_obj[ipv4_ipv6]["max_prefix"] = max_pref

            as_macros = client["cfg"]["filtering"]["irrdb"]["as_sets"]
            if not as_macros:
                if "AS{}".format(asn) in asns:
                    as_macros = asns["AS{}".format(asn)]["as_sets"]

            if as_macros:
                if len(as_macros) > 1:
                    logging.warning(
                        "Client {ip} (AS{asn}) is configured with more than "
                        "one AS-SETs: since the destination format supports "
                        "only one item, only the first one ({as_set}) will "
                        "be exported.".format(
                            ip=client["ip"], asn=client["asn"],
                            as_set=as_macros[0]
                        )
                    )
                vlan_obj[ipv4_ipv6]["as_macro"] = as_macros[0]

            members[asn]["vlan_list"].append(vlan_obj)

        res = []
        for member_asn in members:
            member = {"asnum": int(member_asn)}

            if "descr" in members[member_asn]:
                member["name"] = members[member_asn]["descr"]

            connection_list_entry = OrderedDict()
            connection_list_entry["ixp_id"] = ixp_id
            connection_list_entry["vlan_list"] = members[member_asn]["vlan_list"]
            member["connection_list"] = [connection_list_entry]
            res.append(member)

        return res

    @staticmethod
    def load_config_from_path(path):
        clients = ConfigParserClients()
        asns = ConfigParserASNS()
        try:
            if not os.path.isfile(path):
                raise MissingFileError(path)

            clients.load(path)
            asns.load(path)
        except ARouteServerError as e:
            raise ARouteServerError(
                "One or more errors occurred while loading "
                "clients file{}".format(
                    ": {}".format(str(e)) if str(e) else ""
                )
            )

        return asns, clients

    @staticmethod
    def build_json(path, ixp_id, shortname, vlan_id):
        asns, clients = \
            IXFMemberListFromClientsCommand.load_config_from_path(path)

        res = OrderedDict()
        res["version"] = "0.6"
        res["timestamp"] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        ixp_list_entry = OrderedDict()
        ixp_list_entry["ixp_id"] = ixp_id
        ixp_list_entry["shortname"] = shortname
        ixp_list_entry["vlan"] = [{"id": vlan_id}]
        res["ixp_list"] = [ixp_list_entry]

        res["member_list"] = IXFMemberListFromClientsCommand.get_member_list(
            asns, clients, ixp_id, vlan_id
        )
        return res

    def run(self):
        path = self.args.cfg_clients or program_config.get("cfg_clients")

        dic = self.build_json(path, self.args.ixp_id, self.args.shortname,
                              self.args.vlan_id)

        json.dump(dic, self.args.output_file, indent=2)
        return True

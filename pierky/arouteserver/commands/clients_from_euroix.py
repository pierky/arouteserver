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
import json
import logging
import sys
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen
import yaml

from .base import ARouteServerCommand
from ..config.program import program_config
from ..errors import EuroIXError, EuroIXSchemaError

class ClientsFromEuroIXCommand(ARouteServerCommand):

    COMMAND_NAME = "clients-from-euroix"
    COMMAND_HELP = ("Build a list of clients on the basis "
                    "of EURO-IX JSON file.")
    NEEDS_CONFIG = True
    
    TESTED_EUROIX_SCHEMA_VERSIONS = ("0.4", "0.5", "0.6")

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
            help="The numeric identifier used by the IX to identify the "
                 "infrastructure for which the list of clients is requested.")

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
            "-o", "--output",
            type=argparse.FileType('w'),
            help="Output file. Default: stdout.",
            default=sys.stdout,
            dest="output_file")

    @staticmethod
    def clients_from_euroix(data, ixp_id, vlan_id=None,
                            routeserver_only=False):

        def check_type(v, vname, expected_type):
            if expected_type is str:
                expected_type_set = (str, unicode)
            else:
                expected_type_set = expected_type

            if not isinstance(v, expected_type_set):
                if expected_type is int and \
                    isinstance(v, (str, unicode)) and \
                    v.isdigit():
                    return int(v)

                raise EuroIXSchemaError(
                    "Invalid type for {} with value '{}': "
                    "it is {}, should be {}".format(
                        vname, v, str(type(v)), str(expected_type)
                    )
                )

            return v

        def get_item(key, src, expected_type=None, optional=False):
            if key not in src:
                if optional:
                    return None
                raise EuroIXSchemaError("Missing required item: {}".format(key))
            val = src[key]
            if expected_type:
                val = check_type(val, key, expected_type)
            return val

        def new_client(asn, description):
            client = {}
            client["asn"] = asn
            if description:
                client["description"] = description.encode("ascii", "replace")
            return client

        def get_descr(member, connection=None):

            res = []

            for info, k in [("AS{}", "asnum"),
                            ("name '{}'", "name")]:
                try:
                    res.append(info.format(member[k]))
                except:
                    pass

            if connection:
                for info, k in [("ixp_id {}", "ixp_id"),
                                ("state '{}'", "state")]:
                    try:
                        res.append(info.format(connection[k]))
                    except:
                        pass

                try:
                    for iface in connection["if_list"]:
                        res.append(
                            "iface on switch_id {}".format(iface["switch_id"])
                        )
                except:
                    pass

            if res:
                return ", ".join(res)
            else:
                return "unknown"

        def process_member(member, clients):
            if get_item("member_type", member, str, True) == "routeserver":
                # Member is a route server itself.
                return

            connection_list = get_item("connection_list", member, list)

            for connection in connection_list:
                try:
                    process_connection(member, connection, clients)
                except EuroIXError as e:
                    if str(e):
                        logging.error(
                            "Error while processing {}: {}".format(
                                get_descr(member, connection), str(e)
                            )
                        )
                    raise EuroIXError()

        def process_connection(member, connection, clients):
            check_type(connection, "connection", dict)

            if get_item("ixp_id", connection, int) != ixp_id:
                return

            # Member has a connection to the selected IXP infrastructure.
            asnum = get_item("asnum", member, int)
            name = get_item("name", member, str, True)

            vlan_list = get_item("vlan_list", connection, list, True)

            if vlan_id and not vlan_list:
                # A specific VLAN has been requested but member does not
                # have information about VLANs at all.
                return

            for vlan in vlan_list or []:
                check_type(vlan, "vlan", dict)

                if vlan_id and \
                    get_item("vlan_id", vlan, int, True) != vlan_id:
                    # This VLAN is not the requested one.
                    continue

                for ip_ver in (4, 6):
                    ipv4_6 = "ipv{}".format(ip_ver)
                    ip_info = get_item(ipv4_6, vlan, dict, True)

                    if not ip_info:
                        continue

                    address = get_item("address", ip_info, str, True)

                    if not address:
                        continue

                    if routeserver_only:
                        # Members with routeserver attribute == False
                        # are excluded.
                        if get_item("routeserver", ip_info, bool, True) is False:
                            continue

                    client = new_client(asnum, name)
                    client["ip"] = address

                    as_macro = get_item("as_macro", ip_info, str, True)
                    max_prefix = get_item("max_prefix", ip_info, int, True)

                    if as_macro or max_prefix:
                        client["cfg"] = {
                            "filtering": {}
                        }
                    if as_macro:
                        client["cfg"]["filtering"]["irrdb"] = {
                            "as_sets": [as_macro]
                        }
                    if max_prefix:
                        client["cfg"]["filtering"]["max_prefix"] = {
                            "limit_ipv{}".format(ip_ver): max_prefix
                        }

                    clients.append(client)

        version = get_item("version", data, str)
        tested_versions = ClientsFromEuroIXCommand.TESTED_EUROIX_SCHEMA_VERSIONS
        if version not in tested_versions:
            logging.warning("The version of the JSON schema of this file ({}) "
                            "is not one of those tested ({}). Unexpected "
                            "errors may occurr.".format(
                                version,
                                ", ".join(tested_versions)
                            ))

        ixp_list = get_item("ixp_list", data, list)
        member_list = get_item("member_list", data, list)

        ixp_found = False
        for ixp in ixp_list:
            check_type(ixp, "ixp", dict)

            if get_item("ixp_id", ixp, int) == ixp_id:
                ixp_found = True
                break

        if not ixp_found:
            raise EuroIXError(
                "IXP ID {} not found".format(ixp_id))

        raw_clients = []
        for member in member_list:
            try:
                check_type(member, "member", dict)
                process_member(member, raw_clients)
            except EuroIXError as e:
                if str(e):
                    logging.error(
                        "Error while processing member {}: {}".format(
                            get_descr(member), str(e)
                        )                            
                    )
                raise EuroIXError()

        return raw_clients

        # TODO: Merge clients with same IRRDB info

    def run(self):
        if self.args.url:
            try:
                response = urlopen(self.args.url)
                raw = response.read().decode("utf-8")
            except Exception as e:
                raise EuroIXError(
                    "Error while retrieving Euro-IX JSON file from {}: {}".format(
                        self.args.url, str(e)
                    )
                )
        else:
            raw = self.args.input_file.read()

        try:
            data = json.loads(raw)
        except Exception as e:
            raise EuroIXSchemaError(
                "Error while processing JSON data: {}".format(str(e))
            )

        clients = self.clients_from_euroix(
            data, self.args.ixp_id, vlan_id=self.args.vlan_id,
            routeserver_only=self.args.routeserver_only)
        res = {"clients": clients}

        yaml.safe_dump(res, self.args.output_file, default_flow_style=False)

        return True

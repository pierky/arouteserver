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
import json
import re
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

from .errors import EuroIXError, EuroIXSchemaError

class EuroIXMemberList(object):

    TESTED_EUROIX_SCHEMA_VERSIONS = ("0.4", "0.5", "0.6")

    CUSTOM_COMMUNITIES = ["switch_id", "switch_name", "colocation", "city",
                          "country", "member_type"]
    MEMBER_TYPES = ["peering", "ixp", "routeserver", "probono", "other"]
    EUROIX_SWITCH_ATTRIBUTES_COMMUNITIES_MAP = [
        ("id", "switch_id"),
        ("name", "switch_name"),
        ("colo", "colocation"),
        ("city", "city"),
        ("country", "country")
    ]

    def __init__(self, input_object):
        self.raw_data = None

        if isinstance(input_object, dict):
            self.raw_data = input_object
        elif isinstance(input_object, file):
            raw = input_object.read()
        else:
            try:
                response = urlopen(input_object)
                raw = response.read().decode("utf-8")
            except Exception as e:
                raise EuroIXError(
                    "Error while retrieving Euro-IX "
                    "JSON file from {}: {}".format(
                        input_object, str(e)
                    )
                )

        if not self.raw_data:
            try:
                self.raw_data = json.loads(raw)
            except Exception as e:
                raise EuroIXSchemaError(
                    "Error while processing JSON data: {}".format(str(e))
                )

        self.switches = None
        self.unique_custom_communities = None

        self.check_schema_version()

    @staticmethod
    def _check_type(v, vname, expected_type):
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

    @staticmethod
    def _get_item(key, src, expected_type=None, optional=False):
        if key not in src:
            if optional:
                return None
            raise EuroIXSchemaError("Missing required item: {}".format(key))
        val = src[key]
        if expected_type:
            val = EuroIXMemberList._check_type(val, key, expected_type)
        return val

    def check_schema_version(self):
        data = self.raw_data

        version = self._get_item("version", data, str)
        tested_versions = self.TESTED_EUROIX_SCHEMA_VERSIONS
        if version not in tested_versions:
            logging.warning("The version of the JSON schema of this file ({}) "
                            "is not one of those tested ({}). Unexpected "
                            "errors may occurr.".format(
                                version,
                                ", ".join(tested_versions)
                            ))

    def get_clients(self, ixp_id, vlan_id=None,
                    routeserver_only=False,
                    guess_custom_bgp_communities=[]):

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

        def normalize_bgp_community(s):
            res = s
            res = res.encode("ascii", "ignore")
            res = res.lower()
            res = re.sub("[\\/\[ \]+-]", "_", res)
            res = re.sub("[^0-9a-zA-Z_]", "", res)
            return res

        def attach_custom_bgp_community(client, prefix, name):
            community_tag = normalize_bgp_community(name)

            if "cfg" not in client:
                client["cfg"] = {}

            if "attach_custom_communities" not in client["cfg"]:
                client["cfg"]["attach_custom_communities"] = []

            if community_tag not in client["cfg"]["attach_custom_communities"]:
                client["cfg"]["attach_custom_communities"].append(
                    "{}_{}".format(prefix, community_tag)
                )

        def enrich_with_custom_bgp_communities(clients, connection):
            if not guess_custom_bgp_communities:
                return

            if_list = self._get_item("if_list", connection, list, True)
            if not if_list:
                return

            for if_list_entry in if_list:
                switch_id = self._get_item("switch_id", if_list_entry, int, True)
                if not switch_id:
                    return

                if not str(switch_id) in self.switches:
                    print("D")
                    return

                switch_info = self.switches[str(switch_id)]

                for attribute, prefix in self.EUROIX_SWITCH_ATTRIBUTES_COMMUNITIES_MAP:
                    if not prefix in guess_custom_bgp_communities:
                        continue
                    if not attribute in switch_info:
                        continue
                    attribute_val = switch_info[attribute]

                    for client in clients:
                        attach_custom_bgp_community(client, prefix, attribute_val)

        def process_member(member):
            if self._get_item("member_type", member, str, True) == "routeserver":
                # Member is a route server itself.
                return

            clients = []
            connection_list = self._get_item("connection_list", member, list)

            for connection in connection_list:
                try:
                    new_clients = process_connection(member, connection)
                    if new_clients:
                        enrich_with_custom_bgp_communities(new_clients,
                                                           connection)
                        clients.extend(new_clients)
                except EuroIXError as e:
                    if str(e):
                        logging.error(
                            "Error while processing {}: {}".format(
                                get_descr(member, connection), str(e)
                            )
                        )
                    raise EuroIXError()

            return clients

        def process_connection(member, connection):
            self._check_type(connection, "connection", dict)

            if self._get_item("ixp_id", connection, int) != ixp_id:
                return

            # Member has a connection to the selected IXP infrastructure.

            clients = []
            asnum = self._get_item("asnum", member, int)
            name = self._get_item("name", member, str, True)
            member_type = self._get_item("type", member, str, True)

            vlan_list = self._get_item("vlan_list", connection, list, True)

            if vlan_id and not vlan_list:
                # A specific VLAN has been requested but member does not
                # have information about VLANs at all.
                return

            # Workaround for IXP-Manager issue:
            # https://github.com/inex/IXP-Manager/commit/50c3781711ed38e773f86a8f3017d669d18e464d
            if vlan_list and isinstance(vlan_list[0], list):
                vlan_list = vlan_list[0]

            for vlan in vlan_list or []:
                self._check_type(vlan, "vlan", dict)

                if vlan_id and \
                    self._get_item("vlan_id", vlan, int, True) != vlan_id:
                    # This VLAN is not the requested one.
                    continue

                for ip_ver in (4, 6):
                    ipv4_6 = "ipv{}".format(ip_ver)
                    ip_info = self._get_item(ipv4_6, vlan, dict, True)

                    if not ip_info:
                        continue

                    address = self._get_item("address", ip_info, str, True)

                    if not address:
                        continue

                    if routeserver_only:
                        # Members with routeserver attribute == False
                        # are excluded.
                        if self._get_item("routeserver", ip_info, bool, True) is False:
                            continue

                    client = new_client(asnum, name)
                    client["ip"] = address

                    as_macro = self._get_item("as_macro", ip_info, str, True)
                    max_prefix = self._get_item("max_prefix", ip_info, int, True)

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
                    if guess_custom_bgp_communities and \
                        "member_type" in guess_custom_bgp_communities:
                        if member_type:
                            if member_type not in self.MEMBER_TYPES:
                                raise EuroIXSchemaError(
                                    "Unexpected member type: '{}'".format(
                                        member_type
                                    )
                                )

                            attach_custom_bgp_community(client, "member_type", member_type)

                    clients.append(client)

                return clients

        def get_custom_bgp_comms_data(ixp):
            raw_switches = self._get_item("switch", ixp, list, True)
            if not raw_switches:
                return

            # switches = {
            #   "<switch_id>": {
            #     "<switch_attr_name>": <value>
            #   }
            # }
            self.switches = {}

            # unique_custom_communities = {
            #   "<custom_community_prefix>": set of unique values
            # }
            self.unique_custom_communities = {
                cust_comm_prefix: set()
                for cust_comm_prefix in self.CUSTOM_COMMUNITIES
            }

            if "member_type" in guess_custom_bgp_communities:
                self.unique_custom_communities["member_types"] = set(
                    ["member_type_{}".format(t) for t in self.MEMBER_TYPES]
                )

            for switch in raw_switches:
                switch_id = self._get_item("id", switch, int, True)

                if not switch_id:
                    continue

                self.switches[str(switch_id)] = {}

                for attribute_name, prefix in self.EUROIX_SWITCH_ATTRIBUTES_COMMUNITIES_MAP:
                    attribute_val = self._get_item(attribute_name, switch,
                                                   optional=True)
                    if not attribute_val:
                        continue

                    if isinstance(attribute_val, int):
                        attribute_val = str(attribute_val)
                    attribute_val = attribute_val.encode("ascii", "replace")

                    if prefix in guess_custom_bgp_communities:
                        self.unique_custom_communities[prefix].add(
                            "{}_{}".format(prefix,
                                           normalize_bgp_community(attribute_val)
                                        )
                        )
                    self.switches[str(switch_id)][attribute_name] = attribute_val

        data = self.raw_data

        ixp_list = self._get_item("ixp_list", data, list)
        member_list = self._get_item("member_list", data, list)

        ixp_found = False
        for ixp in ixp_list:
            self._check_type(ixp, "ixp", dict)

            if self._get_item("ixp_id", ixp, int) == ixp_id:
                ixp_found = True
                break

        if not ixp_found:
            raise EuroIXError(
                "IXP ID {} not found".format(ixp_id))

        if guess_custom_bgp_communities:
            get_custom_bgp_comms_data(ixp)

        raw_clients = []
        for member in member_list:
            try:
                self._check_type(member, "member", dict)
                new_clients = process_member(member)
                if new_clients:
                    raw_clients.extend(new_clients)
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

    def print_infrastructure_list(self, out_file):
        data = self.raw_data

        ixp_list = self._get_item("ixp_list", data, list)
        for ixp in ixp_list:
            self._check_type(ixp, "ixp", dict)

            ixp_id = self._get_item("ixp_id", ixp, int)
            shortname = self._get_item("shortname", ixp, str)
            name = self._get_item("name", ixp, str, True)
            country = self._get_item("country", ixp, str, True)

            s = "IXP ID {}, short name '{}'".format(ixp_id, shortname)
            if name:
                s += ", '{}'".format(name)
            if country:
                s += ", {}".format(country)
            out_file.write(s + "\n")

            vlans = self._get_item("vlan", ixp, list, True)

            for vlan in vlans or []:
                s = ""

                vlan_id = self._get_item("id", vlan, int, True)
                if vlan_id:
                    s += ", " if s else ""
                    s += "ID {}".format(vlan_id)

                vlan_name = self._get_item("name", vlan, str, True)
                if vlan_name:
                    s += ", " if s else ""
                    s += "name '{}'".format(vlan_name)

                for ip_ver in (4, 6):
                    ipv4_6 = "ipv{}".format(ip_ver)
                    ip_info = self._get_item(ipv4_6, vlan, dict, True)
                    if not ip_info:
                        continue

                    prefix = self._get_item("prefix", ip_info, str, True)
                    mask_length = self._get_item("mask_length", ip_info, int, True)
                    if prefix:
                        s += ", " if s else ""
                        s += "IPv{} prefix {}".format(ip_ver, prefix)
                        if mask_length:
                            s += "/" + str(mask_length)

                if not s:
                    s = "VLAN with no details"
                else:
                    s = "VLAN " + s

                out_file.write(" - " + s + "\n")


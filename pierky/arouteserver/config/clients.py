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

from copy import deepcopy
import logging
import yaml

from .base import ConfigParserBase, convert_deprecated
from .validators import *
from ..errors import ConfigError, ARouteServerError


class ConfigParserClients(ConfigParserBase):

    ROOT = "clients"

    def __init__(self, general_cfg=None):
        ConfigParserBase.__init__(self)
        self.general_cfg = general_cfg

    def parse(self):

        def get_client_descr(client):
            client_descr = ""
            if "asn" in client:
                client_descr += "AS{}".format(client["asn"])
            if "ip" in client:
                client_descr += " " + client["ip"]
            if not client_descr:
                client_descr = "unknown client"
            return client_descr

        if "clients" not in self.cfg:
            raise ConfigError("Missing top 'clients' statement.")
        if "asns" in self.cfg:
            del self.cfg["asns"]

        errors = False

        schema = {
            "asn": ValidatorASN(),
            "ip": ValidatorIPAddr(),
            "description": ValidatorText(mandatory=False),
            "password": ValidatorText(mandatory=False),
            "cfg": {
                "prepend_rs_as": ValidatorBool(mandatory=False),
                "passive": ValidatorBool(mandatory=False),
                "gtsm": ValidatorBool(mandatory=False),
                "add_path": ValidatorBool(mandatory=False),
                "filtering": {
                    "next_hop": {
                        "policy": ValidatorOption("policy",
                                                  ("strict", "same-as",
                                                   "authorized_addresses"),
                                                  mandatory=False),
                        "authorized_addresses_list": ValidatorListOf(
                            ValidatorIPAddr, mandatory=False
                        )
                    },
                    "ipv4_pref_len": ValidatorIPMinMaxLen(4, mandatory=False),
                    "ipv6_pref_len": ValidatorIPMinMaxLen(6, mandatory=False),
                    "max_as_path_len": ValidatorMaxASPathLen(mandatory=False),
                    "reject_invalid_as_in_as_path": ValidatorBool(mandatory=False),
                    "irrdb": {
                        "as_sets": ValidatorListOf(ValidatorASSet,
                                                   mandatory=False),
                        "enforce_origin_in_as_set": ValidatorBool(mandatory=False),
                        "enforce_prefix_in_as_set": ValidatorBool(mandatory=False),
                        "white_list_pref": ValidatorListOf(
                            ValidatorPrefixListEntry, mandatory=False,
                        ),
                        "white_list_asn": ValidatorASNList(mandatory=False),
                        "white_list_route": ValidatorListOf(
                            ValidatorWhiteListRouteEntry, mandatory=False
                        )
                    },
                    "rpki_bgp_origin_validation": {
                        "enabled": ValidatorBool(mandatory=False),
                        "reject_invalid": ValidatorBool(mandatory=False),
                    },
                    "black_list_pref": ValidatorListOf(
                        ValidatorPrefixListEntry, mandatory=False,
                    ),
                    "max_prefix": {
                        "action": ValidatorOption(
                            "action",
                            ("shutdown", "restart", "block", "warning"),
                            mandatory=False
                        ),
                        "restart_after": ValidatorUInt(mandatory=False),
                        "peering_db": {
                            "enabled": ValidatorBool(mandatory=False),
                            "increment": {
                                "absolute": ValidatorUInt(mandatory=False),
                                "relative": ValidatorUInt(mandatory=False)
                            }
                        },
                        "limit_ipv4": ValidatorUInt(mandatory=False),
                        "limit_ipv6": ValidatorUInt(mandatory=False),
                    },
                    "reject_policy": {
                        "policy": ValidatorOption("reject_policy",
                                                  ("reject", "tag", "tag_and_reject"),
                                                  mandatory=False)
                    },
                },
                "blackhole_filtering" : {
                   "announce_to_client": ValidatorBool(mandatory=False),
                },
                "graceful_shutdown": {
                    "enabled": ValidatorBool(mandatory=False)
                },
                "attach_custom_communities": ValidatorListOf(ValidatorText,
                                                             mandatory=False)
            }
        }

        # Split configurations with more than one IP address into
        # multiple clients
        for client in self.cfg["clients"]:
            if "ip" in client:
                if isinstance(client["ip"], list):
                    for ip in client["ip"]:
                        client_clone = deepcopy(client)
                        client_clone["ip"] = ip
                        self.cfg["clients"].append(client_clone)
                    client["to_be_removed"] = True
        self.cfg["clients"] = [c for c in self.cfg["clients"] if "to_be_removed" not in c]

        # Clients' config validation
        for client in self.cfg["clients"]:
            client_descr = get_client_descr(client)

            try:
                # Convert next_hop_policy (< v0.6.0) into the new format
                if "cfg" in client:
                    convert_deprecated(client["cfg"])

                ConfigParserBase.validate(schema, client, "clients")
            except ARouteServerError as e:
                err_msg = ("One or more errors occurred while processing "
                           "the client configuration for "
                           "'{}'".format(client_descr))
                if str(e):
                    err_msg += ": " + str(e)
                logging.error(err_msg)
                raise ConfigError()

        def inherit_from_general_cfg(dest, src, schema):
            for k in schema:
                if isinstance(schema[k], dict):
                    if k in src:
                        inherit_from_general_cfg(dest[k], src[k], schema[k])
                else:
                    if k not in dest or dest[k] is None:
                        if k in src:
                            dest[k] = src[k]

        # Inherit missing options from the general configuration.
        if self.general_cfg:
            for client in self.cfg["clients"]:
                inherit_from_general_cfg(client["cfg"], self.general_cfg, schema["cfg"])

        # Duplicate IP addresses?
        unique_ip = []
        for client in self.cfg["clients"]:
            ip = client["ip"]
            if ip in unique_ip:
                logging.error(
                    "Duplicate IP address found: {}.".format(ip)
                )
                errors = True
            else:
                unique_ip.append(ip)

        # Clients with...
        # - next_hop.policy == "authorized_addresses" AND
        # - no authorized IP addresses
        # ... or with...
        # - "authorized_addresses_list" AND
        # - next_hop.policy != "authorized_addresses"
        for client in self.cfg["clients"]:
            client_descr = get_client_descr(client)
            next_hop = client["cfg"]["filtering"]["next_hop"]

            if next_hop["policy"] == "authorized_addresses" and \
                not next_hop["authorized_addresses_list"]:

                logging.error("The next_hop policy for client {} "
                              "is set to 'authorized_addresses' but "
                              "the list of authorized IP addresses "
                              "('authorized_addresses_list') is empty".format(
                                  client_descr
                                ))
                errors = True

            if next_hop["policy"] != "authorized_addresses" and \
                "authorized_addresses_list" in next_hop and \
                next_hop["authorized_addresses_list"] is not None:

                logging.error("The next_hop policy for client {} "
                              "is not 'authorized_addresses' but "
                              "the 'authorized_addresses_list' option "
                              "is set".format(
                                  client_descr
                                ))
                errors = True

        # Custom BGP communities must be declared within the general cfg
        for client in self.cfg["clients"]:
            client_descr = get_client_descr(client)

            if not client["cfg"]["attach_custom_communities"]:
                continue

            for comm in client["cfg"]["attach_custom_communities"]:
                if self.general_cfg and \
                    comm not in self.general_cfg["custom_communities"]:

                    logging.error("The custom BGP community {} "
                                  "referenced on client {} is not declared on "
                                  "the general configuration.".format(
                                    comm, client_descr
                                    ))
                    errors = True

        if errors:
            raise ConfigError()


def merge_clients(original, custom_file):
    try:
        new = yaml.safe_load(custom_file)
    except Exception as e:
        raise ConfigError(
            "Error while loading the YAML file: {e}".format(e=e)
        )

    if not new:
        raise ConfigError("The YAML file is empty")

    if "clients" not in new:
        raise ConfigError(
            "The top level 'clients' key is missing from the "
            "the set of clients to be merged."
        )

    if not isinstance(new["clients"], list):
        raise ConfigError(
            "The top level 'clients' key must represent a list "
            "of clients."
        )

    for client_id, client in enumerate(new["clients"]):
        try:
            if "ip" not in client:
                raise ConfigError(
                    "'ip' not found"
                )

            if not isinstance(client["ip"], str):
                raise ConfigError(
                    "'ip' must be a string representing the IP "
                    "address of the original client to be updated."
                )


            # The value of the 'ip' key of the dictionary that will
            # be used below to find the corresponding client and
            # to update it is overriden here with the normalised
            # representation of that IP.
            # This is done in order to avoid mismatching of IPs
            # represented in different ways (lower/upper case,
            # exploded vs compact form), and also to avoid
            # changing the way the IP was represented in
            # the original client definition.
            client["ip"] = ValidatorIPAddr().validate(client["ip"])

            for original_client in original["clients"]:
                if original_client["ip"] != client["ip"]:
                    continue

                if "add_if_missing" in client:
                    raise ConfigError(
                        "client {ip} already exists in the original "
                        "list of clients, but it's also reported in "
                        "the set of clients to be merged with the "
                        "'add_if_missing' attribute set.".format(
                            ip=client["ip"]
                        )
                    )

                # A client having the same IP is present in the
                # list of original clients. It's the one to update
                # with the settings from the custom one.
                original_client.update(client)
                break
            else:
                # No clients to update were found.
                # If the custom one has the 'add_if_missing' key
                # set to True, the custom one can be added to the
                # list of clients.
                if client.pop("add_if_missing", False):
                    original["clients"].append(client)

        except ConfigError as e:
            raise ConfigError(
                "Error while processing the client n. {n} from "
                "the set of clients to be merged: {e}".format(
                    n=client_id + 1,
                    e=e
                )
            )
    try:
        new_res_after_merge = deepcopy(original)
        ConfigParserClients().load_from_dict(new_res_after_merge)
    except ARouteServerError:
        raise ConfigError(
            "Validation of the final clients file failed: "
            "check the logs for more details."
        )

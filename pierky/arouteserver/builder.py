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

import ipaddr
import logging
import os

from jinja2 import Environment, FileSystemLoader

from .config.general import ConfigParserGeneral
from .config.bogons import ConfigParserBogons
from .config.clients import ConfigParserClients
from .errors import MissingDirError, MissingFileError, BuilderError, \
                    ARouteServerError, PeeringDBError, PeeringDBNoInfoError, \
                    MissingArgumentError
from .rpsl import ASSet, RSet
from .peering_db import PeeringDBNet


class ConfigBuilder(object):

    def validate_flavor_specific_configuration(self):
        raise NotImplementedError()

    @staticmethod
    def _get_cfg(obj_or_path, cls, descr, **kwargs):
        assert obj_or_path is not None
        if isinstance(obj_or_path, cls):
            return obj_or_path
        elif isinstance(obj_or_path, str):
            if not os.path.isfile(obj_or_path):
                raise MissingFileError(obj_or_path)
            obj = cls(**kwargs)
            try:
                obj.load(obj_or_path)
            except ARouteServerError as e:
                raise BuilderError(
                    "One or more errors occurred while loading "
                    "{} configuration file{}".format(
                        descr, ": {}".format(str(e)) if str(e) else ""
                    )
                )
            return obj

    @staticmethod
    def _check_is_dir(arg, path):
        if path is None:
            raise MissingArgumentError(arg)
        if not os.path.isdir(path):
            raise MissingDirError(path)
        return path

    def __init__(self, **kwargs):

        self.template_dir = self._check_is_dir(
            "template_dir", kwargs.get("template_dir")
        )

        self.template_name = kwargs.get("template_name")
        if not self.template_name:
            raise MissingArgumentError("template_name")

        self.template_path = os.path.join(self.template_dir,
                                          self.template_name)
        if not os.path.isfile(self.template_path):
            raise MissingFileError(self.template_path)

        self.cache_dir = self._check_is_dir(
            "cache_dir", kwargs.get("cache_dir")
        )

        self.cache_expiry = kwargs.get("cache_expiry")

        self.bgpq3_path = kwargs.get("bgpq3_path")

        try:
            with open(os.path.join(self.cache_dir, "write_test"), "w") as f:
                f.write("OK")
        except Exception as e:
            raise BuilderError(
                "Can't write into cache dir {}: {}".format(
                    self.cache_dir, str(e)
                )
            )

        self.ip_ver = kwargs.get("ip_ver", None)
        if self.ip_ver is not None:
            self.ip_ver = int(self.ip_ver)
            if self.ip_ver not in (4, 6):
                raise BuilderError("Invalid IP version: {}".format(ip_ver))

        self.cfg_general = self._get_cfg(kwargs.get("cfg_general"),
                                         ConfigParserGeneral,
                                         "general")
        self.cfg_bogons = self._get_cfg(kwargs.get("cfg_bogons"),
                                        ConfigParserBogons,
                                        "bogons")
        self.cfg_clients = self._get_cfg(kwargs.get("cfg_clients"),
                                         ConfigParserClients,
                                         "clients",
                                         general_cfg=self.cfg_general)

        self.validate_flavor_specific_configuration()

        self.enrich_config()

    def enrich_config_rpsl_as_set(self, client_id, as_sets, dest_list):
        errors = False
        for as_set in as_sets:
            try:
                asns = ASSet(as_set,
                             bgpq3_path=self.bgpq3_path,
                             cache_dir=self.cache_dir,
                             cache_expiry=self.cache_expiry).asns
                if not asns:
                    raise BuilderError("it's empty")
                dest_list.extend(
                    [asn for asn in asns if asn not in dest_list]
                )
            except ARouteServerError as e:
                errors = True
                logging.error(
                    "Error while retrieving as_set {} for {}: {}".format(
                        as_set, client_id, str(e)
                    )
                )

        if errors:
            raise BuilderError()

    def enrich_config_rpsl_r_set(self, client_id, as_sets, dest_list):
        errors = False
        ip_versions = [self.ip_ver] if self.ip_ver else [4, 6]
        for as_set in as_sets:
            for ip_ver in ip_versions:
                try:
                    prefixes = RSet(as_set, ip_ver,
                                    bgpq3_path=self.bgpq3_path,
                                    cache_dir=self.cache_dir,
                                    cache_expiry=self.cache_expiry).prefixes
                    if not prefixes:
                        raise BuilderError("it's empty")
                    dest_list.extend(
                        prefixes
                    )
                except ARouteServerError as e:
                    errors = True
                    logging.error(
                        "Error while retrieving r_set "
                        "{} for {} IPv{}: {}".format(
                            as_set, client_id, ip_ver, str(e)
                        )
                    )

        if errors:
            raise BuilderError()

    def enrich_config_rpsl(self, client):
        client_rpsl = client["cfg"]["filtering"]["rpsl"]
        if not client_rpsl["enforce_origin_in_as_set"] and \
            not client_rpsl["enforce_prefix_in_as_set"] and \
            not self.cfg_general["filtering"]["rpsl"]["tag_as_set"]:

            return

        client["cfg"]["filtering"]["rpsl"]["as_set_asns"] = []
        client["cfg"]["filtering"]["rpsl"]["as_set_prefixes"] = []

        if client["cfg"]["filtering"]["rpsl"]["as_sets"]:
            as_sets = client["cfg"]["filtering"]["rpsl"]["as_sets"]
        else:
            as_sets = ["AS{}".format(client["as"])]

        errors = False
        try:
            self.enrich_config_rpsl_as_set(
                client["id"],
                as_sets,
                client["cfg"]["filtering"]["rpsl"]["as_set_asns"]
            )
        except ARouteServerError as e:
            errors = True
            logging.error(
                "One or more errors occurred while expanding client's "
                "AS-SETs to obtain the list of allowed origin ASNs; "
                "client ID: {}".format(client["id"])
            )

        try:
            self.enrich_config_rpsl_r_set(
                client["id"],
                as_sets,
                client["cfg"]["filtering"]["rpsl"]["as_set_prefixes"]
            )
        except ARouteServerError as e:
            errors = True
            logging.error(
                "One or more errors occurred while expanding client's "
                "AS-SETs to obtain the list of allowed prefixes; "
                "client ID: {}".format(client["id"])
            )

        if errors:
            raise BuilderError()

    def enrich_config_peeringdb(self, client):
        client_max_prefix = client["cfg"]["filtering"]["max_prefix"]
        if not client_max_prefix["action"]:
            # No max-prefix action given for this client:
            # no needs to know its max-pref limit.
            return

        if client_max_prefix["limit_ipv{}".format(self.ip_ver)]:
            # Client uses a specific limit:
            # no needs to gather info from PeeringDB.
            return

        general_limit_ipv4 = self.cfg_general["filtering"]["max_prefix"]["general_limit_ipv4"]
        general_limit_ipv6 = self.cfg_general["filtering"]["max_prefix"]["general_limit_ipv6"]

        if not client_max_prefix["peering_db"]:
            client_max_prefix["limit_ipv4"] = general_limit_ipv4
            client_max_prefix["limit_ipv6"] = general_limit_ipv6
            return
        
        try:
            net = PeeringDBNet(client["as"],
                               cache_dir=self.cache_dir,
                               cache_expiry=self.cache_expiry)
            client_max_prefix["limit_ipv4"] = net.info_prefixes4 or general_limit_ipv4
            client_max_prefix["limit_ipv6"] = net.info_prefixes6 or general_limit_ipv6

        except PeeringDBNoInfoError:
            # No data found on PeeringDB.
            pass
        except PeeringDBError as e:
            raise BuilderError(
                "An error occurred while retrieving info from PeeringDB "
                "for ASN {}: {}".format(
                    client["as"], str(e) or "error unknown"
                )
            )

    def enrich_config(self):
        errors = False

        # Unique ASNs from clients list.
        clients_asns = {}

        for client in self.cfg_clients.cfg["clients"]:
            # Unique ASNs
            asn = "AS{}".format(client["as"])
            if asn in clients_asns:
                clients_asns[asn] += 1
            else:
                clients_asns[asn] = 1

            # Client's ID
            # Set 'id' as ASx_y where
            # x = ASN
            # y = progressive counter of clients per ASN
            client_id = "{}_{}".format(
                asn, clients_asns[asn]
            )
            client["id"] = client_id

            # RPSL info
            try:
                self.enrich_config_rpsl(client)
            except ARouteServerError as e:
                errors = True
                if str(e):
                    logging.error(str(e))

            # PeerindDB info
            try:
                self.enrich_config_peeringdb(client)
            except ARouteServerError as e:
                errors = True
                if str(e):
                    logging.error(str(e))

        if errors:
            raise BuilderError()

    def render_template(self):
        data = {}
        data["ip_ver"] = self.ip_ver
        data["cfg"] = self.cfg_general
        data["bogons"] = self.cfg_bogons
        data["clients"] = self.cfg_clients

        def current_ipver(ip):
            if self.ip_ver is None:
                return True
            return ipaddr.IPAddress(ip).version == self.ip_ver

        def community_is_set(comm):
            if not comm:
                return False
            if not comm["std"] and not comm["lrg"] and not comm["ext"]:
                return False
            return True

        env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        env.tests["current_ipver"] = current_ipver
        env.filters["community_is_set"] = community_is_set

        tpl = env.get_template(self.template_name)
        return tpl.render(data)

class BIRDConfigBuilder(ConfigBuilder):

    def validate_flavor_specific_configuration(self):
        if self.ip_ver is None:
            raise BuilderError(
                "An explicit target IP version is needed "
                "to build BIRD configuration. Use the "
                "--ip-ver command line argument to supply one."
            )

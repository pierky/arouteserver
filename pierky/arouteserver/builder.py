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
import re
import time

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .config.general import ConfigParserGeneral
from .config.bogons import ConfigParserBogons
from .config.asns import ConfigParserASNS
from .config.clients import ConfigParserClients
from .config.roa import ConfigParserROAEntries
from .errors import MissingDirError, MissingFileError, BuilderError, \
                    ARouteServerError, PeeringDBError, PeeringDBNoInfoError, \
                    MissingArgumentError
from .rpsl import ASSet, RSet
from .cached_objects import CachedObject
from .peering_db import PeeringDBNet


class ConfigBuilder(object):

    def validate_flavor_specific_configuration(self):
        pass

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

    def __init__(self, template_dir=None, template_name=None,
                 cache_dir=None, cache_expiry=CachedObject.DEFAULT_EXPIRY,
                 bgpq3_path="bgpq3", ip_ver=None,
                 cfg_general=None, cfg_bogons=None, cfg_clients=None,
                 cfg_roas=None):

        self.template_dir = self._check_is_dir(
            "template_dir", template_dir
        )

        self.template_name = template_name
        if not self.template_name:
            raise MissingArgumentError("template_name")

        self.template_path = os.path.join(self.template_dir,
                                          self.template_name)
        if not os.path.isfile(self.template_path):
            raise MissingFileError(self.template_path)

        self.cache_dir = self._check_is_dir(
            "cache_dir", cache_dir
        )

        self.cache_expiry = cache_expiry

        self.bgpq3_path = bgpq3_path

        try:
            with open(os.path.join(self.cache_dir, "write_test"), "w") as f:
                f.write("OK")
        except Exception as e:
            raise BuilderError(
                "Can't write into cache dir {}: {}".format(
                    self.cache_dir, str(e)
                )
            )

        self.ip_ver = ip_ver
        if self.ip_ver is not None:
            self.ip_ver = int(self.ip_ver)
            if self.ip_ver not in (4, 6):
                raise BuilderError("Invalid IP version: {}".format(ip_ver))

        self.cfg_general = self._get_cfg(cfg_general,
                                         ConfigParserGeneral,
                                         "general")
        self.cfg_bogons = self._get_cfg(cfg_bogons,
                                        ConfigParserBogons,
                                        "bogons")
        self.cfg_asns = self._get_cfg(cfg_clients,
                                         ConfigParserASNS,
                                         "asns")
        self.cfg_clients = self._get_cfg(cfg_clients,
                                         ConfigParserClients,
                                         "clients",
                                         general_cfg=self.cfg_general)
        if cfg_roas:
            self.cfg_roas = self._get_cfg(cfg_roas, ConfigParserROAEntries, "roas")
        else:
            self.cfg_roas = None

        logging.info("Started processing configuration "
                     "for {}".format(self.template_path))

        start_time = int(time.time())

        self.validate_flavor_specific_configuration()

        self.enrich_config()

        stop_time = int(time.time())

        logging.info("Configuration processing completed after "
                     "{} seconds.".format(stop_time - start_time))

    def enrich_config_rpsl_as_set(self, dest_descr, as_set, dest_list):
        errors = False
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
                    as_set, dest_descr, str(e)
                )
            )

        if errors:
            raise BuilderError()

    def enrich_config_rpsl_r_set(self, dest_descr, as_set, dest_list):
        errors = False
        ip_versions = [self.ip_ver] if self.ip_ver else [4, 6]
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
                        as_set, dest_descr, ip_ver, str(e)
                    )
                )

        if errors:
            raise BuilderError()

    def enrich_config_rpsl(self):
        self.as_sets = []
        errors = False

        def normalize_as_set_id(s):
            return re.sub("[^a-zA-Z0-9_]", "_", s)

        def get_as_set_by_name(name, used_by_client=None):
            for as_set in self.as_sets:
                if as_set["name"] == name:
                    if used_by_client:
                        as_set["used_by"].append(used_by_client)
                    return as_set
            return None

        def use_as_set(as_set_name, used_by_client=None):
            # Returns: id of the added/existing as_set
            existing = get_as_set_by_name(as_set_name)
            if existing:
                if used_by_client:
                    existing["used_by"].append(used_by_client)
                return existing["id"]

            new_as_set_id = normalize_as_set_id(as_set_name)
            self.as_sets.append({
                "id": new_as_set_id,
                "name": as_set_name,
                "asns": [],
                "prefixes": [],
                "used_by": [used_by_client] if used_by_client else []
            })
            return new_as_set_id

        # Add to as_sets all the AS-SETs reported in the 'asns' section.
        for asn in self.cfg_asns.cfg["asns"]:
            self.cfg_asns[asn]["as_set_ids"] = []

            if not self.cfg_asns[asn]["as_sets"]:
                continue

            for as_set in self.cfg_asns[asn]["as_sets"]:
                self.cfg_asns[asn]["as_set_ids"].append(
                    use_as_set(as_set)
                )

        # Add to as_sets all the AS-SETs reported in the 'clients' section.
        for client in self.cfg_clients.cfg["clients"]:
            client_rpsl = client["cfg"]["filtering"]["rpsl"]
            client_rpsl["as_set_ids"] = []

            if not client_rpsl["enforce_origin_in_as_set"] and \
                not client_rpsl["enforce_prefix_in_as_set"] and \
                not self.cfg_general["filtering"]["rpsl"]["tag_as_set"]:
                    # Client does not require AS-SETs info to be gathered.
                    continue

            if client_rpsl["as_sets"]:
                # Client has its own specific set of AS-SETs.
                for as_set in client_rpsl["as_sets"]:
                    client_rpsl["as_set_ids"].append(
                        use_as_set(as_set, "client {}".format(client["id"]))
                    )
                continue

            # Client needs AS-SETs info but has not its own set of AS-SETs.

            # If client's ASN is configured in the 'asns' section and has
            # one or more AS-SETs, the client configuration will be based
            # on those.
            asn = "AS{}".format(client["asn"])
            if asn in self.cfg_asns.cfg["asns"] and \
                self.cfg_asns.cfg["asns"][asn]["as_sets"]:
                for as_set in self.cfg_asns.cfg["asns"][asn]["as_sets"]:
                    client_rpsl["as_set_ids"].append(
                        use_as_set(as_set, "client {}".format(client["id"]))
                    )
                continue

            # No AS-SETs found for the client's ASN in the 'asns' section.
            logging.warning("No AS-SET provided for the '{}' client. "
                            "Only AS{} will be expanded.".format(
                                client["id"], client["asn"]
                            ))

            client_rpsl["as_set_ids"].append(
                use_as_set("AS{}".format(client["asn"]),
                           "client {}".format(client["id"]))
            )

        # Removing unreferenced AS-SETs.
        for as_set in self.as_sets:
            if not as_set["used_by"]:
                logging.debug("Removing unreferenced AS-SET: "
                              "{}".format(as_set["name"]))
        self.as_sets = [as_set for as_set in self.as_sets if as_set["used_by"]]

        # Gathering info.
        for as_set in self.as_sets:
            used_by = ", ".join(as_set["used_by"])
            try:
                self.enrich_config_rpsl_as_set(used_by, as_set["name"],
                                               as_set["asns"])
            except ARouteServerError as e:
                errors = True
                if str(e):
                    logging.error(str(e))
            try:
                self.enrich_config_rpsl_r_set(used_by, as_set["name"],
                                              as_set["prefixes"])
            except ARouteServerError as e:
                errors = True
                if str(e):
                    logging.error(str(e))

        if errors:
            raise BuilderError()

    def enrich_config_peeringdb(self, client):
        client_max_prefix = client["cfg"]["filtering"]["max_prefix"]
        if not client_max_prefix["action"]:
            # No max-prefix action given for this client:
            # no needs to know its max-pref limit.
            return

        for ip_ver in (4, 6):
            if self.ip_ver is not None and self.ip_ver != ip_ver:
                continue

            if client_max_prefix["limit_ipv{}".format(ip_ver)]:
                # Client uses a specific limit:
                # no needs to gather info from PeeringDB.
                return

            general_limit = self.cfg_general["filtering"]["max_prefix"]["general_limit_ipv{}".format(ip_ver)]

            if not client_max_prefix["peering_db"]:
                client_max_prefix["limit_ipv{}".format(ip_ver)] = general_limit
                continue
        
            try:
                net = PeeringDBNet(client["asn"],
                                cache_dir=self.cache_dir,
                                cache_expiry=self.cache_expiry)
                if ip_ver == 4:
                    peeringdb_limit = net.info_prefixes4
                else:
                    peeringdb_limit = net.info_prefixes6

                client_max_prefix["limit_ipv{}".format(ip_ver)] = peeringdb_limit or general_limit

            except PeeringDBNoInfoError:
                # No data found on PeeringDB.
                logging.debug("No data found on PeeringDB "
                            "for AS{} while looking for "
                            "max-prefix limit.".format(client["asn"]))
                pass
            except PeeringDBError as e:
                raise BuilderError(
                    "An error occurred while retrieving info from PeeringDB "
                    "for ASN {}: {}".format(
                        client["asn"], str(e) or "error unknown"
                    )
                )

    def enrich_config_communities(self):
        for comm_name in ConfigParserGeneral.COMMUNITIES_SCHEMA:
            comm = ConfigParserGeneral.COMMUNITIES_SCHEMA[comm_name]
            self.cfg_general["communities"][comm_name]["type"] = comm["type"]
            self.cfg_general["communities"][comm_name]["peer_as"] = comm.get("peer_as", False)

    def enrich_config(self):
        errors = False

        # Unique ASNs from clients list.
        clients_asns = {}

        for client in self.cfg_clients.cfg["clients"]:
            # Unique ASNs
            asn = "AS{}".format(client["asn"])
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

        # RPSL info.
        try:
            self.enrich_config_rpsl()
        except ARouteServerError as e:
            errors = True
            if str(e):
                logging.error(str(e))

        # PeerindDB info
        for client in self.cfg_clients.cfg["clients"]:
            try:
                self.enrich_config_peeringdb(client)
            except ARouteServerError as e:
                errors = True
                if str(e):
                    logging.error(str(e))

        # Communities meta-data useful in J2 templates
        self.enrich_config_communities()

        if errors:
            raise BuilderError()

    def render_template(self):
        data = {}
        data["ip_ver"] = self.ip_ver
        data["cfg"] = self.cfg_general
        data["bogons"] = self.cfg_bogons
        data["clients"] = self.cfg_clients
        data["asns"] = self.cfg_asns
        data["as_sets"] = self.as_sets
        data["roas"] = self.cfg_roas

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
            lstrip_blocks=True,
            undefined=StrictUndefined
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

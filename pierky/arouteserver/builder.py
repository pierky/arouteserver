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
import yaml

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .config.general import ConfigParserGeneral
from .config.bogons import ConfigParserBogons
from .config.asns import ConfigParserASNS
from .config.clients import ConfigParserClients
from .config.roa import ConfigParserROAEntries
from .enrichers.irrdb import IRRDBConfigEnricher_OriginASNs, \
                             IRRDBConfigEnricher_Prefixes
from .enrichers.peeringdb import PeeringDBConfigEnricher
from .errors import MissingDirError, MissingFileError, BuilderError, \
                    ARouteServerError, PeeringDBError, PeeringDBNoInfoError, \
                    MissingArgumentError, TemplateRenderingError
from .irrdb import ASSet, RSet, IRRDBTools
from .cached_objects import CachedObject
from .peering_db import PeeringDBNet


class ConfigBuilder(object):

    def validate_flavor_specific_configuration(self):
        pass

    def enrich_j2_environment(self, env):
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
                 bgpq3_path="bgpq3", bgpq3_host=IRRDBTools.BGPQ3_DEFAULT_HOST,
                 bgpq3_sources=IRRDBTools.BGPQ3_DEFAULT_SOURCES, threads=4,
                 ip_ver=None,
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
        self.bgpq3_host = bgpq3_host
        self.bgpq3_sources = bgpq3_sources

        self.threads = threads

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

        self.as_sets = None

        logging.info("Started processing configuration "
                     "for {}".format(self.template_path))

        start_time = int(time.time())

        self.validate_flavor_specific_configuration()

        self.enrich_config()

        stop_time = int(time.time())

        logging.info("Configuration processing completed after "
                     "{} seconds.".format(stop_time - start_time))

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

        # BGP communities metadata
        for comm_name in ConfigParserGeneral.COMMUNITIES_SCHEMA:
            comm = ConfigParserGeneral.COMMUNITIES_SCHEMA[comm_name]
            self.cfg_general["communities"][comm_name]["type"] = comm["type"]
            self.cfg_general["communities"][comm_name]["peer_as"] = comm.get("peer_as", False)

        # Enrichers
        for enricher_class in (IRRDBConfigEnricher_OriginASNs,
                               IRRDBConfigEnricher_Prefixes,
                               PeeringDBConfigEnricher):
            enricher = enricher_class(self, threads=self.threads)
            try:
                enricher.enrich()
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

        self.enrich_j2_environment(env)

        tpl = env.get_template(self.template_name)
        try:
            return tpl.render(data)
        except Exception as e:
            raise TemplateRenderingError(str(e))

class BIRDConfigBuilder(ConfigBuilder):

    def validate_flavor_specific_configuration(self):
        if self.ip_ver is None:
            raise BuilderError(
                "An explicit target IP version is needed "
                "to build BIRD configuration. Use the "
                "--ip-ver command line argument to supply one."
            )

class TemplateContextDumper(ConfigBuilder):

    def enrich_j2_environment(self, env):

        def to_yaml(obj):
            return yaml.dump(obj, default_flow_style=False)

        env.filters["to_yaml"] = to_yaml

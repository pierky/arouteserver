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

from aggregate6 import aggregate
import logging
import os
from packaging import version
import sys
import time
import yaml

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .config.general import ConfigParserGeneral
from .config.bogons import ConfigParserBogons
from .config.asns import ConfigParserASNS
from .config.clients import ConfigParserClients
from .enrichers.arin_db_dump import ARINWhoisDBDumpEnricher
from .enrichers.registrobr_db_dump import RegistroBRWhoisDBDumpEnricher
from .enrichers.irrdb import IRRDBConfigEnricher_ASNs, \
                             IRRDBConfigEnricher_Prefixes
from .enrichers.pdb_as_set import PeeringDBConfigEnricher_ASSet
from .enrichers.pdb_max_prefix import PeeringDBConfigEnricher_MaxPrefix
from .enrichers.pdb_never_via_route_servers import NeverViaRouteServersEnricher
from .enrichers.rpki_roas import RPKIROAsEnricher
from .enrichers.rtt import RTTGetterConfigEnricher
from .errors import MissingDirError, MissingFileError, BuilderError, \
                    ARouteServerError, MissingArgumentError, \
                    TemplateRenderingError, CompatibilityIssuesError, \
                    ConfigError, MissingGeneralConfigFileError
from .ipaddresses import IPNetwork
from .irrdb import IRRDBInfo
from .cached_objects import CachedObject, normalize_expiry_time


class ConfigBuilder(object):
    """The base configuration builder class.

    This class must be derived by BGP-daemon-specific classes.
    """

    LOCAL_FILES_IDS = None
    LOCAL_FILES_BASE_DIR = None

    DEFAULT_VERSION = None

    IGNORABLE_ISSUES = []

    REJECT_REASONS = {
        "1": "Invalid AS_PATH length",
        "2": "Prefix is bogon",
        "3": "Prefix is in global blacklist",
        "4": "Invalid AFI",
        "5": "Invalid NEXT_HOP",
        "6": "Invalid left-most ASN",
        "7": "Invalid ASN in AS_PATH",
        "8": "Transit-free ASN in AS_PATH",
        "9": "Origin ASN not in IRRDB AS-SETs",
        "10": "IPv6 prefix not in global unicast space",
        "11": "Prefix is in client blacklist",
        "12": "Prefix not in IRRDB AS-SETs",
        "13": "Invalid prefix length",
        "14": "RPKI INVALID route",
        "15": "Never via route-servers ASN in AS_PATH",
    }

    def validate_bgpspeaker_specific_configuration(self):
        """Check compatibility between config and target BGP speaker

        Returns:
            True if there are no compatibility issues;
            False if there are compatibility issues that can be acknowledged
            via command line argument.
        Raises exception in case of blocking errors.
        """
        return True

    def process_bgpspeaker_specific_compatibility_issue(self, issue_id, text):
        """Process a compatibility issue with the target BGP speaker

        If the issue has been ignored via command-line, logs a warning
        message and returns True.
        Otherwise, logs an error message and returns False.

        """
        assert issue_id in self.IGNORABLE_ISSUES

        msg = "Compatibility issue ID '{}'. {}".format(issue_id, text)
        if issue_id in self.ignore_errors or "*" in self.ignore_errors:
            logging.warning(
                "{} - Ignored".format(msg)
            )
            return True
        logging.error(msg)
        return False

    def enrich_j2_environment(self, env):
        pass

    @staticmethod
    def _get_cfg(obj_or_path, cls, descr, **kwargs):
        assert obj_or_path is not None
        if isinstance(obj_or_path, cls):
            return obj_or_path
        elif isinstance(obj_or_path, str):
            path = os.path.expanduser(obj_or_path)
            if not os.path.isfile(path):
                raise MissingFileError(path)
            obj = cls(**kwargs)
            try:
                obj.load(path)
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
        dir_path = os.path.expanduser(path)
        if not os.path.isdir(dir_path):
            raise MissingDirError(path)
        return dir_path

    def __init__(self, template_dir=None, template_name=None,
                 cache_dir=None, cache_expiry=CachedObject.DEFAULT_EXPIRY,
                 bgpq3_path="bgpq3", bgpq3_host=IRRDBInfo.BGPQ3_DEFAULT_HOST,
                 bgpq3_sources=IRRDBInfo.BGPQ3_DEFAULT_SOURCES,
                 rtt_getter_path=None, threads=4,
                 ip_ver=None, perform_graceful_shutdown=False,
                 ignore_errors=[], live_tests=False,
                 local_files=[], local_files_dir=None, target_version=None,
                 cfg_general=None, cfg_bogons=None, cfg_clients=None,
                 **kwargs):
        """Initialize the configuration builder.

        Here, external data sources are also queried to enrich the
        configuration with additional data (PeeringDB records, ASNs and
        prefixes from IRRDBs, ...).

        Raises:

            ARouteServerError or derived exceptions
              (from pierky.arouteserver.errors).

              Exceptions raised here can have no arguments and their string
              representation can be empty: in these cases, it means that
              one or more errors have been logged using the ``logging`` module.

        Args:

            template_dir (str): the directory that contains the templates
                that must be used to render the output configuration.

                Example: /home/user/arouteserver/templates/bird

                Same of:

                - *--templates-dir* CLI argument.
                - *templates_dir* program's configuration file option.

            template_name (str): the name of the file that must be used to
                render the output configuration.

                Example: main.j2

                Same of:

                - *--template-file-name* CLI argument.
                - *template_name* program's configuration file option.

            cfg_general (str)
            cfg_clients (str)
            cfg_bogons (str): paths to the YAML
                files containing the general route server policy, the clients
                list and the list of bogon prefixes.

                Example: ``cfg_general="/home/user/arouteserver/general.yml"``

                Same of:

                - *--general*, *--clients*, *--bogons* CLI arguments.
                - *cfg_general*, *cfg_clients*, *cfg_bogons* program's
                  configuration file options.

            cache_dir (str): the directory that will be used to store results
                from external data sources queries (PeeringDB info, IRRDBs).

                Same of:

                - *--cache-dir* CLI argument.
                - *cache_dir* program's configuration file option.

            cache_expiry (int or dict): how long cached data must be considered
                valid, in seconds. Each "cacheable object" (PeeringDB info,
                IRR datasets, ...) can have its own expiry time. If an int is
                given here, all the expiry times will have the same duration,
                otherwise cacheable objects will pick their specific value
                or use the 'general' one if no more specific value is given.

                Same of:

                - *cache_expiry* program's configuration file option.

            ip_ver (int): if *None*, the output configuration will be targeted
                for both IPv4 and IPv6; otherwise, set this to *4* or to
                *6* to obtain AFI-specific output configuration.

                Same of:

                - *--ip-ver* CLI argument.

            perform_graceful_shutdown (bool): when True, the output config
                includes an outbound policy which is applied to BGP
                sessions toward the clients and which adds the
                GRACEFUL_SHUTDOWN BGP community (65535:0) to all the
                routes that the route server announces to them.

                Same of:

                - *--perform-graceful-shutdown* CLI argument.

            target_version (str): the BGP daemon target version for which the
                output configuration must be generated.

                This is used to detect and/or solve any compatibility issue
                with some features that are available only using a specific
                version of the target BGP daemon.

                The list of available versions is taken from the derived BGP
                daemon specific classes' ``AVAILABLE_VERSION`` attribute.

                The default value is taken from the derived BGP daemon
                specific classes' ``DEFAULT_VERSION`` attribute.

                Example: on OpenBGPD, to avoid errors when building configs
                that use large BGP communities (available only on
                OpenBGPD/OpenBSD > 6.1) use ``target_version="6.1"``

                Same of:

                - *--target-version* CLI argument.

            ignore_errors (list): a list of issue IDs (strings) that must be
                ignored when building the configuration.

                Depending on the target BGP daemon and its version, some
                features may be unavailable; ARouteServer produces errors
                when one or more of these features are enabled in the route
                server configuration YAML file. These errors are marked with
                an 'issue ID' that can be reported in this list to instruct
                ARouteServer to ignore it and to continue the building process.

                Use ``ignore_errors=["*"]`` to ignore any issue.

                Example: ``ignore_errors=["add_path"]`` to ignore the issue due
                to the lack of support for ADD_PATH in OpenBGPD.

                Same of:

                - *--ignore-issues* CLI argument.

            local_files (list): the list of local files IDs for which the
                relative inclusion point must be enabled on the output
                configuration. Details: https://arouteserver.readthedocs.io/en/latest/CONFIG.html#site-specific-custom-configuration-files

                The list of available IDs is taken from the derived BGP daemon
                specific classes' ``LOCAL_FILES_IDS`` attribute.

                Example: ``local_files=["header4", "footer4"]``

                Same of:

                - *--use-local-files* CLI argument.

            local_files_dir (str): the base directory of the local files that
                will be included in the output configuration.

                The default value is taken from the derived BGP daemon
                specific classes' ``LOCAL_FILES_BASE_DIR`` attribute.

                Example: /etc/bird

                Same of:

                - *--local-files-dir* CLI argument.

            bgpq3_path (str): path to the 'bgpq3' or 'bgpq4' external program; this will
                be used to expand AS macros and to obtain the list of
                authorized origin ASNs and prefixes from IRRDBs.

                Same of:

                - *bgpq3_path* program's configuration file option.

            bgpq3_host (str): the host that will be queried by bgpq3/bgpq4; this
                will be used to set the *-h* argument of the program.

                Same of:

                - *bgpq3_host* program's configuration file option.

            bgpq3_sources (str): a comma separated list of sources that will
                be used by the bgpq3/bgpq4 program; this will be used to set the
                *-S* argument of the program.

                Same of:

                - *bgpq3_sources* program's configuration file option.

            rtt_getter_path (str): path to the program that is executed to
                determine the RTT of a peer.
                Syntax and details can be found at the following URL:
                https://arouteserver.readthedocs.io/en/latest/RTT_GETTER.html

                Same of:

                - *rtt_getter_path* program's configuration file option.

            threads (int): number of concurrent threads used to gather
                additional data from external sources (bgpq3/bgpq4, PeeringDB, ...)

                Same of:

                - *threads* program's configuration file option.

            kwargs: additional arguments used by BGP daemon specific builder
                classes.

            live_tests (bool): only used on live tests.
        """

        # Parameters initialization

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

        self.cache_expiry = normalize_expiry_time(cache_expiry)

        self.bgpq3_path = bgpq3_path
        self.bgpq3_host = bgpq3_host
        self.bgpq3_sources = bgpq3_sources

        self.rtt_getter_path = rtt_getter_path

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

        self.perform_graceful_shutdown = perform_graceful_shutdown

        self.ignore_errors = ignore_errors or []

        self.live_tests = live_tests

        self.local_files = local_files
        self.local_files_dir = local_files_dir

        self.target_version = target_version or self.DEFAULT_VERSION

        try:
            self.cfg_general = self._get_cfg(cfg_general,
                                             ConfigParserGeneral,
                                             "general")
        except MissingFileError as e:
            raise MissingGeneralConfigFileError(e.path)

        self.cfg_bogons = self._get_cfg(cfg_bogons,
                                        ConfigParserBogons,
                                        "bogons")

        if isinstance(cfg_clients, str):
            self.cfg_asns = self._get_cfg(cfg_clients,
                                            ConfigParserASNS,
                                            "asns")
        else:
            self.cfg_asns = ConfigParserASNS()
            self.cfg_asns._load_from_yaml("{}")
            self.cfg_asns.parse()

        self.cfg_clients = self._get_cfg(cfg_clients,
                                         ConfigParserClients,
                                         "clients",
                                         general_cfg=self.cfg_general)

        self.kwargs = kwargs

        # Initially None; is set to IRRDB() and finally populated by
        # the IRRDB enrichers.
        # { "<as_set_bundle_id>": <IRRDBRecord>, ... }
        self.irrdb_info = None

        # { "<len>": [{"prefix": "<ip>/<len>", "max_len": x, "asn": "AS<n>"}]
        self.rpki_roas = {}

        # [<asn (int)>]
        self.never_via_route_servers_asns = []

        # { "<origin_asn>": ["a/b", "c/d"] }
        self.arin_whois_records = {}
        self.registrobr_whois_records = {}

        # Validation

        if self.local_files:
            if not isinstance(self.local_files, list):
                raise BuilderError(
                    "local_files must be a list of .local files IDs"
                )
            for local_file_id in self.local_files:
                if local_file_id not in self.LOCAL_FILES_IDS:
                    raise BuilderError(
                        "The .local file ID '{}' is invalid.".format(
                            local_file_id
                        )
                    )

        if not self.validate_bgpspeaker_specific_configuration():
            raise CompatibilityIssuesError(
                "One or more compatibility issues have been found."
            )

        # Processing

        logging.info("Started processing configuration "
                     "for {}".format(self.template_path))

        start_time = int(time.time())

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
        # Order matters: AS-SET from PeeringDB must be run first
        # in order to acquire missing AS-SETs that are processed
        # later by IRRDB enrichers. RPKI ROAs (when only used as
        # route objects) are processed only
        # for those origin ASNs that have been gathered from AS-SETs.
        filtering = self.cfg_general["filtering"]
        irrdb_cfg = filtering["irrdb"]
        used_enricher_classes = []

        if irrdb_cfg["peering_db"]:
            used_enricher_classes += [PeeringDBConfigEnricher_ASSet]

        used_enricher_classes += [IRRDBConfigEnricher_ASNs,
                                  IRRDBConfigEnricher_Prefixes,
                                  PeeringDBConfigEnricher_MaxPrefix]

        if self.cfg_general.rtt_based_functions_are_used:
            used_enricher_classes.append(RTTGetterConfigEnricher)

        if self.cfg_general.rpki_roas_needed and \
            self.cfg_general["rpki_roas"]["source"] == \
                "ripe-rpki-validator-cache":
            used_enricher_classes.append(RPKIROAsEnricher)

        if irrdb_cfg["use_arin_bulk_whois_data"]["enabled"]:
            used_enricher_classes.append(ARINWhoisDBDumpEnricher)

        if irrdb_cfg["use_registrobr_bulk_whois_data"]["enabled"]:
            used_enricher_classes.append(RegistroBRWhoisDBDumpEnricher)

        self.never_via_route_servers_asns = list(
            set(filtering["never_via_route_servers"]["asns"] or [])
        )
        if filtering["never_via_route_servers"]["peering_db"]:
            used_enricher_classes.append(NeverViaRouteServersEnricher)

        for enricher_class in used_enricher_classes:
            enricher = enricher_class(self, threads=self.threads)
            try:
                enricher.enrich()
            except ARouteServerError as e:
                errors = True
                if str(e):
                    logging.error(str(e))

        if errors:
            raise BuilderError()

    def _include_local_file(self, local_file_id):
        raise NotImplementedError()

    def render_template(self, output_file=None):
        """Render the output configuration.

        Raises:

            ARouteServerError or derived exceptions
              (from pierky.arouteserver.errors).

              Exceptions raised here can have no arguments and their string
              representation can be empty: in these cases, it means that
              one or more errors have been logged using the ``logging`` module.

        Args:

            output_file (file): the output file where the configuration must
                be written.
        """

        def sorted_rpki_roas():
            """Returns a list of ROAs, sorted by prefix length, prefix, ASN"""
            res = []
            prefix_lengths = sorted(map(int, self.rpki_roas.keys()))
            for pref_len in prefix_lengths:
                for roa in sorted(self.rpki_roas[str(pref_len)],
                                  key=lambda r: (r["prefix"], r["asn"])):
                    res.append(roa)
            return res

        self.data = {}
        self.data["ip_ver"] = self.ip_ver
        if self.ip_ver is None:
            self.data["list_ip_vers"] = [4, 6]
        else:
            self.data["list_ip_vers"] = [self.ip_ver]
        self.data["cfg"] = self.cfg_general
        self.data["bogons"] = self.cfg_bogons
        self.data["clients"] = self.cfg_clients
        self.data["asns"] = self.cfg_asns
        self.data["irrdb_info"] = self.irrdb_info
        self.data["rpki_roas"] = sorted_rpki_roas()
        self.data["arin_whois_records"] = self.arin_whois_records
        self.data["registrobr_whois_records"] = self.registrobr_whois_records
        self.data["never_via_route_servers_asns"] = self.never_via_route_servers_asns
        self.data["live_tests"] = self.live_tests
        self.data["rtt_based_functions_are_used"] = \
            self.cfg_general.rtt_based_functions_are_used
        self.data["perform_graceful_shutdown"] = self.perform_graceful_shutdown
        self.data["reject_reasons"] = self.REJECT_REASONS

        def ipaddr_ver(ip):
            return IPNetwork(ip).version

        def current_ipver(ip):
            if self.ip_ver is None:
                return True
            return IPNetwork(ip).version == self.ip_ver

        def is_ipver(data, ip_ver):
            prefix = data
            return IPNetwork(prefix).version == ip_ver

        def include_local_file(local_file_id):
            # The 'rpki_rtr_config' local_file_id is always allowed
            # to be included, because it's referenced directly in
            # the Jinja2 template for RPKI configuration.
            if local_file_id == "rpki_rtr_config":
                return self._include_local_file(local_file_id)

            if local_file_id not in self.LOCAL_FILES_IDS:
                raise AssertionError(
                    "Local file ID '{}' is referenced in J2 "
                    "templates but is not in LOCAL_FILES_IDS.".format(
                        local_file_id
                    )
                )
            local_files = self.local_files or []
            if local_file_id in local_files:
                return self._include_local_file(local_file_id)
            return ""

        def target_version_ge(v):
            if self.target_version:
                return version.parse(self.target_version) >= version.parse(v)
            return False

        def target_version_le(v):
            if self.target_version:
                return version.parse(self.target_version) <= version.parse(v)
            return False

        def get_normalized_rtt(v):
            if not v:
                return 0
            if v < 1:
                return 1
            if v > 60000:
                return 60000
            return int(round(v))

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
        env.tests["is_ipver"] = is_ipver
        env.filters["community_is_set"] = community_is_set
        env.filters["ipaddr_ver"] = ipaddr_ver
        env.filters["include_local_file"] = include_local_file
        env.filters["target_version_ge"] = target_version_ge
        env.filters["target_version_le"] = target_version_le
        env.filters["get_normalized_rtt"] = get_normalized_rtt

        self.enrich_j2_environment(env)

        tpl = env.get_template(self.template_name)

        start_time = int(time.time())

        logging.info("Started template rendering "
                     "for {}".format(self.template_path))
        try:
            if output_file:
                for buf in tpl.generate(self.data):
                    output_file.write(buf)
            else:
                return tpl.render(self.data)
        except Exception as e:
            _, _, traceback = sys.exc_info()
            raise TemplateRenderingError(
                "Error while rendering template: {}".format(str(e)),
                traceback=traceback
            )
        finally:
            stop_time = int(time.time())

            logging.info("Template rendering completed after "
                        "{} seconds.".format(stop_time - start_time))

class BIRDConfigBuilder(ConfigBuilder):
    """BIRD configuration builder.

    The ``kwargs`` parameter of the ``__init__`` method can be used
    to pass the following additional arguments.

    Args:

        hooks (list): list of hook IDs for which to enable hooks in
            the output configuration. Details: https://arouteserver.readthedocs.io/en/latest/CONFIG.html#bird-hooks
    """

    LOCAL_FILES_IDS = ["header", "header4", "header6",
                       "footer", "footer4", "footer6",
                       "client", "client4", "client6"]
    LOCAL_FILES_BASE_DIR = "/etc/bird"

    HOOKS = ["pre_receive_from_client", "post_receive_from_client",
             "pre_announce_to_client", "post_announce_to_client",
             "route_can_be_announced_to", "announce_rpki_invalid_to_client",
             "scrub_communities_in", "scrub_communities_out",
             "apply_blackhole_filtering_policy"]

    AVAILABLE_VERSION = ["1.6.3", "1.6.4", "1.6.6", "1.6.7", "1.6.8",
                         "2.0.7"]
    DEFAULT_VERSION = "1.6.8"

    def validate_bgpspeaker_specific_configuration(self):
        if self.ip_ver is None and \
           version.parse(self.target_version) < version.parse("2.0"):
            raise BuilderError(
                "An explicit target IP version is needed "
                "to build BIRD 1.x configuration. Use the "
                "--ip-ver command line argument to supply one."
            )

        hooks = self.kwargs.get("hooks", [])
        if hooks:
            if not isinstance(hooks, list):
                raise BuilderError(
                    "hooks must be a list of hook names"
                )

        return True

    def _include_local_file(self, local_file_id):
        return 'include "{}";\n\n'.format(
            os.path.join(
                self.local_files_dir or self.LOCAL_FILES_BASE_DIR,
                "{}.local".format(local_file_id)
            )
        )

    def enrich_j2_environment(self, env):

        def hook_is_set(hook_name):
            if hook_name not in self.HOOKS:
                raise AssertionError(
                    "Hook '{}' is referenced in J2 "
                    "templates but is not in HOOKS.".format(hook_name)
                )
            hooks = self.kwargs.get("hooks", []) or []
            return hook_name in hooks

        env.filters["hook_is_set"] = hook_is_set

class OpenBGPDConfigBuilder(ConfigBuilder):
    """OpenBGPD configuration builder.
    """

    LOCAL_FILES_IDS = ["header",
                       "pre-irrdb", "post-irrdb",
                       "pre-clients", "post-clients", "client",
                       "pre-filters", "post-filters",
                       "footer"]
    LOCAL_FILES_BASE_DIR = "/etc/bgpd"

    AVAILABLE_VERSION = ["6.0", "6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7"]
    DEFAULT_VERSION = "6.6"

    IGNORABLE_ISSUES = ["path_hiding", "transit_free_action",
                        "add_path", "max_prefix_action",
                        "blackhole_filtering_rewrite_ipv6_nh",
                        "large_communities", "extended_communities",
                        "graceful_shutdown", "internal_communities",
                        "rpki_roas_as_route_objects_source",
                        "rpki_roas_source"]

    def _include_local_file(self, local_file_id):
        return 'include "{}"\n\n'.format(
            os.path.join(
                self.local_files_dir or self.LOCAL_FILES_BASE_DIR,
                "{}.local".format(local_file_id)
            )
        )

    def validate_bgpspeaker_specific_configuration(self):
        res = True

        if self.cfg_general["path_hiding"]:
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "path_hiding",
                "The 'path_hiding' general configuration parameter is "
                "set to True, but the configuration generated by "
                "ARouteServer for OpenBGPD does not support "
                "path-hiding mitigation techniques."
            ):
                res = False

        transit_free_action = self.cfg_general["filtering"]["transit_free"]["action"]
        if transit_free_action and transit_free_action != "reject":
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "transit_free_action",
                "Transit free ASNs policy is configured with "
                "'action' = '{}' but only 'reject' is supported "
                "for OpenBGPD.".format(transit_free_action)
            ):
                res = False

        reject_policy = self.cfg_general["filtering"]["reject_policy"]["policy"]
        if reject_policy == "tag_and_reject":
            res = False
            logging.error(
                "For OpenBGP, 'reject_policy' can't be set to "
                "'tag_and_reject'."
            )

        add_path_clients = []
        max_prefix_action_clients = []
        for client in self.cfg_clients.cfg["clients"]:
            if client["cfg"]["add_path"]:
                add_path_clients.append(client["ip"])

            max_prefix_action = client["cfg"]["filtering"]["max_prefix"]["action"]
            if max_prefix_action:
                if max_prefix_action not in ("shutdown", "restart"):
                    max_prefix_action_clients.append(client["ip"])

        if add_path_clients:
            clients = add_path_clients
            cnt = len(clients)
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "add_path",
                "ADD_PATH not supported by OpenBGPD but "
                "enabled for the following clients: {}{}.".format(
                    ", ".join(clients[:3]),
                    "" if cnt <= 3 else " and {} more".format(cnt - 3)
                )
            ):
                res = False

        if max_prefix_action_clients:
            clients = max_prefix_action_clients
            cnt = len(clients)
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "max_prefix_action",
                "Invalid max-prefix 'action' for the following "
                "clients: {}{}; only 'shutdown' and 'restart' "
                "are supported by OpenBGPD.".format(
                    ", ".join(clients[:3]),
                    "" if cnt <= 3 else " and {} more".format(cnt - 3)
                )
            ):
                res = False

        if self.cfg_general["blackhole_filtering"]["policy_ipv6"] == "rewrite-next-hop" and \
            version.parse(self.target_version) < version.parse("6.1"):
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "blackhole_filtering_rewrite_ipv6_nh",
                "On OpenBSD < 6.1 there is an issue related to next-hop rewriting "
                "that impacts blackhole filtering policies when "
                "'blackhole_filtering.policy_ipv6' is 'rewrite-next-hop': "
                "https://github.com/pierky/arouteserver/issues/3 "
                "If the release running on the route server includes the fix "
                "for this issue, please consider to enable this feature by "
                "setting the configuration target version to a value "
                "greater than or equal to '6.1' (--target-version command "
                "line argument)."
            ):
                res = False

        only_large_comms = []
        large_comms_used = []
        peer_as_ext_comms = []
        for comm_name in ConfigParserGeneral.COMMUNITIES_SCHEMA:
            comm = self.cfg_general["communities"][comm_name]

            # large comms used
            if comm["lrg"]:
                large_comms_used.append((comm_name, comm["lrg"]))

                # only large comms
                if not comm["std"] and not comm["ext"]:
                    only_large_comms.append((comm_name, comm["lrg"]))

            # peer_as ext communities not scrubbed
            comm_def = ConfigParserGeneral.COMMUNITIES_SCHEMA[comm_name]
            peer_as = comm_def.get("peer_as", False)
            direction = comm_def.get("type", None)

            if peer_as and direction == "inbound" and comm["ext"]:
                peer_as_ext_comms.append((comm_name, comm["ext"]))

        large_comms_advice = ("If large BGP communities are supported by the "
                              "release of OpenBGPD running on the route "
                              "server, enable them by setting the "
                              "configuration target version to a value "
                              "greater than or equal to '6.1' "
                              "(--target-version command line argument).")

        if only_large_comms and \
            version.parse(self.target_version) < version.parse("6.1"):
            comms = only_large_comms
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "large_communities",
                "The communit{y_ies} '{names}' ha{s_ve} been configured to be "
                "implemented using only the large communit{y_ies} "
                "'{comms}'; large communities are not supported by "
                "OpenBGPD previous to OpenBSD 6.1 so the function{s1} "
                "{it_they} {is_are} used for will be not available. "
                "{large_comms_advice}".format(
                    y_ies="y" if len(comms) == 1 else "ies",
                    names=", ".join([_[0] for _ in comms]),
                    s_ve="s" if len(comms) == 1 else "ve",
                    comms=", ".join([_[1] for _ in comms]),
                    s1="" if len(comms) == 1 else "s",
                    it_they="it" if len(comms) == 1 else "they",
                    is_are="is" if len(comms) == 1 else "are",
                    large_comms_advice=large_comms_advice
                )
            ):
                res = False

        if large_comms_used and \
            version.parse(self.target_version) < version.parse("6.1"):
            comms = large_comms_used
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "large_communities",
                "The communit{y_ies} '{names}' ha{s_ve} been configured to be "
                "implemented using also the large communit{y_ies} "
                "'{comms}'; large communities are not supported by "
                "OpenBGPD previous to OpenBSD 6.1 so the function{s1} "
                "{it_they} {is_are} used for will be available via "
                "standard/extended communities only. "
                "{large_comms_advice}".format(
                    y_ies="y" if len(comms) == 1 else "ies",
                    names=", ".join([_[0] for _ in comms]),
                    s_ve="s" if len(comms) == 1 else "ve",
                    comms=", ".join([_[1] for _ in comms]),
                    s1="" if len(comms) == 1 else "s",
                    it_they="it" if len(comms) == 1 else "they",
                    is_are="is" if len(comms) == 1 else "are",
                    large_comms_advice=large_comms_advice
                )
            ):
                res = False

        if peer_as_ext_comms:
            comms = peer_as_ext_comms
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "extended_communities",
                "The peer-ASN-specific communit{y_ies} '{names}' "
                "ha{s_ve} been configured to be implemented using the "
                "extended communit{y_ies} '{comms}'; please be aware that "
                "peer-ASN-specific extended communities are not scrubbed "
                "from routes that leave OpenBGPD route servers and they are "
                "propagated to the route server clients.".format(
                    y_ies="y" if len(comms) == 1 else "ies",
                    names=", ".join([_[0] for _ in comms]),
                    s_ve="s" if len(comms) == 1 else "ve",
                    comms=", ".join([_[1] for _ in comms])
                )
            ):
                res = False

        try:
            self.cfg_general.check_overlapping_communities(
                allow_private_asns=False)
        except ConfigError as e:
            res = False
            logging.error("{}OpenBGPD doesn't allow to delete BGP "
                          "communities using ranges of values, but only "
                          "using the wildcard ('*'), so also "
                          "outbound communities whose last part contain "
                          "private ASNs collide with inbound communities "
                          "that use the 'peer_as' macro.".format(
                              str(e) + " " if str(e) else ""
                            ))

        if (self.cfg_general["graceful_shutdown"]["enabled"] or \
            self.perform_graceful_shutdown) and \
            version.parse(self.target_version) <= version.parse("6.1"):
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "graceful_shutdown",
                "GRACEFUL_SHUTDOWN BGP community is not implemented "
                "on OpenBGPD versions prior to 6.2. By marking this issue "
                "as ignored the graceful shutdown option will not be "
                "considered and the feature will be not included into the "
                "configuration. "
                "If the release running on the route server is 6.2 or later "
                "please consider to enable this feature by "
                "setting the configuration target version to a value "
                "greater than or equal to '6.2' (--target-version command "
                "line argument)."
            ):
                res = False

        internal_communities_collistion = []
        for comm_name in ConfigParserGeneral.COMMUNITIES_SCHEMA:
            comm = self.cfg_general["communities"][comm_name]
            if comm["ext"] and comm["ext"].startswith("ro:65535:"):
                internal_communities_collistion.append(comm_name)
        if internal_communities_collistion:
            if not self.process_bgpspeaker_specific_compatibility_issue(
                "internal_communities",
                "The Extended BGP communities in the range ro:65535:* "
                "are reserved for internal purposes. "
                "A collision has been detected with the following "
                "communit{y_ies}: {comms}".format(
                    y_ies="y" if len(internal_communities_collistion) == 1 else "ies",
                    comms=", ".join(internal_communities_collistion)
                )
            ):
                res = False

        # Kept for backward compatibility
        use_rpki_roas_as_route_objects_cfg = \
            self.cfg_general["filtering"]["irrdb"]["use_rpki_roas_as_route_objects"]
        if use_rpki_roas_as_route_objects_cfg["enabled"]:
            if self.cfg_general["rpki_roas"]["source"] != "ripe-rpki-validator-cache":
                if not self.process_bgpspeaker_specific_compatibility_issue(
                    "rpki_roas_as_route_objects_source",
                    "For OpenBGPD only the 'ripe-rpki-validator-cache' "
                    "value is allowed for the 'rpki_roas.source' option."
                ):
                    res = False

        if self.cfg_general.rpki_roas_needed:
            if self.cfg_general["rpki_roas"]["source"] != "ripe-rpki-validator-cache":
                if not self.process_bgpspeaker_specific_compatibility_issue(
                    "rpki_roas_source",
                    "For OpenBGPD only the 'ripe-rpki-validator-cache' "
                    "value is allowed for the 'rpki_roas.source' option."
                ):
                    res = False

        return res

    def enrich_j2_environment(self, env):

        def convert_ext_comm(s):
            parts = s.split(":")
            return "{} {}:{}".format(
                parts[0], parts[1], parts[2]
            )

        def at_least_one_client_uses_tag_reject_policy():
            for client in self.cfg_clients.cfg["clients"]:
                policy = client["cfg"]["filtering"]["reject_policy"]["policy"]
                if policy == "tag":
                    return True
            return False

        def community_is_set(comm):
            if not comm:
                return False
            # OpenBGPD <= 6.0 does not implement large BGP communities,
            # so only standard and extended ones are considered.
            if version.parse(self.target_version) < version.parse("6.1"):
                if not comm["std"] and not comm["ext"]:
                    return False
            else:
                if not comm["std"] and not comm["ext"] and not comm["lrg"]:
                    return False
            return True

        def aggregated_roas_covered_space():
            prefixes = []
            for pref_len in self.rpki_roas:
                for roa in self.rpki_roas[pref_len]:
                    prefixes.append(roa["prefix"])
            return aggregate(prefixes)

        env.filters["convert_ext_comm"] = convert_ext_comm
        env.filters["community_is_set"] = community_is_set
        self.data["at_least_one_client_uses_tag_reject_policy"] = \
            at_least_one_client_uses_tag_reject_policy()
        self.data["rpki_roas_covered_space"] = aggregated_roas_covered_space()

class TemplateContextDumper(ConfigBuilder):

    def enrich_j2_environment(self, env):

        def to_yaml(obj):
            return yaml.safe_dump(obj, default_flow_style=False)

        def parse_irrdb_info(irrdb_info):
            lst = []
            for bundle_id in irrdb_info:
                bundle = irrdb_info[bundle_id]
                lst.append(bundle.to_dict())
            return lst

        def parse_generic_irr_whois_records(records):
            res = {}
            for origin_asn in records:
                res[origin_asn] = list(records[origin_asn].prefixes)
            return res

        env.filters["to_yaml"] = to_yaml
        env.filters["parse_irrdb_info"] = parse_irrdb_info
        env.filters["parse_generic_irr_whois_records"] = parse_generic_irr_whois_records

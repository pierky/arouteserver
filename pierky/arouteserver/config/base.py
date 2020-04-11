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

import os
import logging
import re
import yaml


from .validators import ConfigParserValidator
from ..errors import ConfigError, MissingFileError, ARouteServerError


class ConfigParserBase(object):

    ROOT = None

    def __init__(self):
        self.cfg = None
        self.file_dir = None

    def __contains__(self, name):
        return name in self.cfg[self.ROOT]

    def __getitem__(self, name):
        return self.cfg[self.ROOT][name]

    def __setitem__(self, name, val):
        self.cfg[self.ROOT][name] = val

    def __delitem__(self, name):
        del self.cfg[self.ROOT][name]

    def _load_from_yaml(self, doc):

        def expand_include(lines):
            res = ""
            for line in lines:
                if not line:
                    continue

                if not line.strip():
                    continue

                if res:
                    res += "\n"

                if line.strip().startswith("!include"):
                    filepath = line.strip().split(" ")[1]
                    filepath = os.path.expanduser(filepath)

                    if not os.path.isabs(filepath):
                        if self.file_dir:
                            filepath = os.path.join(self.file_dir, filepath)

                    with open(filepath) as inputfile:
                        raw = inputfile.read()

                    res += expand_include(raw.split("\n"))
                    continue

                res += line

            return res

        def expand_env_vars(doc):
            res = doc
            res = os.path.expandvars(res)
            res = re.sub("\$\{[A-Za-z0-9_]+\}", "", res)
            return res

        lines = doc.split("\n")
        expanded_doc = expand_include(lines)
        expanded_doc = expand_env_vars(expanded_doc)

        try:
            self.cfg = yaml.safe_load(expanded_doc)
        except Exception as e:
            raise ConfigError(
                "Can't parse YAML file: {}".format(str(e))
            )

        if not isinstance(self.cfg, dict):
            raise ConfigError(
                "Error while parsing config file: invalid syntax. "
                "Hint: check that the root element '{}' exists.".format(
                    self.ROOT
                )
            )

    def _load_from_yaml_file(self, cfg_path):
        if not os.path.isfile(cfg_path):
            raise MissingFileError(cfg_path)

        self.file_dir = os.path.dirname(cfg_path)

        with open(cfg_path, "r") as f:
            self._load_from_yaml(f.read())

    def load(self, cfg_path):
        self._load_from_yaml_file(cfg_path)

        try:
            self.parse()
        except ARouteServerError as e:
            if str(e):
                logging.error(str(e))
            raise ConfigError()

    def load_from_dict(self, input_dict):
        self.cfg = input_dict

        try:
            self.parse()
        except ARouteServerError as e:
            if str(e):
                logging.error(str(e))
            raise ConfigError()

    @staticmethod
    def validate(schema, cfg, path=""):
        errors = False
        if cfg is None:
            cfg = {}
            return

        for prop in cfg:
            if prop not in schema:
                errors = True
                logging.error(
                    "Unknown statement at '{}' level: '{}'.".format(
                        path, prop
                    )
                )

        for prop in schema:
            if isinstance(schema[prop], ConfigParserValidator):
                validator = schema[prop]

                try:
                    if prop in cfg:
                        cfg[prop] = validator.validate(cfg[prop])
                    else:
                        cfg[prop] = validator.validate(None)
                except ConfigError as e:
                    errors = True
                    logging.error(
                        "Error parsing '{}' at '{}' level - {}.".format(
                            prop, path, str(e)
                        )
                    )

            elif isinstance(schema[prop], dict):
                if prop not in cfg:
                    cfg[prop] = {}
                if cfg[prop] is None:
                    cfg[prop] = {}

                ConfigParserBase.validate(
                    schema[prop], cfg[prop],
                    prop if path == "" else "{}.{}".format(path, prop)
                )

            else:
                raise NotImplementedError("prop: {}, path: {}".format(prop, path))

        if errors:
            raise ConfigError()

    def parse(self):
        """
        Contents of cfg dict is updated/normalized by validators.
        """
        raise NotImplementedError()

def convert_next_hop_policy(cfg):
    if not isinstance(cfg.get("filtering", None), dict):
        return
    if "next_hop_policy" in cfg["filtering"]:
        if "next_hop" in cfg["filtering"]:
            raise ConfigError(
                "Can't use the new 'next_hop' and the old 'next_hop_policy' "
                "statements simultaneously for NEXT_HOP policy configuration"
            )

        cfg["filtering"]["next_hop"] = {
            "policy": cfg["filtering"]["next_hop_policy"]
        }
        del cfg["filtering"]["next_hop_policy"]

def convert_maxprefix_peeringdb(cfg):
    if not isinstance(cfg.get("filtering", None), dict):
        return
    if "max_prefix" not in cfg["filtering"]:
        return
    if not isinstance(cfg["filtering"]["max_prefix"], dict):
        return
    if "peering_db" in cfg["filtering"]["max_prefix"]:
        peering_db = cfg["filtering"]["max_prefix"]["peering_db"]
        if isinstance(peering_db, dict):
            return
        cfg["filtering"]["max_prefix"]["peering_db"] = {
            "enabled": peering_db
        }

def convert_filtering_rpki(cfg):
    if not isinstance(cfg.get("filtering", None), dict):
        return
    if "rpki" not in cfg["filtering"]:
        return
    if "rpki_bgp_origin_validation" in cfg["filtering"]:
        raise ConfigError(
            "A conflict due to a deprecated syntax exists: "
            "filtering.rpki and filtering.rpki_bgp_origin_validation "
            "are both configured."
        )
    cfg["filtering"]["rpki_bgp_origin_validation"] = \
        cfg["filtering"].pop("rpki")

def build_rpki_roas(cfg):
    """Build rpki_roas.

    Also used to identify those cases where filtering.rpki is enable
    (and then 'rtr' is implicitly used for ROAs collection) and
    filtering.irrdb.rpki_roas_as_route_objects is enabled and source
    is set to 'ripe-rpki-validator-cache'.
    """

    if not isinstance(cfg.get("filtering", None), dict):
        return

    rpki_roas = {}

    def from_rpki_roas_as_route_objects():
        """Return (used [bool], source)"""
        irrdb = cfg["filtering"].get("irrdb", None)
        if not isinstance(irrdb, dict):
            return False, None

        roas_as_route_objects = irrdb.get("use_rpki_roas_as_route_objects",
                                          None)
        if not isinstance(roas_as_route_objects, dict):
            return False, None

        if roas_as_route_objects.get("enabled", False) is not True:
            return False, None

        for k in ("source", "ripe_rpki_validator_url",
                  "allowed_trust_anchors"):
            if k in roas_as_route_objects:
                rpki_roas[k] = roas_as_route_objects.pop(k)

        return True, rpki_roas.get("source", None)

    def from_rpki():
        """Return (used [bool], source)"""
        rpki = cfg["filtering"].get("rpki", None)
        if not isinstance(rpki, dict):
            return False, None

        if rpki.get("enabled", False) is not True:
            return False, None

        rpki_roas["source"] = "rtr"

        return True, "rtr"

    roas_as_routes_used, roas_as_routes_src = from_rpki_roas_as_route_objects()
    rpki_used, rpki_src = from_rpki()

    if roas_as_routes_used and rpki_used and \
        (roas_as_routes_src or rpki_src) != rpki_src:
        raise ConfigError(
            "A deprecated syntax triggered an issue with the configuration "
            "of RPKI BGP Origin Validation (filtering.rpki) and ROAs-as-route-"
            "objects (filtering.irrdb.rpki_roas_as_route_objects). "
            "The former uses RTR as source for ROAs, while the "
            "latter is configured to use the RIPE RPKI Validator "
            "cache file. "
            "To fix this issue, convert them to the new syntax and configure "
            "the desired ROAs source within the 'rpki_roas' section. "
            "Please refer to the general.yml file distributed with the tool "
            "for the proper syntax to use."
        )

    if rpki_roas:
        if "rpki_roas" in cfg:
            raise ConfigError(
                "A conflict due to a deprecated syntax exists: "
                "please check rpki_roas, filtering.rpki and "
                "filtering.irrdb.rpki_roas_as_route_objects."
            )
        cfg["rpki_roas"] = rpki_roas

def convert_ripe_rpki_validator_url(cfg):
    if "rpki_roas" not in cfg:
        return
    if not isinstance(cfg["rpki_roas"], dict):
        return
    if "ripe_rpki_validator_url" not in cfg["rpki_roas"]:
        return
    if not isinstance(cfg["rpki_roas"]["ripe_rpki_validator_url"], list):
        cfg["rpki_roas"]["ripe_rpki_validator_url"] = [cfg["rpki_roas"]["ripe_rpki_validator_url"]]

def convert_rpki_roas_source_rtrlib_into_rtr(cfg):
    if "rpki_roas" not in cfg:
        return
    if not isinstance(cfg["rpki_roas"], dict):
        return
    if "source" not in cfg["rpki_roas"]:
        return
    if cfg["rpki_roas"]["source"] == "rtrlib":
        logging.warning("A deprecated configuration is used for "
                        "filtering.rpki_roas.source: 'rtrlib' has "
                        "been replaced by 'rtr', soon it will be "
                        "no longer a valid value.")
        cfg["rpki_roas"]["source"] = "rtr"

def convert_deprecated(cfg):
    if not cfg:
        return
    if not isinstance(cfg, dict):
        return

    # Convert next_hop_policy (< v0.6.0) into the new format
    convert_next_hop_policy(cfg)

    # Convert max_prefix.peering_db (< v0.13.0) into the new format
    convert_maxprefix_peeringdb(cfg)

    # Build cfg.rpki_roas (< v0.17.0) from rpki and roas_as_route_objects
    build_rpki_roas(cfg)

    # Convert filtering.rpki (< v0.17.0) into the new format
    convert_filtering_rpki(cfg)

    # Convert ripe_rpki_validator_url (<= v0.20.0) into a list
    convert_ripe_rpki_validator_url(cfg)

    # Convert rpki_roas.source from rtrlib into rtr (<= v0.22.2)
    convert_rpki_roas_source_rtrlib_into_rtr(cfg)

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

import os
import logging
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

        lines = doc.split("\n")
        expanded_doc = expand_include(lines)

        try:
            self.cfg = yaml.safe_load(expanded_doc)
        except Exception as e:
            raise ConfigError(
                "Can't parse YAML file: {}".format(str(e))
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

    @staticmethod
    def validate(schema, cfg, path=""):
        errors = False
        if cfg is None:
            cfg = {}
            return

        for prop in cfg:
            if not prop in schema:
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
                raise NotImplementedError()

        if errors:
            raise ConfigError()

    def parse(self):
        """
        Contents of cfg dict is updated/normalized by validators.
        """
        raise NotImplementedError()

def convert_next_hop_policy(cfg):
    if not cfg:
        return
    if not isinstance(cfg, dict):
        return
    if not "filtering" in cfg:
        return
    if not cfg["filtering"]:
        return
    if not isinstance(cfg["filtering"], dict):
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

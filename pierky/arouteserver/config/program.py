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
# along with this program.  Ifnot, see <http://www.gnu.org/licenses/>.

from copy import deepcopy
import logging
import os
import sys
import yaml

from ..cached_objects import CachedObject
from ..resources import get_config_dir, get_templates_dir
from ..errors import ConfigError, ARouteServerError


class ConfigParserProgram(object):

    DEFAULT_CFG_DIR = "/etc/arouteserver"
    DEFAULT_CFG_PATH = "{}/arouteserver.yml".format(DEFAULT_CFG_DIR)

    DEFAULT = {
        "cfg_dir": "{}".format(DEFAULT_CFG_DIR),

        "logging_config_file": "log.ini",

        "cfg_general": "general.yml",
        "cfg_clients": "clients.yml",
        "cfg_bogons": "bogons.yml",

        "template_dir": "templates",
        "template_name": "main.j2",

        "cache_dir": "/var/lib/arouteserver",
        "cache_expiry": CachedObject.DEFAULT_EXPIRY,

        "bgpq3_path": "bgpq3",
    }

    def __init__(self):
        self._reset_to_default()

    def _reset_to_default(self):
        self.cfg = deepcopy(self.DEFAULT)

    def load(self, path):
        self._reset_to_default()
        try:
            with open(path, "r") as f:
                cfg_from_file = yaml.load(f.read())
                if cfg_from_file:
                    self.cfg.update(cfg_from_file)
        except Exception as e:
            logging.error("An error occurred while reading global "
                          "configuration at {}: {}".format(path, str(e)),
                          exc_info=True)
            raise ConfigError()

    def get_cfg_file_path(self, cfg_key):
        assert cfg_key in ("logging_config_file", "cfg_general", "cfg_clients",
                           "cfg_bogons", "template_dir", "cache_dir")

        val = self.cfg[cfg_key]
        if os.path.isabs(val):
            return val
        return os.path.join(self.cfg["cfg_dir"], val)

    def setup(self):

        print("ARouteServer setup")
        print("")

        config_dir = get_config_dir()
        templates_dir = get_templates_dir()

        sys.stdout.write("Where do you want configuration files and templates "
                         "to be stored (default: {}): ".format(
                             self.DEFAULT_CFG_DIR
                         ))
        try:
            dest_dir = raw_input()
        except:
            print("")
            print("Setup aborted")
            return False

        if not dest_dir:
            dest_dir = self.DEFAULT_CFG_DIR
        dest_dir = dest_dir.strip()

        if dest_dir != self.DEFAULT_CFG_DIR:
            print("WARNING: the directory that has been chosen is not the "
                  "default one: use the --cfg command line argument to "
                  "allow the program to find the needed files.")

        sys.stdout.write("Do you confirm you want ARouteServer files to be "
                         "stored at {}: [YES/no] ".format(dest_dir))
        try:
            yes_no = raw_input()
        except:
            print("")
            print("Setup aborted")
            return False

        if not yes_no:
            yes_no = "yes"

        if yes_no.lower() != "yes":
            print("")
            print("Setup aborted")
            return False

        def mk_dir(d):
            sys.stdout.write("Creating {}... ".format(d))
            if os.path.exists(d):
                print("already exists")
            else:
                os.makedirs(d)
                print("OK")

        def cp_file(s, d):
            sys.stdout.write(
                "Copying default {} file into {}... ".format(
                    os.path.basename(s), d
                )
            )

            if os.path.exists(d):
                sys.stdout.write("already exists: "
                                 "do you want to overwrite it [yes/NO]: ")
                try:
                    yes_no = raw_input()
                except:
                    return False

                if not yes_no:
                    yes_no = "no"

                if yes_no.lower() != "yes":
                    print("skipping")
                    return True

            with open(s, "r") as src:
                with open(d, "w") as dst:
                    dst.write(src.read())
            print("OK")
            return True

        mk_dir(dest_dir)
        mk_dir(os.path.join(dest_dir, "templates"))

        def process_dir(s, d):
            for filename in os.listdir(s):
                if os.path.isdir(os.path.join(s, filename)):
                    mk_dir(os.path.join(d, filename))
                    process_dir(os.path.join(s, filename),
                                os.path.join(d, filename))
                else:
                    if not cp_file(os.path.join(s, filename),
                                   os.path.join(d, filename)):
                        print("")
                        print("Setup aborted")
                        return False
            return True

        if not process_dir(config_dir, dest_dir):
            return False
        if not process_dir(templates_dir, os.path.join(dest_dir, "templates")):
            return False

        self.load("{}/arouteserver.yml".format(dest_dir))

        print("")
        print("Configuration complete!")
        print("")
        print("- edit the {} file to set your logging preferences".format(
            self.get_cfg_file_path("logging_config_file")))
        print("- configure route server's options and policies "
              "in the {} file".format(
                self.get_cfg_file_path("cfg_general")))
        print("- configure route server clients in the {} file".format(
            self.get_cfg_file_path("cfg_clients")))

program_config = ConfigParserProgram()

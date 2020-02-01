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
import difflib
import hashlib
import filecmp
import logging
import os
import six
import sys
import textwrap
import yaml

from ..ask import Ask
from ..irrdb import IRRDBInfo
from ..cached_objects import CachedObject
from ..resources import get_config_dir, get_templates_dir
from ..errors import ConfigError, ARouteServerError, MissingFileError, \
                     ProgramConfigError


class ConfigParserProgram(object):

    DEFAULT_CFG_DIR_USR = "~/arouteserver"
    DEFAULT_CFG_DIR_ETC = "/etc/arouteserver"
    DEFAULT_CFG_DIRS = [DEFAULT_CFG_DIR_ETC,
                        DEFAULT_CFG_DIR_USR]
    DEFAULT_CFG_FILE = "arouteserver.yml"
    DEFAULT_CFG_PATHS = [os.path.join(DEFAULT_CFG_DIR_ETC, DEFAULT_CFG_FILE),
                         os.path.join(DEFAULT_CFG_DIR_USR, DEFAULT_CFG_FILE)]

    DEFAULT = {
        "cfg_dir": None,

        "logging_config_file": "log.ini",

        "cfg_general": "general.yml",
        "cfg_clients": "clients.yml",
        "cfg_bogons": "bogons.yml",

        "templates_dir": "templates",
        "template_name": "main.j2",

        "cache_dir": "cache",
        "cache_expiry": CachedObject.DEFAULT_EXPIRY,

        "bgpq3_path": "bgpq3",
        "bgpq3_host": IRRDBInfo.BGPQ3_DEFAULT_HOST,
        "bgpq3_sources": IRRDBInfo.BGPQ3_DEFAULT_SOURCES,

        "rtt_getter_path": "",

        "threads": 4,

        "check_new_release": True
    }

    PATH_KEYS = ("logging_config_file", "cfg_general", "cfg_clients",
                 "cfg_bogons", "templates_dir", "cache_dir", "rtt_getter_path")

    FINGERPRINTS_FILENAME = "fingerprints.yml"

    def v(self, text, new_line=True):
        if self.verbose:
            sys.stdout.write("{}{}".format(
                text, "\n" if new_line else ""
            ))

    def __init__(self, verbose=True, ask=True):
        self._reset_to_default()
        self.verbose = verbose
        self.ask = ask

    def _reset_to_default(self):
        self.cfg = deepcopy(self.DEFAULT)

    def load(self, path_or_file):
        self._reset_to_default()

        if isinstance(path_or_file, six.string_types):
            path = path_or_file

            if path and not os.path.exists(os.path.expanduser(path)):
                raise MissingFileError(path)

            f = None
        else:
            path = "<file> object"
            f = path_or_file

        try:
            if f:
                cfg_from_file = yaml.safe_load(f.read())
            else:
                with open(os.path.expanduser(path), "r") as f:
                    cfg_from_file = yaml.safe_load(f.read())

            if cfg_from_file:
                for key in cfg_from_file:
                    if key not in ConfigParserProgram.DEFAULT:
                        raise ConfigError(
                            "Unknown statement: {}".format(key)
                        )
                self.cfg.update(cfg_from_file)

        except Exception as e:
            logging.error("An error occurred while reading program "
                          "configuration at {}: {}".format(path, str(e)),
                          exc_info=not isinstance(e, ARouteServerError))
            raise ConfigError()

        if self.cfg["cfg_dir"]:
            self.cfg["cfg_dir"] = os.path.expanduser(self.cfg["cfg_dir"])
        else:
            self.cfg["cfg_dir"] = os.path.dirname(os.path.expanduser(path))

        # relative path -> absolute path
        for cfg_key in self.PATH_KEYS:
            if not self.cfg[cfg_key]:
                continue
            val = os.path.expanduser(self.cfg[cfg_key])
            if not os.path.isabs(val):
                self.cfg[cfg_key] = os.path.join(self.cfg["cfg_dir"], val)
            else:
                self.cfg[cfg_key] = val

    def expanduser(self, cfg_key):
        if cfg_key in self.PATH_KEYS:
            return os.path.expanduser(self.cfg[cfg_key])
        else:
            return self.cfg[cfg_key]

    def parse_cli_args(self, args):
        args_dict = vars(args)
        for option_name in self.cfg:
            if option_name in args_dict and args_dict[option_name]:
                self.cfg[option_name] = args_dict[option_name]

    def get(self, cfg_key):
        if self.cfg[cfg_key]:
            return self.expanduser(cfg_key)
        return None

    def get_dir(self, cfg_key):
        v = self.get(cfg_key)
        if not v:
            raise ProgramConfigError(
                "The value of '{}' is missing.".format(cfg_key)
            )
        if not os.path.exists(v):
            raise ProgramConfigError(
                "The path configured for '{}' ({}) does not exist.".format(
                    cfg_key, v
                )
            )
        if not os.path.isdir(v):
            raise ProgramConfigError(
                "The path configured for '{}' ({}) is not a directory.".format(
                    cfg_key, v
                )
            )
        return v

    def mk_dir(self, d):
        self.v("Creating {}... ".format(d), new_line=False)
        if os.path.exists(d):
            self.v("already exists")
        else:
            try:
                os.makedirs(d)
                self.v("OK")
            except OSError as e:
                raise ARouteServerError(str(e))

    def cp_file(self, s, d):
        if os.path.abspath(s) == os.path.abspath(d):
            return
        # Avoid .swp files
        if s.endswith(".swp"):
            return

        assert os.path.exists(s), "The {} file does not exist.".format(s)

        try:
            with open(s, "r") as src:
                with open(d, "w") as dst:
                    dst.write(src.read())
        except (IOError, OSError) as e:
            raise ARouteServerError(str(e))

    def show_diff(self, s, d):
        with open(s, "r") as f:
            fromlines = f.readlines()
        with open(d, "r") as f:
            tolines = f.readlines()
        diff = difflib.unified_diff(fromlines, tolines,
                                    "currently installed", "new")
        self.v("")
        sys.stdout.writelines(diff)
        self.v("")

    def process_file(self, s, d, fps_status=None, rel_path=None):
        assert os.path.exists(s), "The {} file does not exist.".format(s)

        filename = os.path.basename(s)

        def write_title():
            self.v("- {}... ".format(filename), new_line=False)

        write_title()

        if not os.path.exists(d):
            self.cp_file(s, d)
            self.v("OK (created)")
            return True

        if filecmp.cmp(s, d, shallow=False):
            self.v("skipped (same content)")
            return True

        if fps_status:
            status_descr = ConfigParserProgram.get_fingerprints_status_descr(
                fps_status, rel_path)

            if fps_status["new_file"]:
                self.cp_file(s, d)
                self.v("OK (created)")
                return True

            if fps_status["same_file"]:
                self.v("skipped (same content)")
                return True

            if fps_status["local_unknown"]:
                self.v("WARNING!")
                self.v("")
                self.v(
                    "   "
                    "\n   ".join(textwrap.wrap(status_descr, width=60))
                )
                self.v("")
                write_title()
            else:
                if fps_status["installed_version_mismatch"]:
                    if not fps_status["locally_edited"]:
                        self.cp_file(s, d)
                        self.v("OK (updated)")
                        return True

                if fps_status["locally_edited"]:
                    self.v("WARNING!")
                    self.v("")
                    self.v(
                        "   "
                        "\n   ".join(textwrap.wrap(status_descr, width=60))
                    )
                    self.v("")
                    bak_path = "{}.bak".format(d)

                    if self.ask:
                        ret, yes_no = Ask().ask_yes_no(
                            "Do you want to create "
                            "a backup copy into {}?".format(bak_path),
                            default="yes"
                        )
                    else:
                        ret = True
                        yes_no = "yes"

                    if not ret:
                        return False

                    if yes_no.lower() == "yes":
                        self.cp_file(s, bak_path)
                        self.cp_file(s, d)
                        write_title()
                        self.v("OK (backed up and updated)")
                        return True
                    else:
                        write_title()

        while True:
            if self.ask:
                ret, answer = Ask().ask(
                    "already exists: do you want to overwrite it?",
                    options=["yes", "no", "diff"],
                    default="no"
                )
            else:
                ret = True
                answer = "yes"

            if not ret:
                return False

            if answer == "diff":
                self.show_diff(s, d)
                write_title()
            else:
                write_title()

                if answer != "yes":
                    self.v("skipped")
                    return True

                self.cp_file(s, d)
                self.v("OK")
                return True

    def process_dir(self, s, d, fps_status=None, rel_path=None):
        assert os.path.exists(s) and os.path.isdir(s), \
            "The {} directory does not exist.".format(s)

        self.v("Populating {}...".format(d))

        for filename in os.listdir(s):
            if filename == ConfigParserProgram.FINGERPRINTS_FILENAME:
                continue

            new_fps_status = None
            if fps_status and filename in fps_status:
                new_fps_status = fps_status[filename]
            new_rel_path = None
            if rel_path:
                new_rel_path = os.path.join(rel_path, filename)

            if os.path.isdir(os.path.join(s, filename)):
                self.mk_dir(os.path.join(d, filename))
                if not self.process_dir(
                    os.path.join(s, filename),
                    os.path.join(d, filename),
                    fps_status=new_fps_status,
                    rel_path=new_rel_path
                ):
                    return False
            else:
                if new_fps_status:
                    new_fps_status = new_fps_status["status"]
                if not self.process_file(
                    os.path.join(s, filename),
                    os.path.join(d, filename),
                    fps_status=new_fps_status,
                    rel_path=new_rel_path
                ):
                    return False

        return True

    @staticmethod
    def calculate_fingerprints(d):
        assert os.path.exists(d) and os.path.isdir(d), \
            "The {} directory does not exist.".format(d)

        def iterate_dir(d, dic):
            for filename in os.listdir(d):
                if filename == ConfigParserProgram.FINGERPRINTS_FILENAME:
                    continue
                if filename.endswith(".swp"):
                    continue
                path = os.path.join(d, filename)
                if os.path.isdir(path):
                    dic[filename] = {}
                    iterate_dir(path, dic[filename])
                else:
                    with open(path, "rb") as f:
                        hasher = hashlib.sha512()
                        buf = f.read()
                        hasher.update(buf)
                        dic[filename] = hasher.hexdigest()

        res = {}
        iterate_dir(d, res)
        return res

    @staticmethod
    def load_fingerprints_from_file(path):
        assert os.path.exists(path), "The {} file does not exist.".format(path)

        with open(path, "r") as f:
            return yaml.safe_load(f.read())

    def get_local_fingerprints(self):
        """Calculate fingerprints from local template files."""

        templates_dir = self.get_dir("templates_dir")
        return self.calculate_fingerprints(templates_dir)

    def get_local_distrib_fingerprints(self):
        """Get fingerprints of the locally installed templates.

        Reads the fingerprints from <templates_dir>/<FINGERPRINTS_FILENAME>.

        These fingerprints are those distributed by the program at the time
        of the package installation. A difference between these fingerprints
        and those calculated from the real files means that templates have
        been edited on the local system after the package installation.
        """

        templates_dir = self.get_dir("templates_dir")
        path = os.path.join(templates_dir, self.FINGERPRINTS_FILENAME)
        if os.path.exists(path):
            return self.load_fingerprints_from_file(path)
        return {}

    def get_current_distrib_fingerprints(self):
        """Get fingerprints of the distributed package.

        These fingerprints are those distributed within the current release
        of the package. A difference between these fingerprints and those
        calculated from the real files means that templates have been edited
        on the local system after the package installation or that the current
        release uses different files from those installed on the local system.
        """

        distrib_templates_dir = get_templates_dir()
        path = os.path.join(distrib_templates_dir, self.FINGERPRINTS_FILENAME)
        res = self.load_fingerprints_from_file(path)

        assert res is not None and res != {}, \
            "Empty fingerprints from {}.".format(path)

        return res

    @staticmethod
    def get_fingerprints_status_descr(status, filename):
        if status["new_file"]:
            s = ("{filename} expected but not found on the local "
                 "templates directory")
            return s.format(filename=filename)

        if status["same_file"]:
            s = ("the installed version of {filename} is aligned with "
                 "the one used by the current version of the program")
            return s.format(filename=filename)

        if status["local_unknown"]:
            s = ("the {filename} file is not aligned with the current "
                 "version of the program; since the {fp} file is missing, "
                 "it's not possible to determine if the {filename} file "
                 "has been edited after the installation on the "
                 "local system")
            return s.format(fp=ConfigParserProgram.FINGERPRINTS_FILENAME,
                            filename=filename)

        if status["installed_version_mismatch"]:
            s = ("the installed version of {filename} is not aligned "
                 "with the one used by the current version of the program")
            if status["locally_edited"]:
                s += ("; moreover, it seems that it has been edited "
                        "after the installation on the local system")
            return s.format(filename=filename)

        if status["locally_edited"]:
            s = ("the {filename} file has been edited after the "
                 "installation on the local system")
            return s.format(filename=filename)

        raise NotImplementedError("status: {}".format(str(status)))

    def get_fingerprints_status(self):
        """Build a dict containing the status of a template file.

        new_file is True when there isn't any calculated fingerprint.

        same_file is True when the calculated fingerprint matches the
        fingerprint in the current package.

        local_unknown is True when the local fingerpints.yml file does
        not exists.

        locally_edited is True when the calculated fingerprint does
        not match the fingerprint in the local fingerprints.yml file.

        installed_version_mismatch is True when the fingerprint in the
        local fingerprints.yml file does not match the fingerprint in
        the current package.
        """

        calculated_fps = self.get_local_fingerprints()
        local_distrib_fps = self.get_local_distrib_fingerprints()
        current_distrib_fps = self.get_current_distrib_fingerprints()

        fps_status = {}
        def iterate(curr, local, calc, dst):
            for filename in curr:
                dst[filename] = {}
                if isinstance(curr[filename], dict):
                    iterate(
                        curr[filename],
                        local.get(filename, {}),
                        calc.get(filename, {}),
                        dst[filename]
                    )
                else:
                    dst[filename]["curr"] = curr.get(filename, None)
                    dst[filename]["calc"] = calc.get(filename, None)
                    dst[filename]["local"] = local.get(filename, None)

                    status = {}
                    if dst[filename]["calc"] is None:
                        status["new_file"] = True
                        dst[filename]["status"] = status
                        continue
                    status["new_file"] = False

                    if dst[filename]["calc"] == dst[filename]["curr"]:
                        status["same_file"] = True
                        dst[filename]["status"] = status
                        continue
                    status["same_file"] = False

                    if dst[filename]["local"] is None:
                        status["local_unknown"] = True
                        dst[filename]["status"] = status
                        continue
                    status["local_unknown"] = False

                    status["locally_edited"] = \
                        dst[filename]["local"] != dst[filename]["calc"]
                    status["installed_version_mismatch"] = \
                        dst[filename]["local"] != dst[filename]["curr"]
                    dst[filename]["status"] = status

        iterate(current_distrib_fps, local_distrib_fps, calculated_fps,
                fps_status)
        return fps_status

    def verify_templates(self):
        """Verify if templates are aligned with the current version

        Returns:
            list of errors
        """
        fps_status = self.get_fingerprints_status()

        errors = []

        def iterate(dic, path):
            for filename in dic:
                new_path = os.path.join(path, filename)
                if "status" not in dic[filename]:
                    iterate(dic[filename], new_path)
                else:
                    status = dic[filename]["status"]
                    if not status.get("same_file", False):
                        descr = self.get_fingerprints_status_descr(
                            status, new_path
                        )
                        errors.append(descr)

        iterate(fps_status, "templates")
        return errors

    def setup_templates(self):
        distrib_templates_dir = get_templates_dir()

        # Using .get and not .get_dir because the dest dir may not exist.
        dest_dir = self.get("templates_dir")

        self.v("Installing templates into {}...".format(dest_dir))
        self.v("")

        self.mk_dir(dest_dir)

        fps_status = self.get_fingerprints_status()

        if not self.process_dir(
            distrib_templates_dir, dest_dir, fps_status, "templates"
        ):
            self.v("")
            self.v("Templates installation aborted")
            return False

        self.cp_file(
            os.path.join(distrib_templates_dir, self.FINGERPRINTS_FILENAME),
            os.path.join(dest_dir, self.FINGERPRINTS_FILENAME)
        )
        return True

    def setup(self, destination_directory=None):
        self.v("ARouteServer setup")
        self.v("")

        distrib_config_dir = get_config_dir()

        if destination_directory:
            dest_dir = destination_directory
        else:
            if self.ask:
                res, dest_dir = Ask().ask("Where do you want configuration files and templates "
                                          "to be stored?", default=self.DEFAULT_CFG_DIR_USR)
            else:
                res = True
                dest_dir = self.DEFAULT_CFG_DIR_USR

            if not res:
                self.v("")
                self.v("Setup aborted: no destination directory given")
                return False

        dest_dir = dest_dir.strip()

        if dest_dir not in self.DEFAULT_CFG_DIRS:
            self.v("WARNING: the directory that has been chosen is not one "
                   "of those where the program looks for to find "
                   "its configuration file: use the --cfg command line "
                   "argument to allow the program to find that file.")

        dest_dir = os.path.expanduser(dest_dir)
        program_cfg_file_path = os.path.join(dest_dir, "arouteserver.yml")

        if not destination_directory:
            if self.ask:
                res, yes_or_no = Ask().ask_yes_no(
                    "Do you confirm you want ARouteServer files to be "
                    "stored at {}?".format(dest_dir), default="yes")
            else:
                res = True
                yes_or_no = "yes"

            if not res or yes_or_no.lower() != "yes":
                self.v("")
                self.v("Setup aborted: destination directory not confirmed")
                return False

        self.v("Installing configuration files into {}...".format(dest_dir))
        self.v("")

        self.mk_dir(dest_dir)

        if not self.process_dir(distrib_config_dir, dest_dir):
            self.v("")
            self.v("Setup aborted while populating destination directory")
            return False

        # Load the new configuration, so that the following .setup_templates()
        # can work fine.
        self.load(program_cfg_file_path)

        if not self.setup_templates():
            self.v("")
            self.v("Setup aborted while populating templates directory")
            return False

        # Creating cache directory.
        # Using .get and not .get_dir because the dest dir may not exist.
        cache_dir = self.get("cache_dir")
        self.mk_dir(cache_dir)

        self.v("")
        self.v("Configuration complete!")
        self.v("")
        self.v("- edit the {} file to configure program's options".format(
            program_cfg_file_path))
        self.v("- edit the {} file to set your logging preferences".format(
            self.get("logging_config_file")))
        self.v("- set your route server's options and policies in {}\n"
               "  (edit it manually or use the 'arouteserver configure' "
               "command)".format(
                   self.get("cfg_general")))
        self.v("- configure route server clients in the {} file".format(
            self.get("cfg_clients")))

        return True

program_config = ConfigParserProgram()

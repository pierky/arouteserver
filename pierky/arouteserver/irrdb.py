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

import hashlib
import json
import logging
import re
import subprocess

from .cached_objects import CachedObject
from .config.validators import ValidatorPrefixListEntry
from .errors import IRRDBToolsError
from .ipaddresses import IPNetwork


class AS_SET_Bundle(object):

    def __init__(self, object_names):
        assert isinstance(object_names, list)

        self.object_names = sorted([n.upper() for n in set(object_names)])

        # id, internal unique identifier.
        buf = "_".join(self.object_names)
        hasher = hashlib.sha512()
        hasher.update(buf.encode("utf-8"))
        self.id = hasher.hexdigest()

        # descr, textual description of the bundle.
        # Do not use it in templates unless within comments.
        self.descr = ", ".join(self.object_names[:3])
        if len(self.object_names) > 3:
            self.descr += " and {} more".format(len(self.object_names) - 3)

        # name, brief textual representation of the bundle.
        # Only [a-zA-Z0-9_] characters.
        # Can be used in templates.
        if len(self.object_names) == 1:
            self.name = self.object_names[0]
        elif len(self.object_names) <= 3:
            self.name = "_".join(self.object_names)
        else:
            self.name = "{name}_and_{more}_more_{short_hash}".format(
                name=self.object_names[0],
                more=len(self.object_names) - 1,
                short_hash=self.id[:7]
            )
        self.name = re.sub("[^a-zA-Z0-9_]", "_", self.name)

class IRRDBInfo(CachedObject, AS_SET_Bundle):

    BGPQ3_DEFAULT_HOST = "rr.ntt.net"
    BGPQ3_DEFAULT_SOURCES = ("RIPE,APNIC,AFRINIC,ARIN,NTTCOM,ALTDB,"
                             "BBOI,BELL,JPIRR,LEVEL3,RADB,RGNET,"
                             "SAVVIS,TC")

    def __init__(self, object_names, *args, **kwargs):
        assert isinstance(object_names, list)

        CachedObject.__init__(self, *args, **kwargs)
        self.bgpq3_path = kwargs.get("bgpq3_path")
        self.bgpq3_host = kwargs.get("bgpq3_host", self.BGPQ3_DEFAULT_HOST)
        self.bgpq3_sources = kwargs.get("bgpq3_sources",
                                        self.BGPQ3_DEFAULT_SOURCES)

        AS_SET_Bundle.__init__(self, object_names)

    def _run_cmd(self, cmd):
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = proc.communicate()

        if proc.returncode != 0:
            err_msg = "bgpq3 exit code is {}".format(proc.returncode)
            if err is not None and err.strip():
                err_msg += ", stderr: {}".format(err)
            raise ValueError(err_msg)

        if err is not None and err.strip():
            logging.warning("bgpq3 succeeded but an error was "
                            "printed when executing '{}': {}".format(
                                " ".join(cmd), err.strip()
                            ))

        return out

class ASSet(IRRDBInfo):

    def load_data(self):
        logging.debug("Getting origin ASNs for "
                      "{} from IRRdb".format(self.descr))

        IRRDBInfo.load_data(self)

        # list of int
        self.asns = self.raw_data

    def _get_object_filename(self):
        return "{}-as_set.json".format(self.name)

    def _get_data(self):
        cmd = [self.bgpq3_path]
        cmd += ["-h", self.bgpq3_host]
        cmd += ["-S", self.bgpq3_sources]
        cmd += ["-3"]
        cmd += ["-j"]
        cmd += ["-f", "1"]
        cmd += ["-l", "asn_list"]
        cmd += self.object_names

        try:
            out = self._run_cmd(cmd)
        except Exception as e:
            raise IRRDBToolsError(
                "Can't get list of authorized ASNs for {}: {} - "
                "Command: {}".format(
                    self.descr, str(e), " ".join(cmd)
                )
            )

        try:
            data = json.loads(out.decode("utf-8"))
        except Exception as e:
            raise IRRDBToolsError(
                "Error while parsing bgpq3 output "
                "for the following command: '{}': {}".format(
                    " ".join(cmd), str(e)
                )
            )

        return data["asn_list"]

class RSet(IRRDBInfo):

    def __init__(self, object_names, ip_ver, allow_longer_prefixes, **kwargs):
        IRRDBInfo.__init__(self, object_names, **kwargs)

        assert ip_ver in (4, 6)
        self.ip_ver = ip_ver
        self.allow_longer_prefixes = allow_longer_prefixes

    def load_data(self):
        logging.debug("Getting prefixes for {} IPv{} "
                      "from IRRdb".format(self.descr, self.ip_ver))

        IRRDBInfo.load_data(self)

        # list of dict as returned by ValidatorPrefixListEntry
        self.prefixes = self.raw_data

    def _get_object_filename(self):
        return "{}-r_set-ipv{}.json".format(self.name, self.ip_ver)

    def _get_data(self):
        cmd = [self.bgpq3_path]
        cmd += ["-h", self.bgpq3_host]
        cmd += ["-S", self.bgpq3_sources]
        cmd += ["-3"]
        cmd += ["-4"] if self.ip_ver == 4 else ["-6"]
        cmd += ["-A"]
        cmd += ["-j"]
        cmd += ["-l", "prefix_list"]
        if self.allow_longer_prefixes:
            cmd += ["-R"]
            cmd += ["32"] if self.ip_ver == 4 else ["128"]
        cmd += self.object_names

        try:
            out = self._run_cmd(cmd)
        except Exception as e:
            raise IRRDBToolsError(
                "Can't get authorized prefix list for {} IPv{}: {} - "
                "Command: {}".format(
                    self.descr, self.ip_ver, str(e), " ".join(cmd)
                )
            )

        try:
            data = json.loads(out.decode("utf-8"))
        except Exception as e:
            raise IRRDBToolsError(
                "Error while parsing bgpq3 output "
                "for the following command: '{}': {}".format(
                    " ".join(cmd), str(e)
                )
            )

        return [self._parse_prefix(prefix) for prefix in data["prefix_list"]]

    def _parse_prefix(self, raw):
        prefix = IPNetwork(raw["prefix"])
        res = {
            "prefix": prefix.ip,
            "length": prefix.prefixlen,
            "exact": raw["exact"] if "exact" in raw else False
        }
        if res["exact"]:
            res["ge"] = None
            res["le"] = None
        else:
            if "greater-equal" in raw:
                res["ge"] = raw["greater-equal"]
            else:
                res["ge"] = None

            if "less-equal" in raw:
                res["le"] = raw["less-equal"]
            else:
                res["le"] = None

        return ValidatorPrefixListEntry().validate(res)

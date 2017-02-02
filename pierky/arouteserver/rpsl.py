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
import json
import os
import logging
import subprocess
import time

from .cached_objects import CachedObject
from .config.validators import ValidatorPrefixListEntry
from .errors import RPSLToolsError


class RPSLTools(CachedObject):

    def __init__(self, *args, **kwargs):
        CachedObject.__init__(self, *args, **kwargs)
        self.bgpq3_path = kwargs.get("bgpq3_path")

    pass

class ASSet(RPSLTools):

    def __init__(self, object_name, **kwargs):
        RPSLTools.__init__(self, **kwargs)
        self.object_name = object_name

        logging.debug("Getting origin ASNs for "
                      "{} from IRRdb".format(self.object_name))

        self.load_data()
    
        # list of int
        self.asns = self.raw_data

    def _get_object_filename(self):
        return "{}-as_set.json".format(self.object_name)

    def _get_data(self):
        cmd = [self.bgpq3_path]
        cmd += ["-3"]
        cmd += ["-j"]
        cmd += ["-f", "1"]
        cmd += ["-l", "asn_list"]
        cmd += [self.object_name]

        try:
            out = subprocess.check_output(cmd)
        except Exception as e:
            raise RPSLToolsError(
                "Can't get AS-SET data for {}: {}".format(
                    self.object_name, str(e)
                )
            )

        try:
            data = json.loads(out)
        except Exception as e:
            raise RPSLToolsError(
                "Error while parsing bgpq3 output "
                "for the following command: '{}': {}".format(
                    " ".join(cmd), str(e)
                )
            )

        return data["asn_list"]

class RSet(RPSLTools):

    def __init__(self, object_name, ip_ver, **kwargs):
        RPSLTools.__init__(self, **kwargs)
        self.object_name = object_name
        assert ip_ver in (4, 6)
        self.ip_ver = ip_ver

        logging.debug("Getting prefixes for {} IPv{} "
                      "from IRRdb".format(self.object_name, self.ip_ver))

        self.load_data()

        # list of dict as returned by ValidatorPrefixListEntry
        self.prefixes = self.raw_data

    def _get_object_filename(self):
        return "{}-r_set-ipv{}.json".format(self.object_name, self.ip_ver)

    def _get_data(self):
        cmd = [self.bgpq3_path]
        cmd += ["-3"]
        cmd += ["-4"] if self.ip_ver == 4 else ["-6"]
        cmd += ["-A"]
        cmd += ["-j"]
        cmd += ["-l", "prefix_list"]
        cmd += [self.object_name]

        try:
            out = subprocess.check_output(cmd)
        except Exception as e:
            raise RPSLToolsError(
                "Can't get R-SET data for {} IPv{}: {}".format(
                    self.object_name, self.ip_ver, str(e)
                )
            )

        try:
            data = json.loads(out)
        except Exception as e:
            raise RPSLToolsError(
                "Error while parsing bgpq3 output "
                "for the following command: '{}': {}".format(
                    " ".join(cmd), str(e)
                )
            )

        return [self._parse_prefix(prefix) for prefix in data["prefix_list"]]

    def _parse_prefix(self, raw):
        prefix = ipaddr.IPNetwork(raw["prefix"])
        res = {
            "prefix": str(prefix.ip),
            "length": prefix.prefixlen,
            "exact": raw["exact"] if "exact" in raw else False,
            "comment": self.object_name
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

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

import re

from docker import DockerInstance
from instances import Route


class BIRDInstance(DockerInstance):

    DOCKER_IMAGE = "pierky/bird:1.6.3"

    def __init__(self, *args, **kwargs):
        DockerInstance.__init__(self, *args, **kwargs)
        self.protocols_status = {}

    def reload_config(self):
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        res = self._birdcl("configure")

        if "Reconfigured" in res:
            return True
        else:
            return False

    def _get_protocols_status(self, force_update=False):
        if force_update:
            self.protocols_status = {}
        if self.protocols_status:
            return
        out = self._birdcl("show protocols all")
        lines = out.split("\n")
        last_protoname = None
        last_proto_status = None
        for line in lines:
            if line.strip() and not line.startswith(" "):
                last_protoname = line.split(" ")[0]
                last_proto_status = re.search("\sup\s", line) is not None
                continue
            if line.strip().startswith("Neighbor address: "):
                neighbor_ip = line.strip().split(": ")[1]
                if last_protoname is not None and last_proto_status is not None:
                    self.protocols_status[last_protoname] = {
                        "ip": neighbor_ip,
                        "is_up": last_proto_status
                    }
                    last_protoname = None
                    last_proto_status = None
                else:
                    raise Exception(
                        "{}: neighbor with unknown protocol name/status: {}".format(
                            self.name, neighbor_ip
                        )
                    )
        if not self.protocols_status:
            raise Exception("{}: can't build protocols status map".format(self.name))

    def bgp_session_is_up(self, other_inst, force_update=False):
        self._get_protocols_status(force_update=force_update)
        for proto in self.protocols_status:
            if self.protocols_status[proto]["ip"] == other_inst.ip:
                return self.protocols_status[proto]["is_up"]
        raise Exception(
            "Can't get BGP session status for {} on {} "
            "(looking for {})".format(other_inst.name, self.name, other_inst.ip))

    def get_routes(self, prefix, include_filtered=False, only_best=False):
        if include_filtered and only_best:
            raise Exception("Can't set both include_filtered and only_best")

        self._get_protocols_status()
        routes = []

        regex = "[ ]+via ([0-9\.\:a-f]+)[^\[]+\[([^\s]+)[^\n]+"

        options = [""]
        if include_filtered:
            options.append("filtered")
        if only_best:
            options.append("primary")

        for option in options:
            cmd = "show route {} all {}".format(prefix, option)
            out = self._birdcl(cmd)
            match = re.search("^[0-9\.\:a-f]+/[0-9]+{}".format(regex), out, re.MULTILINE)
            if match:
                route = {}
                lines = out.split("\n")
                for line in lines:
                    if not line.strip():
                        continue
                    match = re.search(regex, line)
                    if match:
                        if route:
                            route["filtered"] = option == "filtered"
                            routes.append(Route(**route))
                            route = {}
                        route["prefix"] = prefix
                        route["via"] = self.protocols_status[match.group(2)]["ip"]
                    else:
                        if "BGP.as_path:" in line:
                            route["as_path"] = line.split(": ")[1].strip()
                        if "BGP.next_hop:" in line:
                            route["next_hop"] = line.split(": ")[1].strip()
                        if "BGP.community:" in line:
                            route["std_comms"] = line.split(": ")[1].strip()
                        if "BGP.large_community:" in line:
                            route["lrg_comms"] = line.split(": ")[1].strip()
                        if "BGP.ext_community:" in line:
                            route["ext_comms"] = line.split(": ")[1].strip()
                route["filtered"] = option == "filtered"
                routes.append(Route(**route))
        return routes

    def get_protocol_name_by_ip(self, ip):
        self._get_protocols_status()
        for proto in self.protocols_status:
            if self.protocols_status[proto]["ip"] == ip:
                return proto
        raise Exception("{}: can't find protocolo name from ip {}".format(self.name, ip))
        return None

    def log_contains(self, s):
        out = self.run_cmd("cat /var/log/bird.log")
        if s in out:
            return True
        else:
            return False

class BIRDInstanceIPv4(BIRDInstance):

    def _get_start_cmd(self):
        return "bird -c /etc/bird/bird.conf -d"

    def _birdcl(self, cmd):
        return self.run_cmd("birdcl {}".format(cmd))

class BIRDInstanceIPv6(BIRDInstance):

    def _get_start_cmd(self):
        return "bird6 -c /etc/bird/bird.conf -d"

    def _birdcl(self, cmd):
        return self.run_cmd("birdcl6 {}".format(cmd))


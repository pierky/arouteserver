# Copyright (C) 2017-2018 Pier Carlo Chiodi
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

from .docker import DockerInstance
from .instances import Route, BGPSpeakerInstance, InstanceNotRunning


class BIRDInstance(DockerInstance):
    """This class implements BIRD-specific methods.

    This class is derived from :class:`DockerInstance`, that implements
    some Docker-specific methods to start/stop the instance and to run
    commands on it.
    """

    MESSAGE_LOGGING_SUPPORT = True

    DOCKER_IMAGE = "pierky/bird:1.6.4"

    def __init__(self, *args, **kwargs):
        DockerInstance.__init__(self, *args, **kwargs)

        # See the docstring of _get_protocols_status()
        self.protocols_status = {}

        self.routes = []
        self.log = None

    def restart(self):
        """Restart BIRD.

        It runs the "[birdcl/birdcl6] configure" and "restart all" commands.
        """
        if self.reload_config():

            res = self._birdcl("restart all")

            if "restarted" in res:
                return True
            else:
                return False
        else:
            return False

    def reload_config(self):
        """Reload BIRD configuration.

        It runs the "[birdcl/birdcl6] configure" command to reload BIRD's
        configuration.
        """
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        res = self._birdcl("configure")

        if "Reconfigured" in res:
            return True
        else:
            return False

    def _get_protocols_status(self, force_update=False):
        """Given the BIRD 'show protocols all' output, build the status map.

        This function fills the self.protocols_status dictionary with entries
        in this format:

        "<BIRD protocol name>": {
            "ip": "<neighbor IP address>",
            "is_up": [True|False]
        }

        This dictionary is used by other functions to understand BGP
        sessions status and to map neighbors IP address to instance name.
        """

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
                        "{}: neighbor with unknown "
                        "protocol name/status: {}".format(
                            self.name, neighbor_ip
                        )
                    )

        if not self.protocols_status:
            raise Exception(
                "{}: can't build protocols status map".format(self.name)
            )

    def get_bgp_session(self, other_inst_or_ip, force_update=False):
        if isinstance(other_inst_or_ip, BGPSpeakerInstance):
            other_inst_ip = other_inst_or_ip.ip
        else:
            other_inst_ip = other_inst_or_ip
        self._get_protocols_status(force_update=force_update)
        for proto in self.protocols_status:
            if self.protocols_status[proto]["ip"] == other_inst_ip:
                return self.protocols_status[proto]
        return None

    def _get_all_routes(self):

        def add_route(route):
            if not route:
                return

            new_route = Route(**route)
            self.routes.append(new_route)
            route = {}

        self.routes = []

        self._get_protocols_status()

        # ' via 192.0.2.11 on eth0 [AS1_1 09:57:45] * (100) [AS101i]'
        #       ----------          -----
        route_beginning_re = (
            "[ ]+via "
            "(?P<via>[0-9\.\:a-f]+)"
            "[^\[]+"
            "\[(?P<via_name>[^\s]+)"
        )

        # '101.2.128.0/24     via 192.0.2.11 on eth0 [AS1_1 09:57:45] * (100) [AS101i]'
        #  --------------         ----------          -----
        prefix_beginning_re = "^(?P<prefix>[0-9\.\:a-f]+/[0-9]+){}".format(
            route_beginning_re
        )

        route_beginning_patt = re.compile(route_beginning_re)
        prefix_beginning_patt = re.compile(prefix_beginning_re)

        last_prefix = None
        route = {}
        for option in ["", "filtered"]:
            cmd = "show route all {}".format(option)
            out = self._birdcl(cmd)
            for line in out.split("\n"):
                new_prefix_match = prefix_beginning_patt.search(line)
                new_route_match = route_beginning_patt.search(line)
                if new_prefix_match or new_route_match:
                    # A new route for the last prefix or a block of routes for
                    # a new prefix begins here.
                    add_route(route)
                    route = {}

                    if new_prefix_match:
                        last_prefix = new_prefix_match.group("prefix")
                        via_name = new_prefix_match.group("via_name")
                    else:
                        via_name = new_route_match.group("via_name")

                    route["prefix"] = last_prefix
                    route["via"] = self.protocols_status[via_name]["ip"]
                    route["best"] = (option == "" and " * " in line)
                    route["filtered"] = option == "filtered"
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
                    if "BGP.local_pref:" in line:
                        route["localpref"] = line.split(": ")[1].strip()
            add_route(route)
            route = {}

    def get_routes(self, prefix, include_filtered=False, only_best=False):
        if include_filtered and only_best:
            raise Exception("Can't set both include_filtered and only_best")

        if not self.routes:
            self._get_all_routes()

        routes = []
        for route in self.routes:
            if prefix is None or route.prefix == prefix:
                if route.filtered and not include_filtered:
                    continue
                if not route.best and only_best:
                    continue
                routes.append(route)

        return routes

    def get_protocol_name_by_ip(self, ip):
        self._get_protocols_status()
        for proto in self.protocols_status:
            if self.protocols_status[proto]["ip"] == ip:
                return proto
        raise Exception(
            "{}: can't find protocol name from ip {}".format(self.name, ip)
        )

    def log_contains(self, s):
        if not self.log:
            self.log = self.run_cmd("cat /var/log/bird.log")

        if s in self.log:
            return True
        else:
            return False

    def log_contains_errors(self, allowed_errors=[], list_errors=False):
        out = self.run_cmd("cat /var/log/bird.log")

        errors_found = False
        errors = []
        for line in out.split("\n"):
            if "<ERR>" not in line:
                continue
            if any([msg for msg in allowed_errors if msg in line]):
                continue
            errors_found = True
            errors.append(line)
        if list_errors:
            return errors_found, "\n".join(errors)
        return errors_found

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

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
import re
import time

from kvm import KVMInstance
from instances import Route, BGPSpeakerInstance, InstanceNotRunning

class OpenBGPDRoute(Route):

    def _parse_bgp_communities(self, communities):
        if not communities:
            return []

        res = []
        for bgp_comm in communities.split(" "):
            if bgp_comm == "BLACKHOLE":
                res.append("65535:666")
                continue
            res.append(bgp_comm)
        return res

    def _parse_ext_bgp_communities(self, communities):
        if not communities:
            return []

        res = []
        for bgp_comm in communities.split(", "):
            parts = bgp_comm.split(" ")
            res.append("{}:{}".format(parts[0], parts[1]))
        return res

class OpenBGPDInstance(KVMInstance):
    """This class implements OpenBGPD-specific methods.

    This class is derived from :class:`KVMInstance`, that implements
    some kvm-specific methods to start/stop the instance and to run
    commands on it.

    The VIRSH_DOMAINNAME attribute must be set by derived classes on the
    basis of the specific version of OpenBSD they represent.
    """

    MESSAGE_LOGGING_SUPPORT = False

    VIRSH_DOMAINNAME = None

    def __init__(self, *args, **kwargs):
        KVMInstance.__init__(self, *args, **kwargs)

        self.neighbors_status = None
        self.routes = {}

    def _graceful_shutdown(self):
        self.run_cmd("shutdown -h -p now")
        return True

    def reload_config(self):
        """Reload OpenBGPD configuration.

        Executes '/etc/rc.d/bgpd stop' and then '/etc/rc.d/bgpd start'.
        """
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        try:
            self.run_cmd("mkdir /etc/bgpd")
        except:
            pass

        self._mount_files()

        self.run_cmd("chmod 0600 /etc/bgpd.conf")
        self.run_cmd("chmod 0600 /etc/bgpd/*")

        self.run_cmd("/etc/rc.d/bgpd stop")
        time.sleep(5)
        self.run_cmd("bgpd -vdn")
        self.run_cmd("/etc/rc.d/bgpd start")
        time.sleep(5)

        return True

    def _get_neighbors_status(self, force_update=False):
        if force_update:
            self.neighbors_status = None

        if self.neighbors_status:
            return

        self.neighbors_status = []

        out = self.run_cmd("bgpctl -n show summary terse")
        lines = out.split("\n")

        for line in lines:
            if not line.strip():
                continue

            parts = line.split(" ")
            if len(parts) != 3:
                raise Exception(
                    "{}: can't parse neighbor status: '{}'".format(
                        self.name, line
                    )
                )

            ip = parts[0].strip()
            asn = int(parts[1].strip())
            status = parts[2].strip()
            self.neighbors_status.append({
                "ip": ip,
                "is_up": "Established" in status,
                "asn": asn,
            })

        if not self.neighbors_status:
            raise Exception(
                "{}: can't get neighbors status".format(self.name)
            )

    def get_bgp_session(self, other_inst_or_ip, force_update=False):
        if isinstance(other_inst_or_ip, BGPSpeakerInstance):
            other_inst_ip = other_inst_or_ip.ip
        else:
            other_inst_ip = other_inst_or_ip
        self._get_neighbors_status(force_update=force_update)
        for neighbor in self.neighbors_status:
            if neighbor["ip"] == other_inst_ip:
                return neighbor
        return None

    def _parse_routes(self, out):
        regex = "BGP routing table entry for ([0-9\.\:a-f]+/[0-9]+)"

        route = {}
        routes = []

        lines = out.split("\n")
        last_line_new_route = False
        for line_raw in lines:
            line = line_raw.strip()
            if not line:
                continue

            match = re.search(regex, line, re.MULTILINE)

            if match:
                if route:
                    routes.append(OpenBGPDRoute(**route))
                    route = {}
                route["prefix"] = match.group(1)
                last_line_new_route = True
                continue

            if last_line_new_route:
                asns = line.split(" ")
                for asn in asns:
                    if not asn.isdigit():
                        raise Exception(
                            "Error parsing {}: invalid AS_PATH: {}".format(
                                route["prefix"], line
                            )
                        )
                route["as_path"] = line
                last_line_new_route = False
                continue

            if line.startswith("Nexthop"):
                parts = line.split(" ")
                route["next_hop"] = parts[1]
                route["via"] = parts[5]
            elif line.startswith("Origin"):
                route["best"] = "best" in line

                match = re.search("localpref ([0-9]+)", line)
                route["localpref"] = int(match.group(1))
            elif line.startswith("Communities:"):
                route["std_comms"] = line.split(": ")[1]
            elif line.startswith("Ext. communities:"):
                route["ext_comms"] = line.split(": ")[1]
            elif line.startswith("Large Communities:"):
                route["lrg_comms"] = line.split(": ")[1]
            last_line_new_route = False

        if last_line_new_route:
            raise Exception("Error parsing routes: last route {}".format(
                route["prefix"] if route else "unknown"))

        if route:
            routes.append(OpenBGPDRoute(**route))
            route = {}

        return routes

    def _get_routes_from_neighbor(self, ip):
        out = self.run_cmd(
            "bgpctl -n show rib in neighbor {} detail".format(ip)
        )
        return self._parse_routes(out)

    def _get_routes_from_main(self):
        out = self.run_cmd(
            "bgpctl -n show ip bgp detail"
        )
        return self._parse_routes(out)

    def _get_routes_from_all_sources(self):
        self.routes = {
            "main": [],
        }
        self.routes["main"] = self._get_routes_from_main()

    def _route_is_in(self, route, route_list):
        for other_route in route_list:
            if route.prefix == other_route.prefix and \
                route.via == other_route.via and \
                route.as_path == other_route.as_path and \
                route.next_hop == other_route.next_hop and \
                route.std_comms == other_route.std_comms and \
                route.ext_comms == other_route.ext_comms and \
                route.lrg_comms == other_route.lrg_comms:
                return True
        return False

    def get_routes(self, prefix, include_filtered=False, only_best=False):
        if include_filtered and only_best:
            raise Exception("Can't set both include_filtered and only_best")

        if not self.routes:
            self._get_neighbors_status(force_update=True)
            self._get_routes_from_all_sources()

        res = []

        for route in self.routes["main"]:
            if route.prefix != prefix:
                continue
            if only_best and not route.best:
                continue
            if not self._route_is_in(route, res):
                res.append(route)

        return res

    def log_contains(self, s):
        return True

class OpenBGPD60Instance(OpenBGPDInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd60"

class OpenBGPD61Instance(OpenBGPDInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd61"

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

import re
import time

from .kvm import KVMInstance
from .docker import DockerInstance
from .instances import Route, BGPSpeakerInstance, InstanceNotRunning

class OpenBGPDRoute(Route):

    def _parse_bgp_communities(self, communities):
        if not communities:
            return []

        res = []
        for bgp_comm in communities.split(" "):
            if bgp_comm == "BLACKHOLE":
                res.append("65535:666")
                continue
            if bgp_comm == "GRACEFUL_SHUTDOWN":
                res.append("65535:0")
                continue
            res.append(bgp_comm)
        return res

    def _parse_ext_bgp_communities(self, communities):
        if not communities:
            return []

        res = []

        # If ', ' is found in the value of 'communities', it
        # means we're processing a pre 6.6 output format.
        if ", " in communities:
            for bgp_comm in communities.split(", "):
                parts = bgp_comm.split(" ")
                res.append("{}:{}".format(parts[0], parts[1]))

            return res

        # If ', ' is not found, it's either a post 6.6 format
        # where different communities are separated just by a
        # space, or it's just one single community:
        # soo 65535:65281
        # rt 64537:10
        # rt 64537:10 rt 64538:20

        next_field_should_be = "rt_soo"
        rt_soo = ""
        comm = ""

        for part in communities.split(" "):
            if next_field_should_be == "rt_soo":
                if part not in ("rt", "soo"):
                    raise ValueError(
                        "Error while processing the extended communities "
                        "string '{}': expected 'rt' or 'soo', but '{}' "
                        "found.".format(communities, part)
                    )
                rt_soo = part
                next_field_should_be = "comm"
            elif next_field_should_be == "comm":
                if ":" not in part:
                    raise ValueError(
                        "Error while processing the extended communities "
                        "string '{}': ':' not found in the community '{}' "
                        "part.".format(communities, part)
                    )
                comm = part

                res.append("{}:{}".format(rt_soo, comm))

                next_field_should_be = "rt_soo"

        if next_field_should_be != "rt_soo":
            raise ValueError(
                "Error while processing the extended communities "
                "string '{}': one part of the string remained "
                "unprocessed.".format(communities)
            )

        return res

class OpenBGPDInstance(object):
    """This class implements an interface to OpenBGPD client.

    Only methods needed to interact with the OpenBGPD bgpctl
    client are implemented here. The methods which interact with
    the underlying OS are offloaded to the other classes.

    This class is supposed to be used in conjunction with
    KVMInstance or DockerInstance since it uses some of
    their methods and properties.
    """

    MESSAGE_LOGGING_SUPPORT = False

    def __init__(self):
        self.neighbors_status = None
        self.routes = {}

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
                raw_as_path = line
                if "{" in raw_as_path:
                    # Stripping as_set in strings like this:
                    #   222 333 { 333 333 }
                    as_path = raw_as_path[0:raw_as_path.index("{")].strip()
                    as_set = raw_as_path[raw_as_path.index("{") + 1:-1].strip()
                else:
                    as_path = raw_as_path
                    as_set = None
                asns = as_path.split(" ")
                for asn in asns:
                    if not asn.isdigit():
                        raise Exception(
                            "Error parsing {}: invalid AS_PATH: {}".format(
                                route["prefix"], line
                            )
                        )
                route["as_path"] = as_path
                route["as_set"] = as_set
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
            elif line.lower().startswith("ext. communities:"):
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
            if prefix and route.prefix.lower() != prefix.lower():
                continue
            if only_best and not route.best:
                continue
            if not self._route_is_in(route, res):
                res.append(route)

        return res


    def log_contains(self, s):
        return True

    def log_contains_errors(self, allowed_errors=[], list_errors=False):
        if list_errors:
            return False, ""
        return False

class OpenBGPDClassicInstance(OpenBGPDInstance, KVMInstance):
    """This class implements OpenBGPD-specific methods.

    This class is derived from :class:`KVMInstance`, that implements
    some kvm-specific methods to start/stop the instance and to run
    commands on it.

    The VIRSH_DOMAINNAME attribute must be set by derived classes on the
    basis of the specific version of OpenBSD they represent.
    """

    VIRSH_DOMAINNAME = None

    def __init__(self, *args, **kwargs):
        OpenBGPDInstance.__init__(self)
        KVMInstance.__init__(self, *args, **kwargs)

    def _graceful_shutdown(self):
        self.run_cmd("shutdown -h -p now")
        return True

    def restart(self):
        """Restart OpenBGPD.

        Updates the configuration files, then executes '/etc/rc.d/bgpd stop'
        and then '/etc/rc.d/bgpd -f start'.
        """
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        try:
            self.run_cmd("mkdir /etc/bgpd")
        except:
            pass

        self._mount_files()

        self.run_cmd("chmod 0600 /etc/bgpd.conf")
        self.run_cmd("touch /etc/bgpd/placeholder")
        self.run_cmd("chmod 0600 /etc/bgpd/*")

        self.run_cmd("/etc/rc.d/bgpd stop")
        time.sleep(5)
        self.run_cmd("ndp -c | true")
        self.run_cmd("bgpd -dn")
        self.run_cmd("/etc/rc.d/bgpd -f start")
        time.sleep(5)

        return True

    def reload_config(self):
        """Reload OpenBGPD configuration.

        Updates the configuration files, then executes '/etc/rc.d/bgpd reload'.
        """
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        self._mount_files()

        self.run_cmd("bgpd -dn")
        self.run_cmd("/etc/rc.d/bgpd reload")
        self.run_cmd("ndp -c | true")
        time.sleep(5)

        return True

    def log_contains(self, s):
        return True

    def log_contains_errors(self, allowed_errors=[], list_errors=False):
        if list_errors:
            return False, ""
        return False

class OpenBGPDPortableInstance(OpenBGPDInstance, DockerInstance):
    """This class implements OpenBGPD-specific methods for the Portable edition.

    This class is derived from :class:`DockerInstance`, that implements
    some docker-specific methods to start/stop the instance and to run
    commands on it.

    The VIRSH_DOMAINNAME attribute must be set by derived classes on the
    basis of the specific version of OpenBSD they represent.
    """

    def __init__(self, *args, **kwargs):
        OpenBGPDInstance.__init__(self)
        DockerInstance.__init__(self, *args, **kwargs)

    def restart(self):
        """Restart OpenBGPD.

        Updates the configuration file, then clear all the neighbors.
        """

        self.reload_config()

        self._get_neighbors_status(force_update=True)
        for neighbor in self.neighbors_status:
            ip = neighbor["ip"]
            self.run_cmd("bgpctl neighbor {} clear".format(ip))

        time.sleep(5)

        return True

    def reload_config(self):
        """Reload OpenBGPD configuration.

        Executes 'bgpctl reload'.
        """
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        try:
            res = self.run_cmd("bgpctl reload")
        except:
            pass

        if "request processed" in res:
            time.sleep(5)
            return True

        return False

    def _get_start_cmd(self):
        return "bgpd -f /etc/bgpd.conf -d"

class OpenBGPD60Instance(OpenBGPDClassicInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd60"

    TAG = "openbgpd60"

class OpenBGPD61Instance(OpenBGPDClassicInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd61"

    TAG = "openbgpd61"

class OpenBGPD62Instance(OpenBGPDClassicInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd62"

    TAG = "openbgpd62"

class OpenBGPD63Instance(OpenBGPDClassicInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd63"

    TAG = "openbgpd63"

class OpenBGPD64Instance(OpenBGPDClassicInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd64"

    TAG = "openbgpd64"

class OpenBGPD65Instance(OpenBGPDClassicInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd65"

    TAG = "openbgpd65"

    BGP_SPEAKER_VERSION = "6.5"
    TARGET_VERSION = "6.5"

class OpenBGPD66Instance(OpenBGPDClassicInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd66"

    TAG = "openbgpd66"

    BGP_SPEAKER_VERSION = "6.6"
    TARGET_VERSION = "6.6"

class OpenBGPD67Instance(OpenBGPDClassicInstance):

    VIRSH_DOMAINNAME = "arouteserver_openbgpd67"

    TAG = "openbgpd67"

    BGP_SPEAKER_VERSION = "6.7"
    TARGET_VERSION = "6.7"

OpenBGPDPreviousInstance = OpenBGPD66Instance
OpenBGPDLatestInstance = OpenBGPD67Instance

class OpenBGPD65PortableInstance(OpenBGPDPortableInstance):

    DOCKER_IMAGE = "pierky/openbgpd:6.5p1"

    TAG = "openbgpd65p"

class OpenBGPD66PortableInstance(OpenBGPDPortableInstance):

    DOCKER_IMAGE = "pierky/openbgpd:6.6p0"

    TAG = "openbgpd66p"

    BGP_SPEAKER_VERSION = "6.6p0"
    # TARGET_VERSION not set here because it's assumed to be
    # the same of the OpenBGPD Latest one.


class OpenBGPD67PortableInstance(OpenBGPDPortableInstance):

    DOCKER_IMAGE = "pierky/openbgpd:6.7p0"

    TAG = "openbgpd67p"

    BGP_SPEAKER_VERSION = "6.7p0"
    # TARGET_VERSION not set here because it's assumed to be
    # the same of the OpenBGPD Latest one.

OpenBGPDPortableLatestInstance = OpenBGPD67PortableInstance

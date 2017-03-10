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

import time

from kvm import KVMInstance
from instances import Route, BGPSpeakerInstance


class OpenBGPDInstance(KVMInstance):
    """This class implements OpenBGPD-specific methods.

    This class is derived from :class:`KVMInstance`, that implements
    some kvm-specific methods to start/stop the instance and to run
    commands on it.
    """

    VIRSH_DOMAINNAME = "openbsd1"

    def __init__(self, *args, **kwargs):
        KVMInstance.__init__(self, *args, **kwargs)

        self.neighbors_status = None

    def _graceful_shutdown(self):
        self.run_cmd("shutdown -h now")
        return True

    def reload_config(self):
        """Reload OpenBGPD configuration.

        Executes '/etc/rc.d/bgpd stop' and then '/etc/rc.d/bgpd start'.
        """
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        self._mount_files()

        self.run_cmd("/etc/rc.d/bgpd stop")
        time.sleep(5)
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
            status = parts[2].strip()
            self.neighbors_status.append({
                "ip": ip,
                "is_up": "Established" in status
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

    def get_routes(self, prefix, include_filtered=False, only_best=False):
        if include_filtered and only_best:
            raise Exception("Can't set both include_filtered and only_best")

        #TODO: not implemented yet
        routes = []
        return routes

    def log_contains(self, s):
        return True

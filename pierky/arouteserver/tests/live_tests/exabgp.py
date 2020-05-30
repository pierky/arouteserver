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

from .docker import DockerInstance
from .instances import InstanceNotRunning


class ExaBGPInstance(DockerInstance):

    MESSAGE_LOGGING_SUPPORT = False

    DOCKER_IMAGE = "pierky/exabgp:4.2.7"

    TAG = "exabgp"

    def restart(self):
        raise NotImplementedError()

    def reload_config(self):
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        # no-op, ExaBPG is only used as a route-server client, no needs
        # to reload its configuration.
        return True

    def get_bgp_session(self, other_inst_or_ip, force_update=False):
        raise NotImplementedError()

    def get_routes(self, prefix, include_filtered=False, only_best=False):
        # no-op, ExaBPG is only used as a route-server client, no needs
        # to dump its routes.
        return []

    def log_contains(self, s):
        raise NotImplementedError()

    def log_contains_errors(self, allowed_errors=[], list_errors=False):
        raise NotImplementedError()

    def _get_start_cmd(self):
        return (
            "exabgp --env /etc/exabgp/exabgp.env /etc/exabgp/exabgp.conf"
        )

# Copyright (C) 2017-2026 Pier Carlo Chiodi
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


class RTRTRInstance(DockerInstance):
    """An RTR cache server fed by a static JSON file.

    RTRTR is used here (instead of a real RPKI validator) because its
    'json' unit can read a local file containing both the 'roas' and
    the 'aspas' elements, in the very same RIPE RPKI Validator format
    that ARouteServer itself consumes. That makes the data served over
    RTR completely predictable, and it doesn't need any access to the
    real RPKI repositories.

    Its 'rtr' target speaks version 2 of the RTR protocol, which is
    the only one that carries ASPA payloads.
    """

    DOCKER_IMAGE = "nlnetlabs/rtrtr:v0.3.3"

    TAG = "rtrtr"

    def restart(self):
        raise NotImplementedError()

    def reload_config(self):
        raise NotImplementedError()

    def _get_start_cmd(self):
        return "-c /etc/rtrtr/rtrtr.conf --stderr"

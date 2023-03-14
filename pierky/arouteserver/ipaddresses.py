# Copyright (C) 2017-2023 Pier Carlo Chiodi
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

import ipaddress


class IPAddress(object):

    def __init__(self, ip):
        self.obj = ipaddress.ip_address(ip)
        self.ip = str(self.obj.compressed)

        self.version = self.obj.version

    def __str__(self):
        return self.ip


class IPNetwork(object):

    def __init__(self, ip):
        self.obj = ipaddress.ip_network(ip)
        self.ip = str(self.obj.network_address)

        self.prefixlen = self.obj.prefixlen
        self.max_prefixlen = self.obj.max_prefixlen
        self.version = self.obj.version

    def __str__(self):
        return "{}/{}".format(self.ip, self.prefixlen)

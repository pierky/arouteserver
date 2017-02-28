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

import logging

from .base import BaseConfigEnricher, BaseConfigEnricherThread
from ..errors import BuilderError, ARouteServerError, \
                    PeeringDBError, PeeringDBNoInfoError
from ..peering_db import PeeringDBNet

class PeeringDBConfigEnricher_WorkerThread(BaseConfigEnricherThread):

    DESCR = "PeeringDB"

    def __init__(self, *args, **kwargs):
        BaseConfigEnricherThread.__init__(self, *args, **kwargs)

        self.ip_ver = None
        self.cfg_general = None
        self.cache_dir = None
        self.cache_expiry = None

    def do_task(self, task):
        client = task

        client_max_prefix = client["cfg"]["filtering"]["max_prefix"]
        if not client_max_prefix["action"]:
            # No max-prefix action given for this client:
            # no needs to know its max-pref limit.
            return None

        res = {"limit4": None, "limit6": None}

        for ip_ver in (4, 6):
            if self.ip_ver is not None and self.ip_ver != ip_ver:
                # The current AF is not used.
                continue

            if client_max_prefix["limit_ipv{}".format(ip_ver)]:
                # Client uses a specific limit:
                # no needs to gather info from PeeringDB for
                # the current address family.
                res["limit{}".format(ip_ver)] = \
                    client_max_prefix["limit_ipv{}".format(ip_ver)]
                continue

            general_limit = self.cfg_general["filtering"]["max_prefix"]["general_limit_ipv{}".format(ip_ver)]

            if not client_max_prefix["peering_db"]:
                # PeeringDB disabled for this client:
                # using general limit.
                res["limit{}".format(ip_ver)] = general_limit
                continue

            try:
                peeringdb_limit = None
                net = PeeringDBNet(client["asn"],
                                   cache_dir=self.cache_dir,
                                   cache_expiry=self.cache_expiry)
                if ip_ver == 4:
                    peeringdb_limit = net.info_prefixes4
                else:
                    peeringdb_limit = net.info_prefixes6

                res["limit{}".format(ip_ver)] = peeringdb_limit or general_limit

            except PeeringDBNoInfoError:
                # No data found on PeeringDB.
                logging.debug("No data found on PeeringDB "
                              "for AS{} while looking for "
                              "max-prefix limit.".format(client["asn"]))
                pass
            except PeeringDBError as e:
                raise BuilderError(
                    "An error occurred while retrieving info from PeeringDB "
                    "for ASN {}: {}".format(
                        client["asn"], str(e) or "error unknown"
                    )
                )

        return res["limit4"], res["limit6"]

    def save_data(self, task, data):
        client = task
        limit4, limit6 = data
        if limit4:
            client["cfg"]["filtering"]["max_prefix"]["limit_ipv4"] = limit4
        if limit6:
            client["cfg"]["filtering"]["max_prefix"]["limit_ipv6"] = limit6

class PeeringDBConfigEnricher(BaseConfigEnricher):

    WORKER_THREAD_CLASS = PeeringDBConfigEnricher_WorkerThread

    def _config_thread(self, thread):
        thread.ip_ver = self.builder.ip_ver
        thread.cfg_general = self.builder.cfg_general
        thread.cache_dir = self.builder.cache_dir
        thread.cache_expiry = self.builder.cache_expiry

    def add_tasks(self):
        # Enqueuing tasks.
        for client in self.builder.cfg_clients.cfg["clients"]:
            self.tasks_q.put(client)

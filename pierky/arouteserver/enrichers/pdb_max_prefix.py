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

import logging

from .base import BaseConfigEnricher, BaseConfigEnricherThread
from ..errors import BuilderError, PeeringDBError, PeeringDBNoInfoError
from ..peering_db import PeeringDBNet

class PeeringDBConfigEnricher_MaxPrefix_WorkerThread(BaseConfigEnricherThread):

    DESCR = "PeeringDB max-prefix"

    def __init__(self, *args, **kwargs):
        BaseConfigEnricherThread.__init__(self, *args, **kwargs)

        self.ip_ver = None
        self.cfg_general = None
        self.cache_dir = None
        self.cache_expiry = None
        self.general_limits = None

    def do_task(self, task):
        asn, _ = task

        try:
            net = PeeringDBNet(asn,
                               cache_dir=self.cache_dir,
                               cache_expiry=self.cache_expiry)
            net.load_data()

            return net.info_prefixes4 or self.general_limits["ipv4"], \
                    net.info_prefixes6 or self.general_limits["ipv6"]

        except PeeringDBNoInfoError:
            # No data found on PeeringDB.
            logging.debug("No data found on PeeringDB "
                          "for AS{} while looking for "
                          "max-prefix limit.".format(asn))
            pass
        except PeeringDBError as e:
            logging.error(
                "An error occurred while retrieving info from PeeringDB "
                "for ASN {}: {}".format(
                    asn, str(e) or "error unknown"
                )
            )
            raise BuilderError()

    @staticmethod
    def _set_client_max_prefix_from_pdb(client, afi, pdb_value):
        max_prefix = client["cfg"]["filtering"]["max_prefix"]
        pdb_incr = max_prefix["peering_db"]["increment"]
        limit = int(round(
                    (pdb_value + pdb_incr["absolute"]) * \
                    (1 + float(pdb_incr["relative"]) / 100)
                ))
        max_prefix["limit_ipv{}".format(afi)] = limit

    def save_data(self, task, data):
        _, clients = task
        limit4, limit6 = data
        for client in clients:
            client_max_prefix = client["cfg"]["filtering"]["max_prefix"]
            if limit4 and not client_max_prefix["limit_ipv4"]:
                self._set_client_max_prefix_from_pdb(client, 4, limit4)
            if limit6 and not client_max_prefix["limit_ipv6"]:
                self._set_client_max_prefix_from_pdb(client, 6, limit6)

class PeeringDBConfigEnricher_MaxPrefix(BaseConfigEnricher):

    WORKER_THREAD_CLASS = PeeringDBConfigEnricher_MaxPrefix_WorkerThread

    def _get_general_limit(self, ip_ver):
        return self.builder.cfg_general["filtering"]["max_prefix"]["general_limit_ipv{}".format(ip_ver)]

    def _config_thread(self, thread):
        thread.ip_ver = self.builder.ip_ver
        thread.cfg_general = self.builder.cfg_general
        thread.cache_dir = self.builder.cache_dir
        thread.cache_expiry = self.builder.cache_expiry
        thread.general_limits = {
            "ipv4": self._get_general_limit(4),
            "ipv6": self._get_general_limit(6)
        }

    def add_tasks(self):
        # "<asn>": <clients>
        tasks = {}

        # Enqueuing tasks.
        for client in self.builder.cfg_clients.cfg["clients"]:
            client_max_prefix = client["cfg"]["filtering"]["max_prefix"]

            if not client_max_prefix["action"]:
                # No max-prefix action given for this client:
                # no needs to know its max-pref limit.
                continue

            afis = [4, 6] if self.builder.ip_ver is None else [self.builder.ip_ver]

            pdb_info_needed = False

            for ip_ver in afis:
                if client_max_prefix["limit_ipv{}".format(ip_ver)]:
                    # Client uses a specific limit:
                    # no needs to gather info from PeeringDB for
                    # the current address family.
                    continue

                if not client_max_prefix["peering_db"]["enabled"]:
                    # PeeringDB disabled for this client:
                    # using general limit.
                    client_max_prefix["limit_ipv{}".format(ip_ver)] = \
                        self._get_general_limit(ip_ver)
                    continue

                pdb_info_needed = True

            if pdb_info_needed:
                asn = str(client["asn"])
                if asn not in tasks:
                    tasks[asn] = []
                tasks[asn].append(client)

        for asn in tasks:
            self.tasks_q.put((int(asn), tasks[asn]))

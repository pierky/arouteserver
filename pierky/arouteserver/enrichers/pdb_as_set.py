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

from copy import deepcopy
import logging

from .base import BaseConfigEnricher, BaseConfigEnricherThread
from ..errors import BuilderError, PeeringDBError, PeeringDBNoInfoError
from ..peering_db import PeeringDBNet

class PeeringDBConfigEnricher_ASSet_WorkerThread(BaseConfigEnricherThread):

    DESCR = "PeeringDB AS-SET"

    def __init__(self, *args, **kwargs):
        BaseConfigEnricherThread.__init__(self, *args, **kwargs)

        self.cache_dir = None
        self.cache_expiry = None

    def do_task(self, task):
        asn, _ = task
        try:
            net = PeeringDBNet(asn,
                               cache_dir=self.cache_dir,
                               cache_expiry=self.cache_expiry)
            net.load_data()
        except PeeringDBNoInfoError:
            # No data found on PeeringDB.
            logging.debug("No data found on PeeringDB "
                          "for AS{} while looking for "
                          "AS-SET.".format(asn))
            return None
        except PeeringDBError as e:
            logging.error(
                "An error occurred while retrieving info from PeeringDB "
                "for ASN {}: {}".format(
                    asn, str(e) or "error unknown"
                )
            )
            raise BuilderError()

        return deepcopy(net.irr_as_sets)

    def save_data(self, task, data):
        _, clients = task
        as_sets = data
        if as_sets:
            for client in clients:
                client["as_sets_from_pdb"] = as_sets

class PeeringDBConfigEnricher_ASSet(BaseConfigEnricher):

    WORKER_THREAD_CLASS = PeeringDBConfigEnricher_ASSet_WorkerThread

    def _config_thread(self, thread):
        thread.cache_dir = self.builder.cache_dir
        thread.cache_expiry = self.builder.cache_expiry

    def add_tasks(self):
        # "<asn>": <clients>
        tasks = {}

        # Enqueuing tasks.
        for client in self.builder.cfg_clients.cfg["clients"]:
            client_irrdb = client["cfg"]["filtering"]["irrdb"]

            if not client_irrdb["enforce_origin_in_as_set"] and \
                not client_irrdb["enforce_prefix_in_as_set"] and \
                not self.builder.cfg_general["filtering"]["irrdb"]["tag_as_set"]:
                # Client does not require AS-SETs info to be gathered.
                continue

            if client_irrdb["as_sets"]:
                # Client has its own specific set of AS-SETs.
                continue

            # Client's ASN is configured in the 'asns' section and has
            # one or more AS-SETs.
            asn = "AS{}".format(client["asn"])
            if asn in self.builder.cfg_asns.cfg["asns"] and \
                self.builder.cfg_asns.cfg["asns"][asn]["as_sets"]:
                continue

            asn = str(client["asn"])
            if asn not in tasks:
                tasks[asn] = []
            tasks[asn].append(client)

        for asn in tasks:
            self.tasks_q.put((int(asn), tasks[asn]))

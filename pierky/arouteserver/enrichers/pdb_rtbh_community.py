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

from copy import deepcopy
import logging

from .base import BaseConfigEnricher, BaseConfigEnricherThread
from ..errors import BuilderError, PeeringDBError, PeeringDBNoInfoError
from ..peering_db import PeeringDBNet

class PeeringDBConfigEnricher_RTBHCommunity_WorkerThread(BaseConfigEnricherThread):

    DESCR = "PeeringDB RTBH community"

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
                          "RTBH community.".format(asn))
            return None
        except PeeringDBError as e:
            logging.error(
                "An error occurred while retrieving info from PeeringDB "
                "for ASN {}: {}".format(
                    asn, str(e) or "error unknown"
                )
            )
            raise BuilderError()

        return deepcopy(net.rtbh_community)

    def save_data(self, task, data):
        _, clients = task
        rtbh_community = data
        if rtbh_community:
            for client in clients:
                client_community = \
                    client["cfg"]["blackhole_filtering"]["client_community"]
                client_community["std"] = rtbh_community["std"]
                client_community["lrg"] = rtbh_community["lrg"]

class PeeringDBConfigEnricher_RTBHCommunity(BaseConfigEnricher):

    WORKER_THREAD_CLASS = PeeringDBConfigEnricher_RTBHCommunity_WorkerThread

    def _config_thread(self, thread):
        thread.cache_dir = self.builder.cache_dir
        thread.cache_expiry = self.builder.cache_expiry

    def add_tasks(self):
        # "<asn>": <clients>
        tasks = {}

        # Enqueuing tasks.
        for client in self.builder.cfg_clients.cfg["clients"]:
            client_bh = client["cfg"]["blackhole_filtering"]
            client_community = client_bh["client_community"]

            if not client_bh["announce_to_client"]:
                # Blackhole routes are not announced to this client.
                continue

            if not client_community["peering_db"]:
                # PeeringDB disabled for this client.
                continue

            if client_community["std"] or client_community["lrg"]:
                # Client has its own specific RTBH community.
                continue

            asn = str(client["asn"])
            if asn not in tasks:
                tasks[asn] = []
            tasks[asn].append(client)

        PeeringDBNet.populate_bulk_query_cache(
            list(tasks.keys()),
            cache_dir=self.builder.cache_dir,
            cache_expiry=self.builder.cache_expiry
        )

        for asn in tasks:
            self.tasks_q.put((int(asn), tasks[asn]))

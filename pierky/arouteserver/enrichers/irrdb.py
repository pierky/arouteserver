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

import ipaddr
import logging
import re

from .base import BaseConfigEnricher, BaseConfigEnricherThread
from ..errors import BuilderError, ARouteServerError
from ..irrdb import ASSet, RSet, IRRDBTools


class IRRDBConfigEnricher_WorkerThread(BaseConfigEnricherThread):

    TARGET_FIELD = None

    def __init__(self, *args, **kwargs):
        BaseConfigEnricherThread.__init__(self, *args, **kwargs)

        self.ip_ver = None
        self.irrdbtools_cfg = None

    def do_task(self, task):
        _, dest_descr, as_set_name = task
        data = self._get_external_data(dest_descr, as_set_name)
        return data

    def save_data(self, task, data):
        as_set, _, _ = task
        as_set[self.TARGET_FIELD].extend(
            [_ for _ in data if _ not in as_set[self.TARGET_FIELD]]
        )

class IRRDBConfigEnricher_WorkerThread_Prefixes(IRRDBConfigEnricher_WorkerThread):

    DESCR = "IRRdb prefixes"
    TARGET_FIELD = "prefixes"

    def _get_external_data(self, dest_descr, as_set_name):
        errors = False
        ip_versions = [self.ip_ver] if self.ip_ver else [4, 6]
        res = []
        for ip_ver in ip_versions:
            try:
                prefixes = RSet(as_set_name, ip_ver,
                                **self.irrdbtools_cfg).prefixes
                if not prefixes:
                    logging.warning("No IPv{} prefixes found in "
                                    "{} for {}".format(
                                        ip_ver, as_set_name, dest_descr))
                res.extend(prefixes)
            except ARouteServerError as e:
                errors = True
                logging.error(
                    "Error while retrieving r_set "
                    "{} for {} IPv{}: {}".format(
                        as_set_name, dest_descr, ip_ver, str(e)
                    )
                )

        if errors:
            raise BuilderError()

        return res

class IRRDBConfigEnricher_WorkerThread_OriginASNs(IRRDBConfigEnricher_WorkerThread):

    DESCR = "IRRdb origin ASNs"
    TARGET_FIELD = "asns"

    def _get_external_data(self, dest_descr, as_set_name):
        errors = False
        try:
            asns = ASSet(as_set_name, **self.irrdbtools_cfg).asns
            if not asns:
                logging.warning("No origin ASNs found in "
                                "{} for {}".format(
                                    as_set_name, dest_descr))
            return asns
        except ARouteServerError as e:
            errors = True
            logging.error(
                "Error while retrieving as_set {} for {}: {}".format(
                    as_set_name, dest_descr, str(e)
                )
            )

        if errors:
            raise BuilderError()

class IRRDBConfigEnricher(BaseConfigEnricher):

    WORKER_THREAD_CLASS = None

    def prepare(self):
        if self.builder.as_sets is not None:
            return

        as_sets = []
        errors = False

        def normalize_as_set_id(s):
            return re.sub("[^a-zA-Z0-9_]", "_", s)

        def get_as_set_by_name(name, used_by_client=None):
            for as_set in as_sets:
                if as_set["name"] == name:
                    if used_by_client:
                        as_set["used_by"].append(used_by_client)
                    return as_set
            return None

        def use_as_set(as_set_name, used_by_client=None):
            # Returns: id of the added/existing as_set
            existing = get_as_set_by_name(as_set_name)
            if existing:
                if used_by_client:
                    existing["used_by"].append(used_by_client)
                return existing["id"]

            new_as_set_id = normalize_as_set_id(as_set_name)
            as_sets.append({
                "id": new_as_set_id,
                "name": as_set_name,
                "asns": [],
                "prefixes": [],
                "used_by": [used_by_client] if used_by_client else []
            })
            return new_as_set_id

        # Add to as_sets all the AS-SETs reported in the 'asns' section.
        for asn in self.builder.cfg_asns.cfg["asns"]:
            self.builder.cfg_asns[asn]["as_set_ids"] = []

            if not self.builder.cfg_asns[asn]["as_sets"]:
                continue

            for as_set in self.builder.cfg_asns[asn]["as_sets"]:
                self.builder.cfg_asns[asn]["as_set_ids"].append(
                    use_as_set(as_set)
                )

        # Add to as_sets all the AS-SETs reported in the 'clients' section.
        for client in self.builder.cfg_clients.cfg["clients"]:
            client_irrdb = client["cfg"]["filtering"]["irrdb"]
            client_irrdb["as_set_ids"] = []

            if not client_irrdb["enforce_origin_in_as_set"] and \
                not client_irrdb["enforce_prefix_in_as_set"] and \
                not self.builder.cfg_general["filtering"]["irrdb"]["tag_as_set"]:
                    # Client does not require AS-SETs info to be gathered.
                    continue

            if self.builder.ip_ver is not None:
                ip = client["ip"]
                if ipaddr.IPAddress(ip).version != self.builder.ip_ver:
                    # The address family of this client is not the
                    # current one used to build the configuration.
                    continue

            if client_irrdb["as_sets"]:
                # Client has its own specific set of AS-SETs.
                for as_set in client_irrdb["as_sets"]:
                    client_irrdb["as_set_ids"].append(
                        use_as_set(as_set, "client {}".format(client["id"]))
                    )
                continue

            # Client needs AS-SETs info but has not its own set of AS-SETs.

            # If client's ASN is configured in the 'asns' section and has
            # one or more AS-SETs, the client configuration will be based
            # on those.
            asn = "AS{}".format(client["asn"])
            if asn in self.builder.cfg_asns.cfg["asns"] and \
                self.builder.cfg_asns.cfg["asns"][asn]["as_sets"]:
                for as_set in self.builder.cfg_asns.cfg["asns"][asn]["as_sets"]:
                    client_irrdb["as_set_ids"].append(
                        use_as_set(as_set, "client {}".format(client["id"]))
                    )
                continue

            # No AS-SETs found for the client's ASN in the 'asns' section.
            logging.warning("No AS-SET provided for the '{}' client. "
                            "Only AS{} will be expanded.".format(
                                client["id"], client["asn"]
                            ))

            client_irrdb["as_set_ids"].append(
                use_as_set("AS{}".format(client["asn"]),
                           "client {}".format(client["id"]))
            )

        # Removing unreferenced AS-SETs.
        for as_set in as_sets:
            if not as_set["used_by"]:
                logging.debug("Removing unreferenced AS-SET: "
                              "{}".format(as_set["name"]))
        as_sets = [as_set for as_set in as_sets if as_set["used_by"]]

        self.builder.as_sets = {}
        for as_set in as_sets:
            self.builder.as_sets[as_set["id"]] = as_set

    def _config_thread(self, thread):
        thread.ip_ver = self.builder.ip_ver
        thread.irrdbtools_cfg = {
            "bgpq3_path": self.builder.bgpq3_path,
            "bgpq3_host": self.builder.bgpq3_host,
            "bgpq3_sources": self.builder.bgpq3_sources,
            "cache_dir": self.builder.cache_dir,
            "cache_expiry": self.builder.cache_expiry,
        }

    def add_tasks(self):
        # Enqueuing tasks.
        for as_set_id, as_set in self.builder.as_sets.items():
            used_by = ", ".join(as_set["used_by"])
            self.tasks_q.put((as_set, used_by, as_set["name"]))

class IRRDBConfigEnricher_OriginASNs(IRRDBConfigEnricher):

    WORKER_THREAD_CLASS = IRRDBConfigEnricher_WorkerThread_OriginASNs

class IRRDBConfigEnricher_Prefixes(IRRDBConfigEnricher):

    WORKER_THREAD_CLASS = IRRDBConfigEnricher_WorkerThread_Prefixes

    def _config_thread(self, thread):
        IRRDBConfigEnricher._config_thread(self, thread)
        thread.irrdbtools_cfg["allow_longer_prefixes"] = \
            self.builder.cfg_general["filtering"]["irrdb"]["allow_longer_prefixes"]

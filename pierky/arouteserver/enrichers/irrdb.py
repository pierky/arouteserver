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

import atexit
import logging
import shutil
from six.moves import cPickle
from six import iteritems
import tempfile

from .base import BaseConfigEnricher, BaseConfigEnricherThread
from ..errors import BuilderError, ARouteServerError
from ..ipaddresses import IPAddress
from ..irrdb import ASSet, RSet, AS_SET_Bundle

irrdb_pickle_dir = None
def setup_irrdb_pickle_dir():
    global irrdb_pickle_dir

    if irrdb_pickle_dir:
        return irrdb_pickle_dir

    irrdb_pickle_dir = tempfile.mkdtemp(suffix="_arouteserver")
    atexit.register(clear_irrdb_pickle_dir, target_dir=irrdb_pickle_dir)
    return irrdb_pickle_dir

def clear_irrdb_pickle_dir(target_dir):
    shutil.rmtree(target_dir, ignore_errors=True)

class AS_SET_Bundle_Proxy(AS_SET_Bundle):

    def __init__(self, as_set_names):
        AS_SET_Bundle.__init__(self, as_set_names)

        self.used_by = []

        self.irrdb_pickle_dir = setup_irrdb_pickle_dir()

        self.saved_objects = []

    def get_path(self, objects):
        return "{}/pickle_{}.{}".format(self.irrdb_pickle_dir, self.id, objects)

    def save(self, objects, data):
        if objects in ("asns", "prefixes"):
            with open(self.get_path(objects), "wb") as f:
                cPickle.dump(data, f, cPickle.HIGHEST_PROTOCOL)
            self.saved_objects += [objects]
        else:
            raise ValueError("Unknown objects: {}".format(objects))

    def load(self, objects):
        if objects in self.saved_objects:
            with open(self.get_path(objects), "rb") as f:
                return cPickle.load(f)
        else:
            return []

    @property
    def asns(self):
        return self.load("asns")

    @property
    def prefixes(self):
        return self.load("prefixes")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "descr": self.descr,
            "used_by": ", ".join(sorted(self.used_by)),
            "asns": self.asns,
            "prefixes": self.prefixes
        }

class IRRDBConfigEnricher_WorkerThread(BaseConfigEnricherThread):

    TARGET_FIELD = None

    def __init__(self, *args, **kwargs):
        BaseConfigEnricherThread.__init__(self, *args, **kwargs)

        self.ip_ver = None
        self.irrdbtools_cfg = None

    def do_task(self, task):
        as_set_bundle = task
        used_by_descr = ", ".join(as_set_bundle.used_by)
        data = self._get_external_data(used_by_descr, as_set_bundle.object_names)
        return data

    def save_data(self, task, data):
        as_set_bundle = task
        as_set_bundle.save(self.TARGET_FIELD, data)

class IRRDBConfigEnricher_WorkerThread_Prefixes(IRRDBConfigEnricher_WorkerThread):

    DESCR = "IRRdb prefixes"
    TARGET_FIELD = "prefixes"

    def _get_external_data(self, used_by_descr, as_set_names):
        errors = False
        ip_versions = [self.ip_ver] if self.ip_ver else [4, 6]
        res = []
        for ip_ver in ip_versions:
            obj = RSet(as_set_names, ip_ver, **self.irrdbtools_cfg)
            try:
                obj.load_data()
                prefixes = obj.prefixes
                if not prefixes:
                    logging.warning("No IPv{} prefixes found in "
                                    "{} for {}".format(
                                        ip_ver, obj.descr, used_by_descr))
                res.extend(prefixes)
            except ARouteServerError as e:
                errors = True
                logging.error(
                    "Error while retrieving IPv{} prefixes "
                    "from {} for {}: {}".format(
                        ip_ver, obj.descr, used_by_descr, str(e)
                    )
                )

        if errors:
            raise BuilderError()

        return res

class IRRDBConfigEnricher_WorkerThread_OriginASNs(IRRDBConfigEnricher_WorkerThread):

    DESCR = "IRRdb origin ASNs"
    TARGET_FIELD = "asns"

    def _get_external_data(self, used_by_descr, as_set_name):
        errors = False
        obj = ASSet(as_set_name, **self.irrdbtools_cfg)
        try:
            obj.load_data()
            asns = obj.asns
            if not asns:
                logging.warning("No origin ASNs found in "
                                "{} for {}".format(
                                    obj.descr, used_by_descr))
            return asns
        except ARouteServerError as e:
            errors = True
            logging.error(
                "Error while retrieving origin ASNs from {} for {}: {}".format(
                    obj.descr, used_by_descr, str(e)
                )
            )

        if errors:
            raise BuilderError()

class IRRDBConfigEnricher(BaseConfigEnricher):

    WORKER_THREAD_CLASS = None

    WHITE_LIST_OBJECT_NAME_PREFIX = "WHITE_LIST_"

    def prepare(self):
        if self.builder.irrdb_info is not None:
            return

        # In the end, self.builder.irrdb_info will be a dict
        # with this structure:
        # {
        #   "<as_set_bundle_id>": <AS_SET_Bundle_Proxy>
        # }

        irrdb_info = []

        def use_as_set(as_set_names, used_by_client=None):
            # New bundle for the given AS-SET names.
            # If a bundle for the same AS-SET names is already
            # present in the irrdb_info list, then that one will
            # be returned; otherwise, new_bundle will be.
            #
            # Returns: (<bundle id>, <bundle obj>)
            new_bundle = AS_SET_Bundle_Proxy(as_set_names)

            for as_set_bundle in irrdb_info:
                if as_set_bundle.id == new_bundle.id:
                    # A bundle for the same AS-SET names has been already
                    # added to irrdb_info: use it.
                    if used_by_client:
                        as_set_bundle.used_by.append(used_by_client)
                    return as_set_bundle.id, as_set_bundle

            if used_by_client:
                new_bundle.used_by.append(used_by_client)

            irrdb_info.append(new_bundle)
            return new_bundle.id, new_bundle

        # Add to irrdb_info all the AS-SET bundles reported in the 'asns' section.
        for asn in self.builder.cfg_asns.cfg["asns"]:
            self.builder.cfg_asns[asn]["as_set_bundle_ids"] = set()

            if not self.builder.cfg_asns[asn]["as_sets"]:
                continue

            self.builder.cfg_asns[asn]["as_set_bundle_ids"].add(
                use_as_set(self.builder.cfg_asns[asn]["as_sets"])[0]
            )

        # Add to irrdb_info all the AS-SET bundles reported in the 'clients' section.
        for client in self.builder.cfg_clients.cfg["clients"]:
            client_irrdb = client["cfg"]["filtering"]["irrdb"]
            client_irrdb["as_set_bundle_ids"] = set()

            if not client_irrdb["enforce_origin_in_as_set"] and \
                not client_irrdb["enforce_prefix_in_as_set"] and \
                not self.builder.cfg_general["filtering"]["irrdb"]["tag_as_set"]:
                    # Client does not require AS-SETs info to be gathered.
                    continue

            if self.builder.ip_ver is not None:
                ip = client["ip"]
                if IPAddress(ip).version != self.builder.ip_ver:
                    # The address family of this client is not the
                    # current one used to build the configuration.
                    continue

            # Client needs AS-SETs info because origin ASN or prefix filters
            # are required.

            # In the worst case, use AS<asn>.
            client_irrdb["as_set_bundle_ids"].add(
                use_as_set(["AS{}".format(client["asn"])],
                           "client {}".format(client["id"]))[0]
            )

            # IRR white lists
            for cfg_attr, obj_type in (("white_list_pref", "prefixes"),
                                       ("white_list_asn", "asns")):
                if client_irrdb[cfg_attr]:
                    # If a white list of prefixes/ASNs has been set for the
                    # client, add a fake 'white_list' AS-SET with those
                    # prefixes/ASNs.
                    white_list_name = self.WHITE_LIST_OBJECT_NAME_PREFIX + client["id"]
                    white_list_bundle_id, white_list_bundle = use_as_set(
                        [white_list_name], "client {}".format(client["id"])
                    )
                    white_list_bundle.save(obj_type, client_irrdb[cfg_attr])
                    if white_list_bundle_id not in client_irrdb["as_set_bundle_ids"]:
                        client_irrdb["as_set_bundle_ids"].add(white_list_bundle_id)

            if client_irrdb["as_sets"]:
                # Client has its own specific set of AS-SETs.
                client_irrdb["as_set_bundle_ids"].add(
                    use_as_set(client_irrdb["as_sets"], "client {}".format(client["id"]))[0]
                )
                continue

            # Client needs AS-SETs info but has not its own set of AS-SETs.

            # If client's ASN is configured in the 'asns' section and has
            # one or more AS-SETs, the client configuration will be based
            # on those.
            asn = "AS{}".format(client["asn"])
            if asn in self.builder.cfg_asns.cfg["asns"] and \
                self.builder.cfg_asns.cfg["asns"][asn]["as_sets"]:
                client_irrdb["as_set_bundle_ids"].add(
                    use_as_set(
                        self.builder.cfg_asns.cfg["asns"][asn]["as_sets"],
                        "client {}".format(client["id"])
                    )[0]
                )
                continue

            # If one or more AS-SETs have been found on PeeringDB,
            # use them.
            as_sets_from_pdb = client.get("as_sets_from_pdb", None)
            if as_sets_from_pdb:
                logging.info("No AS-SETs provided for the '{}' client. "
                             "Using AS{} + those obtained from PeeringDB: "
                             "{}.".format(
                                    client["id"], client["asn"],
                                    ", ".join(as_sets_from_pdb)
                                ))
                client_irrdb["as_set_bundle_ids"].add(
                    use_as_set(as_sets_from_pdb, "client {}".format(client["id"]))[0]
                )
                continue

            # No other AS-SETs found for the client.
            logging.warning("No AS-SETs provided for the '{}' client. "
                            "Only AS{} will be expanded.".format(
                                client["id"], client["asn"]
                            ))

        # Removing unreferenced AS-SETs.
        for as_set_bundle in irrdb_info:
            if not as_set_bundle.used_by:
                logging.debug("Removing unreferenced AS-SET: "
                              "{}".format(as_set_bundle.name))
        irrdb_info = [bundle for bundle in irrdb_info if bundle.used_by]

        self.builder.irrdb_info = {}
        for as_set_bundle in irrdb_info:
            self.builder.irrdb_info[as_set_bundle.id] = as_set_bundle

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
        for as_set_bundle_id, as_set_bundle in iteritems(self.builder.irrdb_info):
            if as_set_bundle.name.startswith(self.WHITE_LIST_OBJECT_NAME_PREFIX):
                continue
            self.tasks_q.put(as_set_bundle)

class IRRDBConfigEnricher_OriginASNs(IRRDBConfigEnricher):

    WORKER_THREAD_CLASS = IRRDBConfigEnricher_WorkerThread_OriginASNs

class IRRDBConfigEnricher_Prefixes(IRRDBConfigEnricher):

    WORKER_THREAD_CLASS = IRRDBConfigEnricher_WorkerThread_Prefixes

    def _config_thread(self, thread):
        IRRDBConfigEnricher._config_thread(self, thread)
        thread.irrdbtools_cfg["allow_longer_prefixes"] = \
            self.builder.cfg_general["filtering"]["irrdb"]["allow_longer_prefixes"]

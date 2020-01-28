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

import atexit
import logging
import shutil
from six.moves import cPickle
import six
import tempfile

from .base import BaseConfigEnricher, BaseConfigEnricherThread
from ..errors import BuilderError, ARouteServerError
from ..ipaddresses import IPAddress, IPNetwork
from ..irrdb import ASSet, RSet, AS_SET_Bundle


def clear_irrdb_pickle_dir(target_dir):
    shutil.rmtree(target_dir, ignore_errors=True)

class IRRDB(object):
    """
    Container for IRRDB "records".
    Each record represents a "bundle" of one or more objects and the
    data resulting from their expansion (prefixes and/or ASNs).
    A bundle is made up by one or more aut-num/as-set objects that are
    passed to bgpq3 to retrieve prefixes and/or ASNs; bgpq3's ability
    to aggregate prefixes is used to merge the content of each object
    into a single dataset.
    """

    def __init__(self):
        self.irrdb_pickle_dir = tempfile.mkdtemp(suffix="_arouteserver")
        atexit.register(clear_irrdb_pickle_dir,
                        target_dir=self.irrdb_pickle_dir)

        self.records = {}

    def request(self, names, used_by, object_types=set(["prefixes", "asns"])):
        assert object_types.issubset(set(["prefixes", "asns"]))

        names_list = names if isinstance(names, list) else [names]

        used_source, same_for_all = AS_SET_Bundle.get_source(names_list)
        if not same_for_all:
            logging.info(
                "IRRDB: the source of the bundle '{}' "
                "used by {} is not the same for all the items: "
                "{} will be used for all".format(
                    ", ".join(names_list), used_by,
                    used_source if used_source else "the default sources"
                )
            )

        new_record = IRRDBRecord(names_list, self.irrdb_pickle_dir)

        if new_record.id not in self.records:
            self.records[new_record.id] = new_record
        record = self.records[new_record.id]

        record.used_by.add(used_by)
        record.requested_objects.update(object_types)

        return record.id

    def __getitem__(self, name):
        return self.records[name]

    def __iter__(self):
        return iter(self.records)

    def keys(self):
        return self.records.keys()

    def items(self):
        return self.records.items()

    def iteritems(self):
        return self.records.items()

    def values(self):
        return self.records.values()

class IRRDBRecord(AS_SET_Bundle):

    def __init__(self, as_set_names, irrdb_pickle_dir):
        AS_SET_Bundle.__init__(self, as_set_names)

        self.used_by = set()

        self.requested_objects = set()

        self.irrdb_pickle_dir = irrdb_pickle_dir

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
        irrdb_record = task
        used_by_descr = ", ".join(irrdb_record.used_by)
        data = self._get_external_data(used_by_descr, irrdb_record.object_names)
        return data

    def save_data(self, task, data):
        irrdb_record = task
        irrdb_record.save(self.TARGET_FIELD, data)

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

class IRRDBConfigEnricher_WorkerThread_ASNs(IRRDBConfigEnricher_WorkerThread):

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
        # Create and populate the IRRDB() instances only once
        # (two IRR enrichers are used, but only the first one builds it).
        if self.builder.irrdb_info is not None:
            return

        # In the end, self.builder.irrdb_info will be an IRRDB()
        # object. Its items will be:
        # {
        #   "<as_set_bundle_id>": <IRRDBRecord>
        # }

        self.builder.irrdb_info = IRRDB()

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
                self.builder.irrdb_info.request(
                    "AS{}".format(client["asn"]),
                    "client {}".format(client["id"])
                )
            )

            # IRR white lists
            for cfg_attr, obj_type in (("white_list_pref", "prefixes"),
                                       ("white_list_asn", "asns")):

                white_list_objects = client_irrdb[cfg_attr]

                if not white_list_objects:
                    continue

                if obj_type == "prefixes" and self.builder.ip_ver:
                    # Only consider prefixes for the current IP version.
                    ip_ver = self.builder.ip_ver
                    white_list_objects = [
                        p for p in white_list_objects
                        if IPNetwork(p["prefix"]).version == ip_ver
                    ]

                if white_list_objects:
                    # If a white list of prefixes/ASNs has been set for the
                    # client, add a fake 'white_list' AS-SET with those
                    # prefixes/ASNs.
                    white_list_name = "{prefix}{client_id}".format(
                        prefix=self.WHITE_LIST_OBJECT_NAME_PREFIX,
                        client_id=client["id"]
                    )
                    white_list_record_id = self.builder.irrdb_info.request(
                        white_list_name,
                        "client {} white list".format(client["id"]),
                        set()
                    )
                    self.builder.irrdb_info[white_list_record_id].save(
                        obj_type, client_irrdb[cfg_attr]
                    )
                    if white_list_record_id not in client_irrdb["as_set_bundle_ids"]:
                        client_irrdb["as_set_bundle_ids"].add(white_list_record_id)

            # Client has its own specific set of AS-SETs.
            if client_irrdb["as_sets"]:
                client_irrdb["as_set_bundle_ids"].add(
                    self.builder.irrdb_info.request(
                        client_irrdb["as_sets"],
                        "client {}".format(client["id"])
                    )
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
                    self.builder.irrdb_info.request(
                        self.builder.cfg_asns.cfg["asns"][asn]["as_sets"],
                        "client {}".format(client["id"])
                    )
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
                    self.builder.irrdb_info.request(
                        as_sets_from_pdb,
                        "client {}".format(client["id"])
                    )
                )
                continue

            # No other AS-SETs found for the client.
            logging.warning("No AS-SETs provided for the '{}' client. "
                            "Only AS{} will be expanded.".format(
                                client["id"], client["asn"]
                            ))

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
        target_objects = self.WORKER_THREAD_CLASS.TARGET_FIELD

        # Enqueuing tasks.
        for as_set_record_id, as_set_record in six.iteritems(self.builder.irrdb_info):
            if target_objects in as_set_record.requested_objects:
                self.tasks_q.put(as_set_record)

class IRRDBConfigEnricher_ASNs(IRRDBConfigEnricher):

    WORKER_THREAD_CLASS = IRRDBConfigEnricher_WorkerThread_ASNs

class IRRDBConfigEnricher_Prefixes(IRRDBConfigEnricher):

    WORKER_THREAD_CLASS = IRRDBConfigEnricher_WorkerThread_Prefixes

    def _config_thread(self, thread):
        IRRDBConfigEnricher._config_thread(self, thread)
        thread.irrdbtools_cfg["allow_longer_prefixes"] = \
            self.builder.cfg_general["filtering"]["irrdb"]["allow_longer_prefixes"]

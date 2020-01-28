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

import json
try:
    import mock
except ImportError:
    import unittest.mock as mock
import os

from pierky.arouteserver.arin_db_dump import ARINWhoisDBDump
from pierky.arouteserver.registro_br_db_dump import RegistroBRWhoisDBDump
from pierky.arouteserver.cached_objects import CachedObject
from pierky.arouteserver.config.validators import ValidatorPrefixListEntry
from pierky.arouteserver.enrichers.irrdb import IRRDBConfigEnricher_ASNs, \
                                                IRRDBConfigEnricher_Prefixes
from pierky.arouteserver.enrichers.rtt import RTTGetterConfigEnricher
from pierky.arouteserver.ipaddresses import IPNetwork
from pierky.arouteserver.irrdb import ASSet, RSet
from pierky.arouteserver.peering_db import PeeringDBInfo, PeeringDBNet, \
                                           PeeringDBNetNeverViaRouteServers
from pierky.arouteserver.ripe_rpki_cache import RIPE_RPKI_ROAs


class MockedEnv(object):

    def load(mocked_env, subdir, filename, ret_type=None):
        rel_path = os.path.join(subdir, filename)

        if rel_path in mocked_env.mocked_files:
            return mocked_env.mocked_files[rel_path]

        if mocked_env.base_dir is None:
            raise ValueError("base_dir is missing")

        path = os.path.join(mocked_env.base_dir, subdir, filename)
        with open(path, "r") as f:
            if ret_type == "json":
                return json.load(f)
            return f.read()

    def do_mock_rttgetter(mocked_env):

        def _mock_RTTGetter(self):
            rtts = {}
            for k in mocked_env.base_inst.RTT:
                if k in mocked_env.base_inst.DATA:
                    # it is a prefix ID and not an IP address
                    rtts[mocked_env.base_inst.DATA[k]] = \
                        mocked_env.base_inst.RTT[k]
                else:
                    rtts[k] = mocked_env.base_inst.RTT[k]

            for client in self.builder.cfg_clients.cfg["clients"]:
                if client["ip"] in rtts:
                    client["rtt"] = rtts[client["ip"]]

        mock_RTTGetter = mock.patch.object(
            RTTGetterConfigEnricher, "enrich", autospec=True
        ).start()
        mock_RTTGetter.side_effect = _mock_RTTGetter

    def do_mock_irr(mocked_env):

        def _mock_ASSet_run_cmd(self, cmd):
            asn_list = set()
            for obj_name in self.object_names:
                raw = mocked_env.load("irrdb_data",
                                      "asset_{}.json".format(obj_name),
                                      ret_type="json")
                asn_list.update(raw["asn_list"])
            return json.dumps({"asn_list": list(asn_list)}).encode()

        def _mock_RSet_run_cmd(self, cmd):
            prefix_list = []
            for obj_name in self.object_names:
                raw = mocked_env.load("irrdb_data",
                                      "rset_{}_ipv{}.json".format(obj_name,
                                                                  self.ip_ver),
                                      ret_type="json")
                for prefix in raw["prefix_list"]:
                    if prefix not in prefix_list:
                        prefix_list.append(prefix)
            return json.dumps({"prefix_list": prefix_list}).encode()

        mock_ASSet_run_cmd = mock.patch.object(
            ASSet, "_run_cmd", autospec=True
        ).start()
        mock_ASSet_run_cmd.side_effect = _mock_ASSet_run_cmd

        mock_RSet_run_cmd = mock.patch.object(
            RSet, "_run_cmd", autospec=True
        ).start()
        mock_RSet_run_cmd.side_effect = _mock_RSet_run_cmd

    def do_mock_irrdb(mocked_env):

        def add_prefix_to_list(prefix_name, allow_longer_prefixes, lst):
            obj = IPNetwork(mocked_env.base_inst.DATA[prefix_name])
            lst.append(
                ValidatorPrefixListEntry().validate({
                    "prefix": obj.ip,
                    "length": obj.prefixlen,
                    "comment": prefix_name,
                    "exact": not allow_longer_prefixes
                })
            )

        def _mock_ASSet(self):
            self.prepare()
            for as_set_bundle_id in self.builder.irrdb_info:
                record = self.builder.irrdb_info[as_set_bundle_id]
                asns = []
                for as_set_name in record.object_names:
                    if as_set_name not in mocked_env.base_inst.AS_SET:
                        continue
                    asns.extend(mocked_env.base_inst.AS_SET[as_set_name])
                if asns:
                    record.save("asns", asns)

        def _mock_RSet(self):
            self.prepare()
            allow_longer_prefixes = self.builder.cfg_general["filtering"]["irrdb"]["allow_longer_prefixes"]
            for as_set_bundle_id in self.builder.irrdb_info:
                record = self.builder.irrdb_info[as_set_bundle_id]
                prefixes = []
                for as_set_name in record.object_names:
                    if as_set_name not in mocked_env.base_inst.R_SET:
                        continue
                    for prefix_name in mocked_env.base_inst.R_SET[as_set_name]:
                        add_prefix_to_list(prefix_name, allow_longer_prefixes,
                                           prefixes)
                if prefixes:
                    record.save("prefixes", prefixes)

        mock_ASSet = mock.patch.object(
            IRRDBConfigEnricher_ASNs, "enrich", autospec=True
        ).start()
        mock_ASSet.side_effect = _mock_ASSet

        mock_RSet = mock.patch.object(
            IRRDBConfigEnricher_Prefixes, "enrich", autospec=True
        ).start()
        mock_RSet.side_effect = _mock_RSet

    def do_mock_cached_objects(mocked_env):

        def load_data_from_cache(self):
            return False

        def save_data_to_cache(self):
            return

        mock_load_data_from_cache = mock.patch.object(
            CachedObject, "load_data_from_cache", autospec=True
        ).start()
        mock_load_data_from_cache.side_effect = load_data_from_cache

        mock_save_data_to_cache = mock.patch.object(
            CachedObject, "save_data_to_cache", autospec=True
        ).start()
        mock_save_data_to_cache.side_effect = save_data_to_cache

    def do_mock_peering_db(mocked_env):

        def get_data_from_peeringdb(self):
            return mocked_env.load(
                "peeringdb_data",
                self._get_peeringdb_url(),
                ret_type="json"
            )

        def get_url_net(self):
            return "net_{}.json".format(self.asn)

        def get_url_never_via_route_servers(self):
            return "never_via_route_servers.json"

        mock_get_data_from_peeringdb = mock.patch.object(
            PeeringDBInfo, "_get_data_from_peeringdb", autospec=True
        ).start()
        mock_get_data_from_peeringdb.side_effect = get_data_from_peeringdb

        mock_get_url_net = mock.patch.object(
            PeeringDBNet, "_get_peeringdb_url", autospec=True
        ).start()
        mock_get_url_net.side_effect = get_url_net

        mock_get_url_net = mock.patch.object(
            PeeringDBNetNeverViaRouteServers, "_get_peeringdb_url", autospec=True
        ).start()
        mock_get_url_net.side_effect = get_url_never_via_route_servers

    def do_mock_ripe_rpki_cache(mocked_env):

        def get_data(self):
            return mocked_env.load("ripe-rpki-cache", "ripe-rpki-cache.json",
                                   ret_type="json")

        mock_get_data = mock.patch.object(
            RIPE_RPKI_ROAs, "_get_data", autospec=True
        ).start()
        mock_get_data.side_effect = get_data

    def do_mock_arin_db_dump(mocked_env):

        def get_data(self):
            return mocked_env.load("arin_whois_db", "dump.json",
                                   ret_type="json")

        mock_get_data = mock.patch.object(
            ARINWhoisDBDump, "_get_data", autospec=True
        ).start()
        mock_get_data.side_effect = get_data

    def do_mock_registrobr_db_dump(mocked_env):

        def get_data(self):
            return mocked_env.load("registrobr_whois_db", "dump.txt")

        mock_get_data = mock.patch.object(
            RegistroBRWhoisDBDump, "_get_data", autospec=True
        ).start()
        mock_get_data.side_effect = get_data

    def __init__(mocked_env, base_inst=None, base_dir=None, default=True,
                 **kwargs):
        """
        - bypass_cache:

          Mock CachedObject.load_data_from_cache() and .save_data_to_cache()
          methods to bypass cache.
          This is automatically set to True when other "cache users"
          functions are mocked.

        - peering_db:

          Mock the PeeringDBInfo._get_data_from_peeringdb() and
          PeeringDBNet._get_peeringdb_url() methods.

          It reads data from the <base_dir>/peeringdb_data/net_<ASN>.json

          Implies bypass_cache.

        - ripe_rpki_cache:

          Mock the RIPE_RPKI_ROAs._get_data() method.

          The content of the RIPE RPKI cache is read from the
          <base_dir>/ripe-rpki-cache/ripe-rpki-cache.json local path.

          Implies bypass_cache.

        - irr:

          Mock ASSet and RSet _run_cmd() methods.

          Raw data as returned by bgpq3 are read from the local files
          <base_dir>/irrdb_data/asset_<name>.json and
          <base_dir>/irrdb_data/rset_<name>_ipv[4|6].json
          Sets of unique ASNs and prefixes are built and returned in the
          bgpq3 format.

          Implies bypass_cache.

        - irrdb:

          Mock IRRDBConfigEnricher_ASNs and IRRDBConfigEnricher_Prefixes
          enrich() method.

          It uses base_inst.DATA, base_inst.AS_SET and base_inst.R_SET to
          read ASNs and prefixes and to save them into IRRDB records:
          record.save("asns") / record.save("prefixes").

          Implies bypass_cache.

        - rttgetter:

          Mock the RTTGetterConfigEnricher.enrich() method.

          It uses base_inst.DATA and base_inst.RTT to fill clients' rtt
          attribute.

        - arin_db_dump:

          Mock the ARINWhoisDBDump._get_data() method.

          The content of the ARIN DB dump is read from the local
          <base_dir>/arin_whois_db/dump.json file.

        - registrobr_db_dump:

          Mock the RegistroBRWhoisDBDump._get_data() method.

          The content of the Registro.br DB dump is read from the local
          <base_dir>/registrobr_whois_db/dump.json file.
        """
        mocked_env.base_inst = base_inst

        mocked_env.bypass_cache = kwargs.get("bypass_cache", default)

        mocked_env.peering_db = kwargs.get("peering_db", default)

        mocked_env.ripe_rpki_cache = kwargs.get("ripe_rpki_cache", default)

        mocked_env.irr = kwargs.get("irr", default)

        mocked_env.irrdb = kwargs.get("irrdb",
                                      default and base_inst is not None)

        if mocked_env.irrdb:
            assert base_inst is not None, \
                "when irrdb is True, base_inst is needed"

        mocked_env.rttgetter = kwargs.get("rttgetter",
                                          default and base_inst is not None)

        if mocked_env.rttgetter:
            assert base_inst is not None, \
                "when rttgetter is True, base_inst is needed"

        mocked_env.arin_db_dump = kwargs.get("arin_db_dump", default)

        mocked_env.registrobr_db_dump = kwargs.get("registrobr_db_dump", default)

        mocked_env.base_dir = base_dir

        # Setup mocks

        if mocked_env.peering_db or mocked_env.ripe_rpki_cache or \
            mocked_env.irr or mocked_env.irrdb or mocked_env.arin_db_dump or \
            mocked_env.registrobr_db_dump:
            mocked_env.bypass_cache = True

        if mocked_env.bypass_cache:
            mocked_env.do_mock_cached_objects()

        if mocked_env.peering_db:
            mocked_env.do_mock_peering_db()

        if mocked_env.ripe_rpki_cache:
            mocked_env.do_mock_ripe_rpki_cache()

        if mocked_env.irr:
            mocked_env.do_mock_irr()

        if mocked_env.irrdb:
            mocked_env.do_mock_irrdb()

        if mocked_env.rttgetter:
            mocked_env.do_mock_rttgetter()

        if mocked_env.arin_db_dump:
            mocked_env.do_mock_arin_db_dump()

        if mocked_env.registrobr_db_dump:
            mocked_env.do_mock_registrobr_db_dump()

        mocked_env.mocked_files = {}

    @staticmethod
    def stopall():
        mock.patch.stopall()

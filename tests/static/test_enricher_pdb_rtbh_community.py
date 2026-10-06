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

import os
import shutil
import tempfile
import unittest

from pierky.arouteserver.cached_objects import normalize_expiry_time
from pierky.arouteserver.config.clients import ConfigParserClients
from pierky.arouteserver.config.general import ConfigParserGeneral
from pierky.arouteserver.enrichers.pdb_rtbh_community import \
    PeeringDBConfigEnricher_RTBHCommunity
from pierky.arouteserver.tests.mocked_env import MockedEnv


class FakeBuilder(object):

    def __init__(self, cfg_clients, cache_dir):
        self.cfg_clients = cfg_clients
        self.cache_dir = cache_dir
        self.cache_expiry = normalize_expiry_time()


class TestPeeringDBRTBHCommunityEnricher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        MockedEnv(default=False, peering_db=True,
                  base_dir=os.path.dirname(__file__))

    @classmethod
    def tearDownClass(cls):
        MockedEnv.stopall()

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _enrich(self, clients_config):
        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  blackhole_filtering:",
            "    policy_ipv4: propagate-unchanged",
            "    client_community:",
            "      peering_db: True",
        ]))
        general.parse()

        clients = ConfigParserClients(general_cfg=general)
        clients._load_from_yaml("\n".join(["clients:"] + clients_config))
        clients.parse()

        enricher = PeeringDBConfigEnricher_RTBHCommunity(
            FakeBuilder(clients, self.temp_dir), threads=2
        )
        enricher.enrich()

        return {
            client["ip"]: client["cfg"]["blackhole_filtering"]["client_community"]
            for client in clients.cfg["clients"]
        }

    def test_enricher(self):
        """PeeringDB RTBH community enricher"""
        res = self._enrich([
            # rtbh_community not set on PeeringDB
            "  - asn: 1",
            "    ip: 192.0.2.11",
            # No data on PeeringDB
            "  - asn: 2",
            "    ip: 192.0.2.21",
            # Standard community on PeeringDB
            "  - asn: 4",
            "    ip: 192.0.2.41",
            # Large community on PeeringDB
            "  - asn: 5",
            "    ip: 192.0.2.51",
            # Same ASN, but not enabled to receive blackhole routes
            "  - asn: 5",
            "    ip: 192.0.2.52",
            "    cfg:",
            "      blackhole_filtering:",
            "        announce_to_client: False",
            # Same ASN, PeeringDB disabled
            "  - asn: 5",
            "    ip: 192.0.2.53",
            "    cfg:",
            "      blackhole_filtering:",
            "        client_community:",
            "          peering_db: False",
            # Same ASN, community configured in clients.yml
            "  - asn: 5",
            "    ip: 192.0.2.54",
            "    cfg:",
            "      blackhole_filtering:",
            "        client_community:",
            "          std: '5:999'",
            # Invalid value on PeeringDB (list)
            "  - asn: 6",
            "    ip: 192.0.2.61",
        ])

        def comms(ip):
            return res[ip]["std"], res[ip]["lrg"]

        self.assertEqual(comms("192.0.2.11"), (None, None))
        self.assertEqual(comms("192.0.2.21"), (None, None))
        self.assertEqual(comms("192.0.2.41"), ("65000:666", None))
        self.assertEqual(comms("192.0.2.51"), (None, "5:666:0"))
        self.assertEqual(comms("192.0.2.52"), (None, None))
        self.assertEqual(comms("192.0.2.53"), (None, None))
        self.assertEqual(comms("192.0.2.54"), ("5:999", None))
        self.assertEqual(comms("192.0.2.61"), (None, None))

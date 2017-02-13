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

import unittest

import yaml

from .cfg_base import TestConfigParserBase 
from pierky.arouteserver.config.clients import ConfigParserClients
from pierky.arouteserver.config.general import ConfigParserGeneral


class TestConfigParserClients(TestConfigParserBase):

    FILE_PATH = "config.d/clients.yml"
    CONFIG_PARSER_CLASS = ConfigParserClients
    SHORT_DESCR = "Clients config parser"

    def test_valid_cfg(self):
        """{}: valid configuration"""
        self._contains_err()

    def test_unknown_statement(self):
        """{}: unknown statement"""
        self.cfg[0]["test"] = "test"
        self._contains_err("Unknown statement at 'clients' level: 'test'.")

    def test_as(self):
        """{}: AS number"""
        for v in (-1, 0, "test"):
            self.cfg[0]["asn"] = v
            self._contains_err("Error parsing 'asn' at 'clients' level - Invalid ASN: {}.".format(v))

    def test_ip(self):
        """{}: IP address"""
        for v in ("192.0.2.1/24", "2001:db8::1/64"):
            self.cfg[0]["ip"] = v
            self._contains_err("Error parsing 'ip' at 'clients' level - Invalid IP address: {}.".format(v))
        for v in ("192.0.2.1", "10.0.1.1", "1.2.3.4", "fe80::1", "2001:DB8::1"):
            self.cfg[0]["ip"] = v
            self._contains_err()

    def test_duplicate_ip(self):
        """{}: duplicate IP addresses"""
        self.cfg[0]["ip"] = "192.0.2.1"
        self.cfg[1]["ip"] = self.cfg[0]["ip"]
        self._contains_err("Duplicate IP address found: 192.0.2.1.")

    def test_multiple_ip_addresses(self):
        """{}: clients with multiple IP addresses"""
        clients_config = [
            "clients:",
            "  - asn: 111",
            "    ip:",
            "      - '192.0.2.11'",
            "      - '2001:db8:1:1::11'",
            "  - asn: 222",
            "    ip:",
            "      - '192.0.2.21'",
            "      - '2001:db8:1:1::21'",
        ]

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(clients_config))
        self._contains_err()

        # Duplicate address.
        clients_config = [
            "clients:",
            "  - asn: 111",
            "    ip:",
            "      - '192.0.2.11'",
            "      - '2001:db8:1:1::11'",
            "  - asn: 222",
            "    ip:",
            "      - '192.0.2.11'",
            "      - '2001:db8:1:1::21'",
        ]

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(clients_config))
        self._contains_err("Duplicate IP address found: 192.0.2.11")

    def test_inherit_from_general_cfg(self):
        """{}: inherit from general cfg"""
        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2"
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join([
            "clients:",
            "  - asn: 111",
            "    ip: 192.0.2.11",
            "  - asn: 222",
            "    ip: 192.0.2.21",
            "    cfg:",
            "      passive: False",
            "      prepend_rs_as: True",
            "      add_path: True",
            "      filtering:",
            "        irrdb:",
            "          enforce_origin_in_as_set: False",
            "          enforce_prefix_in_as_set: False",
            "        rpki:",
            "          enabled: True",
            "        reject_invalid_as_in_as_path: False",
            "        max_as_path_len: 64",
            "        ipv4_pref_len:",
            "          min: 1",
            "          max: 2",
            "        ipv6_pref_len:",
            "          min: 3",
            "          max: 4",
            "        next_hop_policy: same-as",
            "        max_prefix:",
            "          peering_db: False",
            "          limit_ipv4: 10",
            "          limit_ipv6: 20"
        ]))
        self.cfg.parse()
        self._contains_err()

        client = self.cfg[0]
        self.assertEqual(client["cfg"]["passive"], True)
        self.assertEqual(client["cfg"]["add_path"], False)
        self.assertEqual(client["cfg"]["prepend_rs_as"], False)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["enforce_origin_in_as_set"], True)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["enforce_prefix_in_as_set"], True)
        self.assertEqual(client["cfg"]["filtering"]["rpki"]["enabled"], False)
        self.assertEqual(client["cfg"]["filtering"]["reject_invalid_as_in_as_path"], True)
        self.assertEqual(client["cfg"]["filtering"]["max_as_path_len"], 32)
        self.assertEqual(client["cfg"]["filtering"]["ipv4_pref_len"]["min"], 8)
        self.assertEqual(client["cfg"]["filtering"]["ipv4_pref_len"]["max"], 24)
        self.assertEqual(client["cfg"]["filtering"]["ipv6_pref_len"]["min"], 12)
        self.assertEqual(client["cfg"]["filtering"]["ipv6_pref_len"]["max"], 48)
        self.assertEqual(client["cfg"]["filtering"]["next_hop_policy"], "strict")
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["limit_ipv4"], None)
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["limit_ipv6"], None)
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["peering_db"], True)

        client = self.cfg[1]
        self.assertEqual(client["cfg"]["passive"], False)
        self.assertEqual(client["cfg"]["add_path"], True)
        self.assertEqual(client["cfg"]["prepend_rs_as"], True)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["enforce_origin_in_as_set"], False)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["enforce_prefix_in_as_set"], False)
        self.assertEqual(client["cfg"]["filtering"]["rpki"]["enabled"], True)
        self.assertEqual(client["cfg"]["filtering"]["reject_invalid_as_in_as_path"], False)
        self.assertEqual(client["cfg"]["filtering"]["max_as_path_len"], 64)
        self.assertEqual(client["cfg"]["filtering"]["ipv4_pref_len"]["min"], 1)
        self.assertEqual(client["cfg"]["filtering"]["ipv4_pref_len"]["max"], 2)
        self.assertEqual(client["cfg"]["filtering"]["ipv6_pref_len"]["min"], 3)
        self.assertEqual(client["cfg"]["filtering"]["ipv6_pref_len"]["max"], 4)
        self.assertEqual(client["cfg"]["filtering"]["next_hop_policy"], "same-as")
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["limit_ipv4"], 10)
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["limit_ipv6"], 20)
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["peering_db"], False)

    def test_blackhole_filtering_propagation(self):
        """{}: inherit from general cfg - blackhole filtering"""
        clients_config = [
            "clients:",
            "  - asn: 111",
            "    ip: 192.0.2.11",
            "    cfg:",
            "      blackhole_filtering:",             
            "  - asn: 222",
            "    ip: 192.0.2.21",
            "    cfg:",
            "      blackhole_filtering:",
            "        announce_to_client: True",
            "  - asn: 333",
            "    ip: 192.0.2.31",
            "    cfg:",
            "      blackhole_filtering:",
            "        announce_to_client: False",
        ]

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(clients_config))
        self.cfg.parse()
        self._contains_err()

        self.assertIs(general["blackhole_filtering"]["announce_to_client"], True)

        client = self.cfg[0]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], True)
        client = self.cfg[1]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], True)
        client = self.cfg[2]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], False)

        # ------------------------

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  blackhole_filtering:",
            "    announce_to_client: False"  
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(clients_config))
        self.cfg.parse()
        self._contains_err()

        self.assertTrue(general["blackhole_filtering"]["announce_to_client"] is False)

        client = self.cfg[0]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], False)
        client = self.cfg[1]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], True)
        client = self.cfg[2]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], False)

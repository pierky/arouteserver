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

import json
import os
import shutil
import tempfile
try:
    import mock
except ImportError:
    import unittest.mock as mock
import yaml

from pierky.arouteserver.builder import BIRDConfigBuilder, \
                                        OpenBGPDConfigBuilder
from pierky.arouteserver.errors import BuilderError, CompatibilityIssuesError
from pierky.arouteserver.ripe_rpki_cache import RIPE_RPKI_ROAs
from pierky.arouteserver.tests.base import ARouteServerTestCase
from pierky.arouteserver.tests.mocked_env import MockedEnv


class TestASPABuilder(ARouteServerTestCase):

    NEED_TO_CAPTURE_LOG = True

    SHORT_DESCR = "ASPA builder"

    ROAS_AND_ASPAS = {
        "roas": [
            {"asn": "AS101", "prefix": "192.0.2.0/24", "maxLength": 24,
             "ta": "test"}
        ],
        "aspas": [
            {"customer": "AS101", "providers": ["AS1", "AS2"], "ta": "test"},
            {"customer": "AS102", "providers": ["AS3"], "ta": "not-allowed"},
            {"customer": "AS103", "providers": ["AS4"]}
        ]
    }

    CLIENTS = {
        "clients": [
            {"asn": 1, "ip": "192.0.2.11"}
        ]
    }

    def _setUp(self):
        MockedEnv(base_dir=os.path.dirname(__file__), default=True,
                  ripe_rpki_cache=False)
        self.temp_dir = tempfile.mkdtemp(suffix="arouteserver_unittest")

        self.rpki_file_path = os.path.join(self.temp_dir, "rpki.json")
        with open(self.rpki_file_path, "w") as f:
            json.dump(self.ROAS_AND_ASPAS, f)

    def tearDown(self):
        MockedEnv.stopall()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write(self, name, dic):
        path = os.path.join(self.temp_dir, name)
        with open(path, "w") as f:
            yaml.dump(dic, f, default_flow_style=False)
        return path

    def _general(self, aspa_source="rtr", roles=True, aspa_urls=None,
                 roa_urls=None):
        cfg = {
            "cfg": {
                "rs_as": 999,
                "router_id": "192.0.2.2",
                "filtering": {
                    "irrdb": {
                        "enforce_origin_in_as_set": False,
                        "enforce_prefix_in_as_set": False,
                        "tag_as_set": False
                    },
                    "never_via_route_servers": {
                        "peering_db": False
                    },
                    "rpki_aspa_verification": {
                        "enabled": True,
                        "reject_invalid": True
                    },
                    "roles": {
                        "enabled": roles
                    }
                },
                "rpki_aspas": {
                    "source": aspa_source,
                    "allowed_trust_anchors": ["test"]
                }
            }
        }
        if aspa_urls is not None:
            cfg["cfg"]["rpki_aspas"]["json_url"] = aspa_urls
        if roa_urls is not None:
            cfg["cfg"]["filtering"]["rpki_bgp_origin_validation"] = {
                "enabled": True
            }
            cfg["cfg"]["rpki_roas"] = {
                "source": "ripe-rpki-validator-cache",
                "ripe_rpki_validator_url": roa_urls,
                "allowed_trust_anchors": ["test"]
            }
        return cfg

    def _build(self, builder_class, tpl_dir, target_version, general,
               ignore_errors=[]):
        return builder_class(
            template_dir="templates/{}".format(tpl_dir),
            template_name="main.j2",
            cfg_general=self._write("general.yml", general),
            cfg_clients=self._write("clients.yml", self.CLIENTS),
            cfg_bogons="config.d/bogons.yml",
            cache_dir=self.temp_dir,
            cache_expiry=120,
            target_version=target_version,
            ignore_errors=ignore_errors,
            ip_ver=4 if tpl_dir == "bird" else None
        )

    # ---------------------------------------------------------------
    # OpenBGPD: RFC9234 roles are a hard requirement
    # ---------------------------------------------------------------

    def test_010_openbgpd_aspa_without_roles(self):
        """{}: OpenBGPD, ASPA without roles raises an error"""

        with self.assertRaisesRegex(
            BuilderError, "RFC9234 roles .* are not"
        ):
            self._build(OpenBGPDConfigBuilder, "openbgpd", "9.2",
                        self._general(roles=False),
                        ignore_errors=["*"])

    def test_011_openbgpd_aspa_with_roles(self):
        """{}: OpenBGPD, ASPA with roles is fine"""

        builder = self._build(OpenBGPDConfigBuilder, "openbgpd", "9.2",
                              self._general(roles=True))
        self.assertIn("avs invalid", builder.render_template())

    def test_012_openbgpd_aspa_without_roles_on_old_target(self):
        """{}: OpenBGPD, ASPA without roles on a target with no ASPA support"""

        # The target doesn't support ASPA at all, so the roles
        # requirement doesn't apply: only the compatibility issue is
        # raised, and it can be ignored.
        builder = self._build(OpenBGPDConfigBuilder, "openbgpd", "7.7",
                              self._general(roles=False),
                              ignore_errors=["aspa_not_available"])
        self.assertNotIn("avs invalid", builder.render_template())

    def test_013_bird_aspa_without_roles(self):
        """{}: BIRD, ASPA without roles is fine"""

        # On BIRD the ASPA check does not depend on the role of the
        # session, so roles are not needed.
        builder = self._build(BIRDConfigBuilder, "bird", "3.3.2",
                              self._general(roles=False))
        self.assertIn("aspa_check_upstream(ASPA)", builder.render_template())

    # ---------------------------------------------------------------
    # Target release support
    # ---------------------------------------------------------------

    def test_020_bird_unsupported_targets(self):
        """{}: BIRD, ASPA on targets that don't support it"""

        # BIRD 3.0 is the alpha release, that predates the ASPA
        # implementation even though its version number is greater
        # than 2.16.
        # RFC9234 roles are not available on these targets either, so
        # they are disabled here to keep the ASPA issue isolated.
        for target_version in ("1.6.8", "2.15", "3.0"):
            with self.assertRaisesRegex(
                CompatibilityIssuesError, "compatibility issues"
            ):
                self._build(BIRDConfigBuilder, "bird", target_version,
                            self._general(roles=False))

            builder = self._build(BIRDConfigBuilder, "bird", target_version,
                                  self._general(roles=False),
                                  ignore_errors=["aspa_not_available"])
            res = builder.render_template()
            self.assertNotIn("aspa table ASPA", res)
            self.assertNotIn("aspa_check_upstream", res)

    def test_021_bird_supported_targets(self):
        """{}: BIRD, ASPA on targets that support it"""

        for target_version in ("2.16", "2.19.2", "3.2.3", "3.3.2"):
            builder = self._build(BIRDConfigBuilder, "bird", target_version,
                                  self._general())
            res = builder.render_template()
            self.assertIn("aspa table ASPA", res)
            self.assertIn("aspa_check_upstream(ASPA)", res)

    def test_022_openbgpd_unsupported_targets(self):
        """{}: OpenBGPD, ASPA on targets that don't support it"""

        for target_version in ("7.0", "7.7"):
            with self.assertRaisesRegex(
                CompatibilityIssuesError, "compatibility issues"
            ):
                self._build(OpenBGPDConfigBuilder, "openbgpd", target_version,
                            self._general())

    def test_023_openbgpd_supported_targets(self):
        """{}: OpenBGPD, ASPA on targets that support it"""

        for target_version in ("7.8", "8.4", "8.7", "9.2"):
            builder = self._build(OpenBGPDConfigBuilder, "openbgpd",
                                  target_version, self._general())
            self.assertIn("avs invalid", builder.render_template())

    # ---------------------------------------------------------------
    # ASPAs from a JSON file, and the single-fetch optimization
    # ---------------------------------------------------------------

    def test_030_aspas_from_json(self):
        """{}: ASPAs gathered from a JSON file"""

        builder = self._build(
            BIRDConfigBuilder, "bird", "3.3.2",
            self._general(aspa_source="json",
                          aspa_urls=[self.rpki_file_path]))

        # AS102's ASPA comes from a TA that is not allowed;
        # AS103's one has no TA at all, so it's used.
        self.assertEqual(builder.rpki_aspas, [
            {"customer_asn": 101, "providers": [1, 2]},
            {"customer_asn": 103, "providers": [4]}
        ])

        res = builder.render_template()
        self.assertIn("route aspa 101 providers 1, 2;", res)
        self.assertIn("route aspa 103 providers 4;", res)
        self.assertNotIn("route aspa 102", res)

    def test_031_no_aspa_available(self):
        """{}: no ASPA available"""

        empty_path = os.path.join(self.temp_dir, "empty.json")
        with open(empty_path, "w") as f:
            json.dump({"roas": [], "aspas": []}, f)

        # BIRD accepts an empty 'protocol static' block...
        builder = self._build(
            BIRDConfigBuilder, "bird", "3.3.2",
            self._general(aspa_source="json", aspa_urls=[empty_path]))
        res = builder.render_template()
        self.assertIn("aspa table ASPA", res)
        self.assertNotIn("route aspa ", res)

        # ...but OpenBGPD rejects an empty 'aspa-set', so the
        # statement must not be emitted at all.
        builder = self._build(
            OpenBGPDConfigBuilder, "openbgpd", "9.2",
            self._general(aspa_source="json", aspa_urls=[empty_path]))
        res = builder.render_template()
        self.assertNotIn("aspa-set", res)
        self.assertIn("avs invalid", res)

    def test_032_aspa_with_no_providers(self):
        """{}: ASPA with no providers"""

        path = os.path.join(self.temp_dir, "noprov.json")
        with open(path, "w") as f:
            json.dump({
                "roas": [],
                "aspas": [
                    {"customer": "AS101", "providers": [], "ta": "test"}
                ]
            }, f)

        # BIRD has an explicit syntax for a customer with no providers.
        builder = self._build(
            BIRDConfigBuilder, "bird", "3.3.2",
            self._general(aspa_source="json", aspa_urls=[path]))
        self.assertIn("route aspa 101 transit;", builder.render_template())

        # OpenBGPD does not accept an empty 'provider-as { }', so the
        # record is skipped; and since it was the only one, the whole
        # 'aspa-set' is not emitted either.
        builder = self._build(
            OpenBGPDConfigBuilder, "openbgpd", "9.2",
            self._general(aspa_source="json", aspa_urls=[path]))
        res = builder.render_template()
        self.assertNotIn("aspa-set", res)
        self.assertNotIn("customer-as", res)

    def test_040_same_url_fetched_once(self):
        """{}: ROAs and ASPAs from the same URL are fetched once"""

        with mock.patch.object(
            RIPE_RPKI_ROAs, "_get_data_from_url", autospec=True,
            side_effect=RIPE_RPKI_ROAs._get_data_from_url
        ) as mock_get:
            builder = self._build(
                BIRDConfigBuilder, "bird", "3.3.2",
                self._general(aspa_source="json",
                              aspa_urls=[self.rpki_file_path],
                              roa_urls=[self.rpki_file_path]))

        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(len(builder.rpki_aspas), 2)
        self.assertEqual(len(builder.rpki_roas), 1)

    def test_041_different_urls_fetched_twice(self):
        """{}: ROAs and ASPAs from different URLs are fetched twice"""

        other_file_path = os.path.join(self.temp_dir, "rpki2.json")
        shutil.copy(self.rpki_file_path, other_file_path)

        with mock.patch.object(
            RIPE_RPKI_ROAs, "_get_data_from_url", autospec=True,
            side_effect=RIPE_RPKI_ROAs._get_data_from_url
        ) as mock_get:
            builder = self._build(
                BIRDConfigBuilder, "bird", "3.3.2",
                self._general(aspa_source="json",
                              aspa_urls=[other_file_path],
                              roa_urls=[self.rpki_file_path]))

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(builder.rpki_aspas), 2)
        self.assertEqual(len(builder.rpki_roas), 1)

# Copyright (C) 2017-2021 Pier Carlo Chiodi
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
import logging
import datetime

import requests

from .cached_objects import CachedObject
from .errors import RPKIValidatorCacheError
from .ipaddresses import IPNetwork


class RIPE_RPKI_ROAs(CachedObject):

    EXPIRY_TIME_TAG = "ripe_rpki_roas"

    DEFAULT_URL = "https://console.rpki-client.org/vrps.json"
    DEFAULT_IGNORE_FILES_OLDER_THAN = 21600

    def __init__(self, *args, **kwargs):
        CachedObject.__init__(self, *args, **kwargs)

        self.urls = kwargs.get("ripe_rpki_validator_url",
                               [self.DEFAULT_URL])

        self.ignore_cache_files_older_than = kwargs.get(
            "ignore_cache_files_older_than",
            self.DEFAULT_IGNORE_FILES_OLDER_THAN
        )

        self.roas = {}

    def load_data(self):
        logging.debug("Loading RPKI ROAs...")

        CachedObject.load_data(self)

        self.roas = self.raw_data

    def _get_object_filename(self):
        return "ripe-rpki-cache.json"

    @staticmethod
    def _get_utc_now():
        return datetime.datetime.utcnow()

    def _get_data_from_url(self, url):
        if url.lower().startswith(("http://", "https://")):
            logging.debug("Fetching RPKI ROAs from {}".format(url))
            try:
                response = requests.get(url,
                                        headers={'Accept': 'text/json'})
                response.raise_for_status()
                raw = response.content
            except requests.exceptions.HTTPError as e:
                raise RPKIValidatorCacheError(
                    "HTTP error while retrieving ROAs from "
                    "RIPE RPKI Validator cache ({}): "
                    "{}".format(
                        url, str(e)
                    )
                )
            except Exception as e:
                raise RPKIValidatorCacheError(
                    "Error while retrieving ROAs from "
                    "RIPE RPKI Validator cache ({}): {}".format(
                        url, str(e)
                    )
                )
        else:
            logging.debug("Loading RPKI ROAs from {} file".format(url))
            try:
                raw = open(url, "rb").read()
            except Exception as e:
                raise RPKIValidatorCacheError(
                    "Error while reading ROAs from file "
                    "{}: {}".format(
                        url, str(e)
                    )
                )

        try:
            roas = json.loads(raw.decode("utf-8"))
        except Exception as e:
            raise RPKIValidatorCacheError(
                "Error while parsing ROAs from "
                "RIPE RPKI Validator cache ({}): {}".format(
                    url, str(e)
                )
            )

        if "roas" not in roas:
            raise RPKIValidatorCacheError("missing 'roas' root element")
        if not isinstance(roas["roas"], list):
            raise RPKIValidatorCacheError("'roas' root element is not a list")

        buildtime_dt_utc = None

        if "metadata" in roas and "buildtime" in roas["metadata"]:
            # rpki-client format.

            buildtime = roas["metadata"]["buildtime"]

            try:
                buildtime_dt_utc = datetime.datetime.strptime(
                    buildtime,
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            except Exception as e:
                raise RPKIValidatorCacheError(
                    "Error while parsing metadata.buildtime from "
                    "RPKI cache file ({}): {}".format(
                        url, str(e)
                    )
                )

        elif "metadata" in roas and "generated" in roas["metadata"]:
            # OctoRPKI format.

            generated = roas["metadata"]["generated"]

            try:
                buildtime_dt_utc = datetime.datetime.utcfromtimestamp(int(generated))
            except Exception as e:
                raise RPKIValidatorCacheError(
                    "Error while parsing metadata.generated from "
                    "RPKI cache file ({}): {}".format(
                        url, str(e)
                    )
                )

        if buildtime_dt_utc and buildtime_dt_utc < self._get_utc_now() - datetime.timedelta(
            seconds=self.ignore_cache_files_older_than
        ):
            raise RPKIValidatorCacheError(
                "The RPKI cache file from {} was built at {} UTC, "
                "so it was generated more than {} seconds ago "
                "(ignore_cache_files_older_than), hence "
                "it will be ignored.".format(
                    url,
                    buildtime_dt_utc,
                    self.ignore_cache_files_older_than
                )
            )

        valid_dt_utc = None

        if "metadata" in roas and "valid" in roas["metadata"]:
            # OctoRPKI format.

            valid = roas["metadata"]["valid"]

            try:
                valid_dt_utc = datetime.datetime.utcfromtimestamp(int(valid))
            except Exception as e:
                raise RPKIValidatorCacheError(
                    "Error while parsing metadata.valid from "
                    "RPKI cache file ({}): {}".format(
                        url, str(e)
                    )
                )

        if valid_dt_utc and valid_dt_utc < self._get_utc_now():
            raise RPKIValidatorCacheError(
                "The RPKI cache file from {} is valid till {} UTC, "
                "hence it will be ignored.".format(
                    url,
                    valid_dt_utc
                )
            )

        max_invalid_roas = 10
        invalid = 0
        timestamp_now_utc = int(datetime.datetime.timestamp(self._get_utc_now()))

        result = {"roas": []}
        for roa in roas["roas"]:
            try:
                if "expires" in roa:
                    expires = roa["expires"]
                    if not isinstance(expires, int):
                        if not expires.isdigit():
                            raise ValueError("invalid expires")
                        else:
                            expires = int(expires)
                    if expires < timestamp_now_utc:
                        continue

                asn = roa.get("asn", None)
                if asn is None:
                    raise ValueError("missing ASN")
                if isinstance(asn, int):
                    roa["asn"] = "AS{}".format(asn)
                elif asn.isdigit():
                    roa["asn"] = "AS{}".format(asn)
                else:
                    if not asn.startswith("AS"):
                        raise ValueError("invalid ASN: " + asn)
                    if not asn[2:].isdigit():
                        raise ValueError("invalid ASN: " + asn)

                if "ta" not in roa:
                    raise ValueError("missing trust anchor")

                prefix = roa.get("prefix", None)
                if not prefix:
                    raise ValueError("missing prefix")
                try:
                    IPNetwork(prefix)
                except:
                    raise ValueError("invalid prefix: " + prefix)

                max_len = roa.get("maxLength", None)
                if max_len is None:
                    raise ValueError("missing maxLength")
                if not isinstance(max_len, int):
                    if not max_len.isdigit():
                        raise ValueError("invalid maxLength: " + max_len)
                    else:
                        roa["maxLength"] = int(max_len)

                result["roas"].append(roa)

            except ValueError as e:
                logging.warning("Invalid ROA: {}, {}".format(
                    str(roa), str(e)
                ))

                invalid += 1
                if invalid > max_invalid_roas:
                    raise RPKIValidatorCacheError(
                        "More than {} invalid ROAs have been found. "
                        "Aborting.".format(max_invalid_roas)
                    )

                continue

        return result

    def _get_data(self):
        # List of (url, error)
        errors = []
        for url in self.urls:
            try:
                res = self._get_data_from_url(url)
                logging.info(
                    "RPKI ROAs loaded successfully from {}".format(url)
                )
                return res
            except RPKIValidatorCacheError as e:
                logging.warning(str(e))
                errors.append((url, str(e)))

        exc_msg = "Impossible to load RPKI ROAs:\n"
        for url, err in errors:
            exc_msg += " - while trying {}: {}\n".format(url, err)
        raise RPKIValidatorCacheError(exc_msg)

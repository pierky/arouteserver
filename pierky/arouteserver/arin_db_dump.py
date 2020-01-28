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

from bz2 import decompress
import json
import logging
import os
import requests
from packaging import version

from .ipaddresses import IPNetwork
from .cached_objects import CachedObject
from .errors import ARINWhoisDBDumpError


class ARINWhoisDBDump(CachedObject):

    EXPIRY_TIME_TAG = "arin_whois_db_dump"

    def __init__(self, *args, **kwargs):
        CachedObject.__init__(self, *args, **kwargs)

        self.source = kwargs.get("source")

        self.whois_records = []

    def load_data(self):
        CachedObject.load_data(self)

        logging.debug("Processing ARIN Whois DB dump")

        dic = self.raw_data

        try:
            json_schema = dic.get("json_schema", None)
            if json_schema is None:
                raise ValueError("'json_schema' key is missing")
            if version.parse(json_schema) >= version.parse("0.2"):
                raise ValueError(
                    "unsupported JSON schema version: {}".format(json_schema)
                )

            source = dic.get("source", None)
            if source is None:
                raise ValueError("'source' key is missing")
            if source != "ARIN-WHOIS":
                raise ValueError(
                    "unsupported source: {}".format(source)
                )

            whois_records = dic.get("whois_records", None)
            if whois_records is None:
                raise ValueError("'whois_records' key is missing")
            if not isinstance(whois_records, dict):
                raise ValueError("'whois_records' is not a list")
            if "v4" not in whois_records and "v6" not in whois_records:
                raise ValueError("'v4' and 'v6' lists missing")

            for v4_v6 in ["v4", "v6"]:
                if not isinstance(whois_records.get(v4_v6, []), list):
                    raise ValueError("'{}': a list was expected".format(
                        v4_v6))
                for record in whois_records.get(v4_v6, []):
                    try:
                        if not isinstance(record, dict):
                            raise ValueError("a dict was expected")
                        if "originas" not in record:
                            raise ValueError("'originas' key is missing")
                        originas = record["originas"]
                        if not originas.startswith("AS"):
                            raise ValueError("Origin AS must start with 'AS'")
                        if not originas[2:].isdigit():
                            raise ValueError(
                                "Origin AS must be in 'AS<n>' format"
                            )
                        if "prefix" not in record:
                            raise ValueError("'prefix' key is missing")
                        prefix = record["prefix"]
                        try:
                            IPNetwork(prefix)
                        except Exception as e:
                            raise ValueError("invalid prefix: {} - {}".format(
                                prefix, str(e)
                            ))
                        self.whois_records.append({
                            "originas": record["originas"],
                            "prefix": record["prefix"]
                        })
                    except ValueError as e:
                        raise ValueError(
                            "invalid record '{}': {}".format(
                                str(record), str(e)
                            )
                        )
        except ValueError as e:
            msg = (
                "An error occurred while processing the ARIN Whois "
                "database dump: {}".format(str(e))
            )
            if self.from_cache:
                logging.warning("{} - trying to bypass the cache".format(msg))
                self.bypass_cache = True
                self.load_data()
            else:
                raise ARINWhoisDBDumpError(msg)

    def _get_object_filename(self):
        return "arin-whois-db-dump.json"

    def _get_data(self):
        if self.source.lower().startswith("http://") or \
            self.source.lower().starswith("https://"):

            logging.debug("Downloading ARIN Whois DB dump")

            url = self.source
            try:
                response = requests.get(url).content
            except requests.exceptions.HTTPError as e:
                raise ARINWhoisDBDumpError(
                    "HTTP error while retrieving ARIN Whois DB dump "
                    "from {}: {}".format(
                        url, str(e)
                    )
                )
            except Exception as e:
                raise ARINWhoisDBDumpError(
                    "Error while retrieving ARIN Whois DB dump "
                    "from {}: {}".format(
                        url, str(e)
                    )
                )
        else:
            logging.debug("Loading ARIN Whois DB dump")

            path = self.source
            if not os.path.exists(path):
                raise ARINWhoisDBDumpError(
                    "The ARIN Whois DB dump can't be found, "
                    "file not found: {}".format(path)
                )
            try:
                with open(path, "rb") as f:
                    response = f.read()
            except Exception as e:
                raise ARINWhoisDBDumpError(
                    "Error while reading the ARIN Whois DB dump "
                    "from {}: {}".format(path, str(e))
                )

        if self.source.endswith(".bz2"):
            try:
                raw = decompress(response).decode("utf-8")
            except Exception as e:
                raise ARINWhoisDBDumpError(
                    "An error occurred while "
                    "decompressing ARIN Whois DB "
                    "BZ2 file: {}".format(str(e))
                )
        else:
            raw = response.decode("utf-8")

        try:
            ret = json.loads(raw)
        except Exception as e:
            raise ARINWhoisDBDumpError(
                "Can't parse ARIN Whois DB JSON file: {}".format(str(e))
            )

        return ret

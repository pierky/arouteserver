# Copyright (C) 2017-2024 Pier Carlo Chiodi
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

import logging
import os

import requests
import urllib.request as request
from contextlib import closing


from .ipaddresses import IPNetwork
from .cached_objects import CachedObject
from .errors import RegistroBRWhoisDBDumpError


class RegistroBRWhoisDBDump(CachedObject):

    EXPIRY_TIME_TAG = "registrobr_whois_db_dump"

    def __init__(self, *args, **kwargs):
        CachedObject.__init__(self, *args, **kwargs)

        self.source = kwargs.get("source")

        self.whois_records = []

    def load_data(self):
        CachedObject.load_data(self)

        logging.debug("Processing Registro.br Whois DB dump")

        raw = self.raw_data
        try:
            for row in raw.splitlines():
                if not row.strip():
                    continue
                try:
                    if "|" not in row:
                        raise ValueError(
                            "unknown record format, missing field separator ('|')"
                        )
                    fields = row.split("|")
                    if len(fields) < 3:
                        if fields[1] == "--whois err--":
                            continue
                        raise ValueError(
                            "unknown record format, less than 3 fields found"
                        )
                    originas = fields[0]
                    if not originas.startswith("AS"):
                        raise ValueError("Origin AS must start with 'AS'")
                    if not originas[2:].isdigit():
                        raise ValueError(
                            "Origin AS must be in 'AS<n>' format"
                        )
                    prefixes = fields[3:]
                    for prefix in prefixes:
                        try:
                            IPNetwork(prefix)
                        except Exception as e:
                            raise ValueError("invalid prefix: {} - {}".format(
                                prefix, str(e)
                            ))
                        self.whois_records.append({
                            "originas": originas,
                            "prefix": prefix
                        })
                except ValueError as e:
                    logging.warning(
                        "invalid record '{}': {}".format(
                            str(row), str(e)
                        )
                    )
                    continue
        except Exception as e:
            msg = (
                "An error occurred while processing the Registro.br Whois "
                "database dump: {}".format(str(e))
            )
            if self.from_cache:
                logging.warning("{} - trying to bypass the cache".format(msg))
                self.bypass_cache = True
                self.load_data()
            else:
                raise RegistroBRWhoisDBDumpError(msg)

    def _get_object_filename(self):
        return "registro-br-whois-db-dump.json"

    def _get_data(self):
        if self.source.lower().startswith("http://") or \
            self.source.lower().startswith("https://"):

            logging.debug("Downloading Registro.br Whois DB dump via HTTP(S)...")

            url = self.source
            try:
                response = requests.get(url)
                raw_data = response.raw.read()
            except Exception as e:
                raise RegistroBRWhoisDBDumpError(
                    "Error while retrieving Registro.br Whois DB dump "
                    "from {}: {}".format(
                        url, str(e)
                    )
                )

        elif self.source.lower().startswith("ftp://"):
            logging.debug("Downloading Registro.br Whois DB dump via FTP...")

            url = self.source
            try:
                with closing(request.urlopen(url)) as r:
                    raw_data = r.read()

            except Exception as e:
                raise RegistroBRWhoisDBDumpError(
                    "Error while retrieving Registro.br Whois DB dump "
                    "from {}: {}".format(
                        url, str(e)
                    )
                )

        else:
            logging.debug("Loading Registro.br Whois DB dump")

            path = self.source
            if not os.path.exists(path):
                raise RegistroBRWhoisDBDumpError(
                    "The Registro.br Whois DB dump can't be found, "
                    "file not found: {}".format(path)
                )
            try:
                with open(path, "rb") as f:
                    raw_data = f.read()
            except Exception as e:
                raise RegistroBRWhoisDBDumpError(
                    "Error while reading the Registro.br Whois DB dump "
                    "from {}: {}".format(path, str(e))
                )

        try:
            return raw_data.decode("utf-8")
        except Exception as e:
            raise RegistroBRWhoisDBDumpError(
                "Can't decode Registro.br Whois DB raw file: {}".format(str(e))
            )

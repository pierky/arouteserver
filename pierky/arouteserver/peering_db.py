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

import logging
import json
import re
from six.moves.urllib.request import urlopen
from six.moves.urllib.error import HTTPError

from .cached_objects import CachedObject
from .errors import PeeringDBError, PeeringDBNoInfoError


class PeeringDBInfo(CachedObject):

    MISSING_INFO_EXCEPTION = PeeringDBNoInfoError

    def _get_peeringdb_url(self):
        raise NotImplementedError()

    @staticmethod
    def _read_from_url(url):
        try:
            response = urlopen(url)
        except HTTPError as e:
            if e.code == 404:
                return "{}"
            else:
                raise PeeringDBError(
                    "HTTP error while retrieving info from PeeringDB: "
                    "code: {}, reason: {} - {}".format(
                        e.code, e.reason, str(e)
                    )
                )
        except Exception as e:
            raise PeeringDBError(
                "Error while retrieving info from PeeringDB: {}".format(
                    str(e)
                )
            )

        return response.read().decode("utf-8")

    def _get_data_from_peeringdb(self):
        plain_text = self._read_from_url(self._get_peeringdb_url())
        try:
            data = json.loads(plain_text)
            return data
        except Exception as e:
            raise PeeringDBError(
                "Error while decoding PeeringDB output: {}".format(
                    str(e)
                )
            )

    def _get_data(self):
        data = self._get_data_from_peeringdb()
        if "data" not in data:
            raise PeeringDBNoInfoError("Missing 'data'")
        if not isinstance(data["data"], list):
            raise PeeringDBNoInfoError("Unexpected format: 'data' is not a list")
        if len(data["data"]) == 0:
            raise PeeringDBNoInfoError("No data for this nextwork")

        return data["data"]

class PeeringDBNet(PeeringDBInfo):

    PEERINGDB_URL = "https://www.peeringdb.com/api/net?asn={asn}"

    def __init__(self, asn, **kwargs):
        PeeringDBInfo.__init__(self, **kwargs)
        self.asn = asn

    def load_data(self):
        logging.debug("Getting data from PeeringDB: net {}".format(self.asn))

        PeeringDBInfo.load_data(self)

        self.info_prefixes4 = self.raw_data[0].get("info_prefixes4", None)
        self.info_prefixes6 = self.raw_data[0].get("info_prefixes6", None)
        self.irr_as_sets = self.parse_as_sets(
            self.raw_data[0].get("irr_as_set", None)
        )

    def parse_as_sets(self, raw_irr_as_sets):
        res = []
        if raw_irr_as_sets and raw_irr_as_sets.strip():
            raw_irr_as_sets = re.split("[/,&\s]", raw_irr_as_sets)
            for raw_irr_as_set in raw_irr_as_sets:
                irr_as_set = self.parse_as_set(raw_irr_as_set)
                if irr_as_set and irr_as_set not in res:
                    res.append(irr_as_set)
        return res

    def parse_as_set(self, in_value):
        v = in_value.strip()

        if not v:
            return None

        guessed = False

        # Removing things like "<registry>::" and "<registry>: ".
        pattern = re.compile("^(?:RIPE|APNIC|AFRINIC|ARIN|NTTCOM|"
                             "ALTDB|BBOI|BELL|JPIRR|LEVEL3|RADB|"
                             "RGNET|SAVVIS|TC):[:\s]", flags=re.IGNORECASE)
        v, number_of_subs_made = pattern.subn("", v)
        if number_of_subs_made > 0:
            v = v.strip()
            guessed = True
        if not v:
            return None

        # Removing "ipv4:" and "ipv6:".
        pattern = re.compile("^(?:ipv4|ipv6):", flags=re.IGNORECASE)
        v, number_of_subs_made = pattern.subn("", v)
        if number_of_subs_made > 0:
            v = v.strip()
            guessed = True
        if not v:
            return None

        # "Many objects in RPSL have a name.  An <object-name> is
        # made up of letters, digits, the character underscore "_",
        # and the character hyphen "-"; the first character of a
        # name must be a letter, and the last character of a name
        # must be a letter or a digit.
        # An AS number x is represented as the string "ASx".  That
        # is, the AS 226 is represented as AS226."
        # https://datatracker.ietf.org/doc/html/rfc2622#section-2
        #
        # "A hierarchical set name is a sequence of set names and
        # AS numbers separated by colons ":".
        # At least one component of such a name must be an actual
        # set name (i.e. start with one of the prefixes above)."
        # https://datatracker.ietf.org/doc/html/rfc2622#section-5
        as_dash_found = False
        parts = []
        for part in v.split(":"):
            name = part.strip().upper()
            if not re.match("^(?:AS[\d]+|AS-[A-Z0-9_\-]*[A-Z0-9])$", name):
                logging.debug("AS-SET from PeeringDB for AS{}: "
                              "ignoring {}, invalid name {}".format(
                                  self.asn, v, name))
                return None
            if name.startswith("AS-"):
                as_dash_found = True
            parts.append(name)
        v = ":".join(parts)

        if not as_dash_found:
            logging.debug("AS-SET from PeeringDB for AS{}: "
                          "ignoring {}, no ""AS-"" found".format(
                              self.asn, v))
            return None

        if guessed:
            logging.info("AS-SET from PeeringDB for AS{}: "
                         "guessed {} from {}".format(
                             self.asn, v, in_value))

        return v

    def _get_object_filename(self):
        return "peeringdb_net_{}.json".format(self.asn)

    def _get_peeringdb_url(self):
        return self.PEERINGDB_URL.format(asn=self.asn)

class PeeringDBNetIXLan(PeeringDBInfo):

    PEERINGDB_URL = "https://www.peeringdb.com/api/netixlan?ixlan_id={ixlanid}"

    def __init__(self, ixlanid, **kwargs):
        PeeringDBInfo.__init__(self, **kwargs)
        self.ixlanid = ixlanid

    def load_data(self):
        logging.debug("Getting data from PeeringDB: Net IX LAN {}".format(self.ixlanid))

        PeeringDBInfo.load_data(self)

    def _get_object_filename(self):
        return "peeringdb_ixlanid_{}.json".format(self.ixlanid)

    def _get_peeringdb_url(self):
        return self.PEERINGDB_URL.format(ixlanid=self.ixlanid)


def clients_from_peeringdb(netixlanid, cache_dir):
    clients = []

    pdb_net_ixlan = PeeringDBNetIXLan(netixlanid, cache_dir=cache_dir)
    pdb_net_ixlan.load_data()
    netixlans = pdb_net_ixlan.raw_data
    for netixlan in netixlans:
        if netixlan["is_rs_peer"] is True:
            client = {
                "asn": netixlan["asn"],
                "ip": [],
            }
            for ipver in ("ipaddr4", "ipaddr6"):
                if netixlan[ipver]:
                    client["ip"].append(netixlan[ipver].encode("ascii", "ignore"))
            clients.append(client)

    asns = {}

    for client in clients:
        asn = client["asn"]
        net = PeeringDBNet(asn)
        net.load_data()

        if not net.irr_as_sets:
            continue

        key = "AS{}".format(asn)
        if key not in asns:
            asns[key] = {
                "as_sets": []
            }

        for irr_as_set in net.irr_as_sets:
            irr_as_set = irr_as_set.strip()
            if irr_as_set not in asns[key]["as_sets"]:
                asns[key]["as_sets"].append(irr_as_set.encode("ascii", "ignore"))

    data = {
        "asns": asns,
        "clients": clients
    }

    return data

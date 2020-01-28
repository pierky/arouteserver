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

import logging
import json
import re
import requests

from .cached_objects import CachedObject
from .config.validators import ValidatorASSet
from .errors import PeeringDBError, PeeringDBNoInfoError, ConfigError
from .irrdb import IRRDBInfo


class PeeringDBInfo(CachedObject):

    EXPIRY_TIME_TAG = "pdb_info"

    MISSING_INFO_EXCEPTION = PeeringDBNoInfoError

    def _get_peeringdb_url(self):
        raise NotImplementedError()

    @staticmethod
    def _read_from_url(url):
        response = requests.get(url)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return "{}"
            else:
                raise PeeringDBError(
                    "HTTP error while retrieving info from PeeringDB: "
                    "{}".format(
                        str(e)
                    )
                )
        except Exception as e:
            raise PeeringDBError(
                "Error while retrieving info from PeeringDB: {}".format(
                    str(e)
                )
            )

        return response.content.decode("utf-8")

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

    EXPIRY_TIME_TAG = "pdb_info"

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

        # Removing "ipv4:" and "ipv6:".
        pattern = re.compile("^(?:ipv4|ipv6):", flags=re.IGNORECASE)
        v, number_of_subs_made = pattern.subn("", v)
        if number_of_subs_made > 0:
            v = v.strip()
            guessed = True
        if not v:
            return None

        # IRR record source
        valid_sources_regex = IRRDBInfo.BGPQ3_DEFAULT_SOURCES.replace(",", "|")

        # Converting stuff like AS-FOO@SOURCE in SOURCE::AS-FOO
        pattern = re.compile(
            "^([^@]+)@({sources})$".format(sources=valid_sources_regex),
            flags=re.IGNORECASE
        )
        v, number_of_subs_made = pattern.subn("\\2::\\1", v)
        if number_of_subs_made > 0:
            guessed = True

        # Converting "SOURCE:AS-FOO" format (single colon) to "SOURCE::AS-FOO"
        # (only for known sources)
        pattern = re.compile(
            "^({sources}):([^:].+)$".format(sources=valid_sources_regex),
            flags=re.IGNORECASE
        )
        v, number_of_subs_made = pattern.subn("\\1::\\2", v)
        if number_of_subs_made > 0:
            guessed = True

        try:
            v = ValidatorASSet().validate(v)
        except ConfigError as e:
            logging.debug("AS-SET from PeeringDB for AS{}: "
                          "ignoring {}, {}".format(self.asn, v, str(e)))
            return None

        if guessed:
            logging.info("AS-SET from PeeringDB for AS{}: "
                         "guessed {} from {}".format(self.asn, v, in_value))

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

class PeeringDBNetNeverViaRouteServers(PeeringDBInfo):

    PEERINGDB_URL = "https://www.peeringdb.com/api/net?info_never_via_route_servers=1"

    EXPIRY_TIME_TAG = "pdb_info"

    def __init__(self, **kwargs):
        PeeringDBInfo.__init__(self, **kwargs)

        self.networks = []

    def load_data(self):
        logging.debug("Getting 'never via route-servers' networks from PeeringDB")

        PeeringDBInfo.load_data(self)

        for network in self.raw_data:
            self.networks.append({
                "asn": network["asn"]
            })

    def _get_object_filename(self):
        return "peeringdb_neverviarouteservers.json"

    def _get_peeringdb_url(self):
        return self.PEERINGDB_URL.format()

class PeeringDBIXList(PeeringDBInfo):

    PEERINGDB_URL = "https://peeringdb.com/api/ix"

    def __init__(self, **kwargs):
        PeeringDBInfo.__init__(self, **kwargs)

        self.ixp_list = []

    def load_data(self):
        logging.debug("Getting the list of IXs from PeeringDB")

        PeeringDBInfo.load_data(self)

        for ixp in self.raw_data:
            self.ixp_list.append({
                "city": ixp["city"],
                "country": ixp["country"],
                "full_name": ixp["name_long"],
                "short_name": ixp["name"],
                "peeringdb_handle": ixp["id"]
            })

    def _get_object_filename(self):
        return "peeringdb_ixlist.json"

    def _get_peeringdb_url(self):
        return self.PEERINGDB_URL

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
                    client["ip"].append(netixlan[ipver].encode("ascii", "ignore").decode("utf-8"))
            clients.append(client)

    asns = {}

    for client in clients:
        asn = client["asn"]
        net = PeeringDBNet(asn, cache_dir=cache_dir)
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
                asns[key]["as_sets"].append(irr_as_set.encode("ascii", "ignore").decode("utf-8"))

    data = {
        "asns": asns,
        "clients": clients
    }

    return data

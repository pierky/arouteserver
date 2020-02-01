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

from .base import BaseConfigEnricher
from ..errors import BuilderError, PeeringDBError, PeeringDBNoInfoError
from ..peering_db import PeeringDBNetNeverViaRouteServers

class NeverViaRouteServersEnricher(BaseConfigEnricher):

    def enrich(self):

        logging.info("Retrieving 'never via route-servers' networks from PeeringDB...")

        try:
            peeringdb_data = PeeringDBNetNeverViaRouteServers(
               cache_dir=self.builder.cache_dir,
               cache_expiry=self.builder.cache_expiry,
            )
            peeringdb_data.load_data()
        except PeeringDBNoInfoError:
            # No data found on PeeringDB.
            logging.warning("No networks found on PeeringDB "
                            "with 'info_never_via_route_servers' "
                            "attribute set.")
            return
        except PeeringDBError as e:
            logging.error(
                "An error occurred while retrieving 'never via route-servers' "
                "networks from PeeringDB: {}".format(
                    str(e) or "error unknown"
                )
            )
            raise BuilderError()

        for network in peeringdb_data.networks:
            asn = network["asn"]
            if asn not in self.builder.never_via_route_servers_asns:
                self.builder.never_via_route_servers_asns.append(asn)

        logging.info("{} 'never via route-servers' networks "
                     "found on PeeringDB".format(len(peeringdb_data.networks)))

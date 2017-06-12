#!/usr/bin/env python

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

import argparse
import base64
import json
import sys
try:
        from urllib.request import Request, urlopen
except ImportError: # Python 2
        from urllib2 import Request, urlopen

def run(args):
    try:
        import yaml
    except:
        print("\n")
        print("In order to used this script, the 'PyYAML' package is needed.")
        print("Please consider installing it using the 'pip install PyYAML'.")
        print("\n")
        return False

    with open(args.clients, "r") as f:
        cfg = yaml.safe_load(f)

    networks = {}
    email = {
        "type": "email",
        "host": "smtp_server_address",
        "from_addr": "noc@acme-ix.net",
        "template_file": "/etc/exabgp/template",

        "recipients": {
        }
    }

    clients = cfg["clients"]
    for client in clients:
        asn = "AS{}".format(client["asn"])
        neighbors = client["ip"]
        if not isinstance(neighbors, list):
            neighbors = [neighbors]

        if asn not in networks:
            networks[asn] = {
                "neighbors": neighbors
            }
        else:
            networks[asn]["neighbors"].extend(neighbors)
        networks[asn]["neighbors"] = list(set(networks[asn]["neighbors"]))

        if args.email:
            if asn not in email["recipients"]:
                email["recipients"][asn] = {
                    "info": {
                        "email": []
                    }
                }

    if args.email and args.fetch_email_from_peeringdb:

        for asn in email["recipients"]:
            print("Fetching contacts from PeeringDB: {}...".format(asn))

            url = "https://www.peeringdb.com/api/net?asn={asn}".format(
                asn=asn[2:]
            )
            try:
                response = urlopen(url)
            except Exception as e:
                print("Error while fetching network info "
                      "from PeeringDB: {}".format(str(e)))
                continue

            try:
                json_obj = json.load(response.fp)
            except Exception as e:
                print("Error while decoding PeeringDB "
                      "network object: {}".format(str(e)))
                continue
            finally:
                response.close()

            try:
                net_id = int(json_obj["data"][0]["id"])
            except Exception as e:
                print("Error while getting network ID from "
                      "PeeringDB network object: {}".format(str(e)))
                continue

            url = "https://www.peeringdb.com/api/poc?net_id={}".format(net_id)
            try:
                if args.peeringdb_username and args.peeringdb_password:
                    credentials = '{}:{}'.format(
                        args.peeringdb_username, args.peeringdb_password
                    )
                    response = urlopen(Request(url, headers={
                        "Authorization": "Basic " + base64.b64encode(credentials)
                    }))
                else:
                    response = urlopen(url)
            except Exception as e:
                print("Error while fetching contacts info "
                      "from PeeringDB: {}".format(str(e)))
                continue

            try:
                json_obj = json.load(response.fp)
            except Exception as e:
                print("Error while decoding PeeringDB "
                      "contacts object: {}".format(str(e)))
                continue
            finally:
                response.close()

            for contact in json_obj["data"]:
                if not contact["email"]:
                    continue
                if contact["email"] in email["recipients"][asn]["info"]["email"]:
                    continue

                if contact["status"] == "ok" and \
                    contact["role"] in ["Technical", "NOC"]:

                    email["recipients"][asn]["info"]["email"].append(
                        contact["email"]
                    )

    json.dump(networks, args.networks, indent=2)

    if args.email:
        json.dump(email, args.email, indent=2)

    return True

def main():
    parser = argparse.ArgumentParser(
       description="Build config files for invalid_routes_reporter.py "
                   "starting from ARouteServer 'clients.yml' file.",
       epilog="Copyright (c) {} - Pier Carlo Chiodi - "
              "https://pierky.com".format(2017)
    )

    parser.add_argument(
        "-n", "--networks",
        type=argparse.FileType('w'),
        help="The output file where the networks configuration will be "
             "written. Default: stdout.",
        default=sys.stdout
    )

    group = parser.add_argument_group(
        title="EMail alerter configuration",
        description="This section can be used to also configure an "
                    "email alerter using information from ARouteServer "
                    "'clients.yml' configuration file and - optionally - "
                    "from PeeringDB."
    )
    group.add_argument(
        "--email",
        type=argparse.FileType('w'),
        help="The output file where the email alerter configuration will be "
             "written."
    )
    group.add_argument(
        "--fetch-email-from-peeringdb",
        action="store_true",
        help="If set, the email addresses used to send alerts are fetched "
             "from PeeringDB. Used only if --email is given.",
    )
    group.add_argument(
        "--peeringdb-username",
        help="PeeringDB username. Used only if --fetch-email-from-peeringdb "
             "is given. Some networks' contacts on PeeringDB are "
             "hidden because they are only visible to authenticated users. "
             "Providing valid username and password here allows to access "
             "those contacts."
    )
    group.add_argument(
        "--peeringdb-password",
        help="PeeringDB password. See also --peeringdb-username."
    )

    parser.add_argument(
        "clients",
        help="ARouteServer 'clients.yml' file."
    )

    args = parser.parse_args()

    if run(args):
        sys.exit(0)
    else:
        sys.exit(1)

main()

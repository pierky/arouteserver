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
import six
import telnetlib

from .cached_objects import CachedObject
from .errors import WhoisError, WhoisResourceError


class WhoisClient(object):

    def __init__(self, server="whois.ripe.net", port=43, timeout=30):
        self.server = server
        self.port = port
        self.timeout = timeout

        self.connected = False
        self.socket = None

    def _connect(self):
        if self.connected:
            return

        try:
            logging.debug("Connecting to {}:{}".format(
                self.server, self.port
            ))
            self.socket = telnetlib.Telnet(
                self.server, self.port, self.timeout
            )
        except Exception as e:
            raise WhoisError(
                "Can't connect to the whois server at {}:{} - {}".format(
                    self.server, self.port, str(e)
                )
            )

        self.connected = True

        # Switch to a persistent connection.
        try:
            self._query("-k")
        except Exception as e:
            raise WhoisError(
                "Error while switching to a permanent connection: {}".format(
                    str(e)
                )
            )

    def _close(self):
        logging.debug("Closing connection to {}:{}".format(
                self.server, self.port
        ))

        self.connected = False
        try:
            self.socket.close()
        except:
            pass

        self.socket = None

    def _send_cmd(self, cmd):
        assert self.connected

        try:
            self.socket.write(six.b(cmd + "\n"))
        except Exception as e:
            raise WhoisError(
                "Error while sending command '{}' - {}".format(
                    cmd, str(e)
                )
            )

    def _read_line(self, timeout=None):
        assert self.connected

        try:
            line = self.socket.read_until(six.b("\n"), timeout=timeout)
            line = line.decode("utf-8")
        except Exception as e:
            raise WhoisError(
                "An error occurred while reading data "
                "from the server: {}".format(str(e))
            )

        return line

    def _get_response(self):
        assert self.connected

        response = ""
        consecutive_empty_line_cnt = 0

        err = None
        while True:
            line = self._read_line()

            line = line.strip()

            if not line:
                consecutive_empty_line_cnt += 1
                if consecutive_empty_line_cnt == 2:
                    break
                continue

            consecutive_empty_line_cnt = 0

            if line.startswith("%ERROR:101:"):
                err = (WhoisResourceError, line)
                continue

            if line.startswith("%ERROR:"):
                err = (WhoisError, line)
                continue

            if line.startswith("%"):
                continue

            response += line + "\n"

        if err:
            raise err[0](err[1])

        return response

    def _query(self, cmd):
        assert self.connected

        logging.debug("Sending query: '{}'".format(cmd))

        self._send_cmd(cmd)

        try:
            return self._get_response()
        except Exception as e:
            raise WhoisError(
                "An error occurred while processing the response "
                "for this query: '{}' - {}".format(
                    cmd, str(e)
                )
            )

    def query(self, cmd):
        tries = 0
        while True:
            self._connect()

            tries += 1
            try:
                return self._query(cmd)
            except WhoisError as e:
                self._close()
                if tries < 3:
                    logging.debug(
                        "Query failed: {} - Retrying.".format(str(e))
                    )
                else:
                    logging.error(
                        "Query failed: {} - Aborting.".format(str(e))
                    )
                    raise

    def get_autnum(self, asn):
        return self.query(
            "--no-referenced --no-personal -T aut-num {}".format(asn)
        )

class AutNumObject(CachedObject):

    def __init__(self, asn, *args, **kwargs):
        CachedObject.__init__(self, *args, **kwargs)

        assert asn.startswith("AS"), \
            "Invalid ASN: must be in 'ASxxx' format"
        assert asn[2:].isdigit(), \
            "Invalid ASN: must be in 'ASxxx' format"

        self.asn = asn

        self.whois_client = kwargs.get("whois_client", None)
        if not self.whois_client:
            self.whois_client = WhoisClient()

    def _get_object_filename(self):
        return "aut-num-{}.txt".format(self.asn)

    def _get_data(self):
        logging.info("Retrieving {} aut-num info".format(self.asn))
        return self.whois_client.get_autnum(self.asn)

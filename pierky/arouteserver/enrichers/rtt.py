# Copyright (C) 2017-2018 Pier Carlo Chiodi
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
import re
import subprocess

from .base import BaseConfigEnricher, BaseConfigEnricherThread
from ..errors import BuilderError, MissingFileError

class RTTGetter_WorkerThread(BaseConfigEnricherThread):

    DESCR = "RTTGetter"

    # The following regex pattern is reported by docs/RTT_GETTER.rst
    RETURN_VALUE_RE_PATTERN = re.compile("^\d+[.]?\d*$")

    def __init__(self, *args, **kwargs):
        BaseConfigEnricherThread.__init__(self, *args, **kwargs)

        self.rtt_getter_path = None

    @staticmethod
    def _parse_result(raw):
        if not raw:
            raise ValueError("no value returned")

        res = raw.strip()
        if not res:
            raise ValueError("empty value returned")

        res = res.split("\n")[0]
        if res.lower() == "none":
            return None

        if not RTTGetter_WorkerThread.RETURN_VALUE_RE_PATTERN.match(res):
            raise ValueError("invalid value: {}".format(res))

        return float(res)

    def do_task(self, task):
        client = task

        cmd = [self.rtt_getter_path]
        cmd += [client["ip"]]
        cmd += [str(client["asn"])]
        cmd += [str(client["id"])]

        try:
            out = subprocess.check_output(cmd)
        except Exception as e:
            err = "Error while executing RTT getter command '{}': {}".format(
                " ".join(cmd), str(e)
            )
            logging.error(err)
            raise BuilderError()

        try:
            return self._parse_result(out.decode("utf-8"))
        except ValueError as e:
            err = ("Error while parsing result from "
                   "RTT getter command '{}': {}".format(" ".join(cmd), str(e)))
            logging.error(err)
            raise BuilderError()

    def save_data(self, task, data):
        client = task
        rtt = data
        client["rtt"] = rtt

class RTTGetterConfigEnricher(BaseConfigEnricher):

    WORKER_THREAD_CLASS = RTTGetter_WorkerThread

    def prepare(self):
        path = self.builder.rtt_getter_path
        if path:
            if not os.path.exists(path):
                raise MissingFileError(path)
            if not (os.path.isfile(path) and \
                    os.access(path, os.X_OK)):
                raise BuilderError(
                    "The file {} used for rtt_getter_path is not "
                    "executable.".format(path)
                )
        else:
            raise BuilderError("Path of the RTT getter program is missing.")

    def _config_thread(self, thread):
        thread.rtt_getter_path = self.builder.rtt_getter_path

    def add_tasks(self):
        # Enqueuing tasks.
        for client in self.builder.cfg_clients.cfg["clients"]:
            self.tasks_q.put(client)

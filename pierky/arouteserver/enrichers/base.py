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
from Queue import Queue, Empty, Full
import threading

from ..errors import BuilderError, ARouteServerError

class BaseConfigEnricherThread(threading.Thread):

    DESCR = None

    def __init__(self, tasks_q, errors_q, lock):
        threading.Thread.__init__(self)

        self.tasks_q = tasks_q
        self.errors_q = errors_q
        self.lock = lock

    def do_task(self, task):
        raise NotImplementedError()

    def save_data(self, task, data):
        raise NotImplementedError()

    def run(self):
        logging.debug("{} thread {} started".format(self.DESCR, self.name))

        while True:
            try:
                task = self.tasks_q.get(block=True, timeout=0.1)
            except Empty:
                break

            try:
                data = self.do_task(task)
                if data:
                    with self.lock:
                        self.save_data(task, data)
            except Exception as e:
                if not isinstance(e, ARouteServerError):
                    logging.debug("{} thread {} error: {}".format(
                        self.DESCR, self.name, str(e)))
                try:
                    self.errors_q.put_nowait(True)
                except Full:
                    pass

            self.tasks_q.task_done()

        logging.debug("{} thread {} stopped".format(
            self.DESCR, self.name))

class BaseConfigEnricher(object):

    WORKER_THREAD_CLASS = None

    def __init__(self, builder, threads):
        self.builder = builder
        self.threads = threads
        self.tasks_q = Queue()
        self.errors_q = Queue(maxsize=1)

    def prepare(self):
        pass

    def _config_thread(self, thread):
        pass

    def add_tasks(self):
        raise NotImplementedError()

    def enrich(self):
        self.prepare()

        lock = threading.Lock()

        threads = []
        for i in range(self.threads):
            t = self.WORKER_THREAD_CLASS(
                self.tasks_q, self.errors_q, lock
            )
            self._config_thread(t)
            threads.append(t)

        self.add_tasks()

        for t in threads:
            t.start()

        self.tasks_q.join()

        try:
            self.errors_q.get_nowait()
            raise BuilderError()
        except Empty:
            return

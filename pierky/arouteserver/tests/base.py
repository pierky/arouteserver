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
import os
import sys
import unittest


class CaptureLog(logging.Handler):

    def __init__(self, *args, **kwargs):
        self.reset_messages()
        super(CaptureLog, self).__init__(*args, **kwargs)

    def reset_messages(self):
        self.msgs = []
        self.warnings = []

    def emit(self, record):
        self.acquire()
        try:
            if record.levelname.lower() == "error":
                self.msgs.append(record.getMessage())
            if record.levelname.lower() == "warning":
                self.warnings.append(record.getMessage())
        finally:
            self.release()

    def reset(self):
        self.acquire()
        try:
            self._reset_messages()
        finally:
            self.release()

class ARouteServerTestCase(unittest.TestCase):

    NEED_TO_CAPTURE_LOG = False
    SHORT_DESCR = ""
    DEBUG = False
    SKIP_ON_TRAVIS = False

    def _capture_log(self):
        self.logger_handler = None
        if self.NEED_TO_CAPTURE_LOG:
            logger = logging.getLogger()
            self.logger_handler = CaptureLog(level="DEBUG")
            logger.addHandler(self.logger_handler)

            self.logger_handler.reset_messages()

    def clear_log(self):
        if self.logger_handler:
            self.logger_handler.reset_messages()

    def _setUp(self):
        pass

    def setUp(self):
        self._capture_log()
        self._setUp()

    @classmethod
    def _setUpClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        cls._setUpClass()

    @classmethod
    def _tearDownClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        cls._tearDownClass()

    @classmethod
    def print_msg(cls, s):
        sys.stderr.write("{}\n".format(s))

    @classmethod
    def debug(cls, s):
        if cls.DEBUG or "DEBUG" in os.environ:
            cls.print_msg("DEBUG: {}".format(s))

    @classmethod
    def info(cls, s):
        cls.print_msg(s)

    def shortDescription(self):
        return self._testMethodDoc.format(self.SHORT_DESCR)

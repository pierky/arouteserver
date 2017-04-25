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
import yaml

from pierky.arouteserver.errors import ConfigError, ARouteServerError
from pierky.arouteserver.tests.base import ARouteServerTestCase


class TestConfigParserBase(ARouteServerTestCase):

    NEED_TO_CAPTURE_LOG = True

    FILE_PATH = None
    CONFIG_PARSER_CLASS = None

    def _setUp(self):
        self.load_config()

    def load_config(self, file_name=None, yaml=None):
        self.cfg = None
        self.cfg = self.CONFIG_PARSER_CLASS()
        if yaml:
            self.cfg._load_from_yaml(yaml)
        elif file_name:
            self.cfg.load(file_name)
        else:
            self.cfg.load(self.FILE_PATH)

    def _contains_err(self, err=None):
        logging.info("-----------------------------------------------")
        self.clear_log()

        exception_raised = False
        try:
            self.cfg.parse()
        except ARouteServerError as e:
            exception_raised = True
            if err is None:
                self.fail(
                    "An unexpected exception occurred: {}".format(
                        str(e)
                    )
                )
        if err is not None and not exception_raised:
            self.fail(
                "An error was expected but no exceptions have been raised"
            )

        res = self.logger_handler.msgs

        found = False

        if err:
            for s in res:
                if err in s:
                    found = True

            if not found:
                self.fail("Error message expected but not found:\n"
                          " - expected:\n"
                          "\t{}\n"
                          " - received: \n"
                          "\t{}".format(
                              err, "\n\t".join(res)
                              ))
        elif res:
            raise self.fail(
                "Unexpected error message(s) found:\n"
                "\t{}".format("\n\t".join(res))
            )

    def _test_mandatory(self, dic, key, has_default=False):
        del dic[key]
        if has_default:
            self._contains_err()
        else:
            self._contains_err("Can't be empty.")

        for v in (None, "", "     "):
            dic[key] = v
            if has_default:
                self._contains_err()
            else:
                self._contains_err("Can't be empty.")

    def _test_optional(self, dic, key):
        del dic[key]
        self._contains_err()

        for v in (None, "", "     "):
            dic[key] = v
            self._contains_err()

    def _test_bool_val(self, dic, key):
        for v in (True, "true", "True", "tRuE", "yes", "YES", "t", "T", "1", 1):
            dic[key] = v
            self._contains_err()
        for v in (False, "false", "False", "fAlSe", "no", "NO", "f", "F", "0", 0):
            dic[key] = v
            self._contains_err()
        for v in ("sure"):
            dic[key] = v
            self._contains_err("Invalid boolean value: {}.".format(v))

    def _test_option(self, dic, key, valid_options):
        for v in valid_options:
            dic[key] = v
            self._contains_err()
        for v in ("xxx", "yyy"):
            dic[key] = v
            self._contains_err("Invalid option for '{}': '{}';".format(key, v))

    def _test_ip_min_max_len(self, dic, key, min_max, ip_ver, valid, invalid):
        for v in valid:
            dic[key][min_max] = v
            self._contains_err()
        for v in invalid:
            dic[key][min_max] = v
            self._contains_err("'{}' in the IPv{} min/max length".format(min_max, ip_ver))

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

import json
try:
    import mock
except ImportError:
    import unittest.mock as mock
import os
import re
from tatsu.util import asjson
import unittest

from pierky.arouteserver.cached_objects import CachedObject
from pierky.arouteserver.rpsl.rpsl_via import RPSLViaParser
from pierky.arouteserver.whois import WhoisClient, AutNumObject

dir_path = os.path.join(os.path.dirname(__file__), "rpsl-via")

def remove_dup_whitespace(s):
    return re.sub("\s+", " ", s)

def _create_new_test_syntax(line):

    def test_syntax(self):
        self._test_syntax(line)

    return test_syntax

def _create_new_test_exp_result(line, exp_res, exp_res_file):

    def test_exp_result(self):

        def print_exp_res():
            res = "\n"
            res += " cat <<EOF > {}".format(exp_res_file) + "\n"
            res += json.dumps(dic, indent=2) + "\n"
            res += "EOF" + "\n"
            res += "\n"
            return res

        self.maxDiff = None

        parser = RPSLViaParser()
        ast = parser.parse(line, rule_name="start")
        dic = asjson(ast)

        if exp_res:
            self.assertDictEqual(dic, exp_res, "\n\nTo fix it:\n{}".format(print_exp_res()))
            return

        print(print_exp_res())

    return test_exp_result

def _create_new_test_autnum_whois(asn):

    @unittest.skipIf("TRAVIS" in os.environ, "not executed on TRAVIS")
    def test_autnum_whois(self):
        if asn in ["AS48526"]:
            raise unittest.SkipTest("OR syntax not supported")

        aut_num = AutNumObject(asn, whois_client=self.client)
        rpsl_via_lines = aut_num.get_rpsl_via_lines()
        for line in rpsl_via_lines:
            try:
                self._test_syntax(line)
            except:
                print("\n\nError while processing '{}'\n\n".format(line))
                raise

    return test_autnum_whois

def _create_new_test_process_autnum(asn, content):

    def test_autnum_content(self):
        aut_num = AutNumObject(asn)
        aut_num.raw_data = content
        rpsl_via_lines = aut_num.get_rpsl_via_lines()
        for line in rpsl_via_lines:
            try:
                self._test_syntax(line)
            except:
                print("\n\nError while processing '{}'\n\n".format(line))
                raise

    return test_autnum_content

def populate_line_by_line(cls, arg_list):
    for filename, line_no, line in arg_list:
        doc_line = line
        doc_line = doc_line.replace("import-via:", "iv:")
        doc_line = doc_line.replace("export-via:", "ev:")
        doc_line = remove_dup_whitespace(doc_line)

        base_filename = filename.replace(".rpsl", "")

        _method = _create_new_test_syntax(line)
        _method.__name__ = "test_syntax_{}_{}".format(base_filename, line_no)
        _method.__doc__ = "RPSL syntax: {}-{}, {}".format(base_filename, line_no, doc_line)
        setattr(cls, _method.__name__, _method)

        exp_res_filepath = os.path.join(dir_path, "{}-{}.json".format(base_filename, line_no))
        if not os.path.exists(exp_res_filepath):
            continue

        with open(exp_res_filepath, "r") as f:
            exp_res_line = f.read()
        if exp_res_line:
            exp_res = json.loads(exp_res_line)
        else:
            exp_res = {}

        _method = _create_new_test_exp_result(line, exp_res, exp_res_filepath)
        _method.__name__ = "test_exp_result_{}_{}".format(base_filename, line_no)
        _method.__doc__ = "RPSL result: {}-{}, {}".format(base_filename, line_no, doc_line)
        setattr(cls, _method.__name__, _method)

def populate_whois_queries(cls, file_list):
    # Iterate over unique filenames with format [0-9]+.rpsl and use
    # the ASN to run a whois query, extract RPSL-via statements and
    # parse them.
    for filename in file_list:
        if not re.match("^[0-9]+\.rpsl$", filename):
            continue

        asn = "AS" + filename.replace(".rpsl", "")
        _method = _create_new_test_autnum_whois(asn)
        _method.__name__ = "test_autnum_whois_{}".format(asn)
        _method.__doc__ = "RPSL from Whois aut-num: {}".format(asn)
        setattr(cls, _method.__name__, _method)

def populate_autnum_processing(cls, file_list):
    for filename in file_list:
        match = re.match("^([0-9]+).*\.aut-num$", filename)
        if not match:
            continue
        asn = "AS" + match.group(1)
        path = os.path.join(dir_path, filename)

        with open(path, "r") as f:
            content = f.read()

        _method = _create_new_test_process_autnum(asn, content)
        _method.__name__ = "test_autnum_content_{}".format(filename)
        _method.__doc__ = "aut-num processing: {}".format(filename)
        setattr(cls, _method.__name__, _method)

class TestRPSLSyntax(unittest.TestCase):

    @classmethod
    def mock_cached_objects(cls):

        def load_data_from_cache(self):
            return False

        def save_data_to_cache(self):
            return

        mock_load_data_from_cache = mock.patch.object(
            CachedObject, "load_data_from_cache", autospec=True
        ).start()
        mock_load_data_from_cache.side_effect = load_data_from_cache

        mock_save_data_to_cache = mock.patch.object(
            CachedObject, "save_data_to_cache", autospec=True
        ).start()
        mock_save_data_to_cache.side_effect = save_data_to_cache

    @classmethod
    def setUpClass(cls):
        cls.mock_cached_objects()

        cls.client = WhoisClient()

    def _test_syntax(self, line):
        parser = RPSLViaParser()
        ast = parser.parse(line, rule_name="start")

        # Build the reverse statement starting from the result of the parser
        # and check that it matches the input line.
        # Do this only when there are no actions in the original line, too
        # much effort to rebuild the action list.
        if "action" in line:
            return

        dic = asjson(ast)

        from_to = "from" if dic["action"] == "import-via:" else "to"
        accept_announce = "accept" if dic["action"] == "import-via:" else "announce"

        s = "{action} {afi} {rules} {filter}".format(
            action=dic["action"],
            afi="afi {afi_list}".format(
                afi_list=" ".join([afi for afi in dic["afi"]])
            ) if dic["afi"] else "",
            rules=" ".join([
                "{via} {from_to} {peers}".format(
                    from_to=from_to,
                    via="{intermediate_as} {router}".format(
                        intermediate_as=rule["via"]["intermediate_as"],
                        router="{peer} {at} {local}".format(
                            peer=rule["via"]["router"]["peer_router"]
                                 if rule["via"]["router"] and rule["via"]["router"]["peer_router"]
                                 else "",
                            at="at"
                               if rule["via"]["router"] and rule["via"]["router"]["local_router"]
                               else "",
                            local=rule["via"]["router"]["local_router"]
                                  if rule["via"]["router"] and rule["via"]["router"]["local_router"]
                                  else "",
                        )
                    ),
                    peers="{peer}{except_}".format(
                        peer=rule["peers"]["{}_peer".format(from_to)]["peer"],
                        except_=" EXCEPT {}".format(rule["peers"]["{}_peer".format(from_to)]["except_"])
                                if rule["peers"]["{}_peer".format(from_to)]["except_"]
                                else ""
                    )
                ) for rule in dic["rules"]
            ]),
            filter="{accept_announce} {objects}".format(
                accept_announce=accept_announce,
                objects=" ".join(dic[accept_announce])
            )
        )
        s = remove_dup_whitespace(s)
        if line.strip().endswith(";"):
            s += ";"
        self.assertEqual(
            s.lower().strip(),
            remove_dup_whitespace(line).lower().strip()
        )

        return dic

# Directory layout:
# <tag>.rpsl
#   Content: rpsl-via lines
#   Tests (for each line):
#   - test_syntax_<tag>_<line_no>:
#     - rpsl-via parsing
#     - reverse statement from parsed result
#   - [if the file <tag>-<line_no>.json exists]
#     test_exp_result_<tag>_<line_no>:
#     - match expected result
#   Tests (for each file where <tag> is [0-9]+):
#   - test_autnum_whois_<tag>:
#     - real whois query + rpsl-via lines parsing + test_syntax
# <tag>.aut-num
#   Content: raw aut-num data from whois
#   Tests (for each file):
#   - test_autnum_content_<filename>:
#     - processing of rpsl-via lines + syntax check
line_by_line_tests = []
whois_queries_tests = []
autnum_processing_tests = []
for filename in os.listdir(dir_path):
    path = os.path.join(dir_path, filename)
    if not os.path.isfile(path):
        continue

    if filename.endswith(".json"):
        continue

    if filename.endswith(".rpsl"):
        whois_queries_tests.append(filename)

        with open(path, "r") as f:
            line_no = 0
            for line in f.readlines():
                line_no += 1
                if not line:
                    continue
                line_by_line_tests.append((filename, line_no, line))

    if filename.endswith(".aut-num"):
        autnum_processing_tests.append(filename)

populate_line_by_line(TestRPSLSyntax, line_by_line_tests)
populate_whois_queries(TestRPSLSyntax, whois_queries_tests)
populate_autnum_processing(TestRPSLSyntax, autnum_processing_tests)

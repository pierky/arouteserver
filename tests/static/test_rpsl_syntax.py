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
import os
from nose.tools import istest
import re
from tatsu.util import asjson
import unittest

from pierky.arouteserver.rpsl.rpsl_via import RPSLViaParser

dir_path = os.path.join(os.path.dirname(__file__), "rpsl-via")

def remove_dup_whitespace(s):
    return re.sub("\s+", " ", s)

def _test_syntax(line):

    def test_syntax(self):
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
        self.assertEqual(s.lower().strip(), remove_dup_whitespace(line).lower().strip())

    return test_syntax

def _test_exp_result(line, exp_res, exp_res_file):

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

def populate(cls, arg_list):
    for filename, line_no, line in arg_list:
        doc_line = line
        doc_line = doc_line.replace("import-via:", "iv:")
        doc_line = doc_line.replace("export-via:", "ev:")
        doc_line = remove_dup_whitespace(doc_line)

        base_filename = filename.replace(".rpsl", "")

        _method = _test_syntax(line)
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

        _method = _test_exp_result(line, exp_res, exp_res_filepath)
        _method.__name__ = "test_exp_result_{}_{}".format(base_filename, line_no)
        _method.__doc__ = "RPSL result: {}-{}, {}".format(base_filename, line_no, doc_line)
        setattr(cls, _method.__name__, _method)

class TestRPSLSyntax(unittest.TestCase):

    pass

args = []
for filename in os.listdir(dir_path):
    if filename.endswith(".json"):
        continue
    if not filename.endswith(".rpsl"):
        continue

    path = os.path.join(dir_path, filename)
    if not os.path.isfile(path):
        continue

    with open(path, "r") as f:
        line_no = 0
        for line in f.readlines():
            line_no += 1
            if not line:
                continue
            args.append((filename, line_no, line))

populate(TestRPSLSyntax, args)

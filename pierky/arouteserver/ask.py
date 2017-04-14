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

import sys

def ask(text, options=None, default=None):
    """Returns: ([True|False], answer)"""

    msg = "{} ".format(text)
    if options:
        msg_options = []
        for opt in options:
            if opt == default:
                msg_options.append(opt.upper())
            else:
                msg_options.append(str(opt))
        msg += "["
        msg += "/".join(msg_options)
        msg += "] "
    else:
        if default:
            msg += "(default: {}) ".format(default)
    sys.stdout.write(msg)

    try:
        answer = raw_input()
    except:
        return False, None

    answer = answer.strip()
    if answer:
        if options and answer not in options:
            print("Invalid choice: {} - must be one of {}.".format(
                answer, ", ".join(options)))
            return False, None
        return True, answer
    else:
        if default:
            return True, default
        else:
            print("No answer given.")
            return False, None

def ask_yes_no(text, default=None):
    return ask(text, ["yes", "no"], default)

def ask_int(text, default=None):
    answer_given, v = ask(text, None, default)
    if not answer_given:
        return False, None
    if not v.isdigit():
        print("Invalid input: it must be an integer.")
        return False, None
    return True, int(v)

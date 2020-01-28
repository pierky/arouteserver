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

from six.moves import input
import sys

from .ipaddresses import IPAddress

class Ask(object):

    def __init__(self):
        self.next_answer = None

    def get_input(self):
        if self.next_answer:
            ans = self.next_answer
            self.next_answer = None
            self.wr_out(ans)
            return ans
        else:
            return input()

    def wr_out(self, msg):
        sys.stdout.write(msg)

    def ask(self, text, options=None, default=None, raise_exc=False):
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
        self.wr_out(msg)

        try:
            answer = self.get_input()
        except:
            if raise_exc:
                raise
            return False, None

        answer = answer.strip()
        if answer:
            if options and answer.lower() not in [_.lower() for _ in options]:
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

    def ask_yes_no(self, text, default=None, raise_exc=False):
        return self.ask(text, ["yes", "no"], default, raise_exc)

    def ask_int(self, text, default=None, raise_exc=False):
        answer_given, v = self.ask(text, None, default, raise_exc)
        if not answer_given:
            return False, None
        if not v.isdigit():
            print("Invalid input: it must be an integer.")
            return False, None
        return True, int(v)

    def ask_ipv4_addr(self, text, default=None, raise_exc=False):
        answer_given, v = self.ask(text, None, default, raise_exc)
        if not answer_given:
            return False, None
        try:
            ip = IPAddress(v)
            if ip.version != 4:
                raise ValueError()
        except:
            print("Invalid input: must be a valid IPv4 address.")
            return False, None
        return True, ip.ip

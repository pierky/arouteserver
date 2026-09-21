# Copyright (C) 2017-2026 Pier Carlo Chiodi
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

class RPKIRTRScenario_Data4(object):

    DATA = {
        "rs_IPAddress":                     "192.0.2.2",

        "AS10745_allowed_prefixes":         "199.43.0.0/24",
        "AS3333_allowed_prefixes":          "193.0.0.0/21",

        "AS1_1_IPAddress":                  "192.0.2.111",
        "AS1_1":                            "193.0.0.0/24",

        # The following prefixes are not covered by any ROA, so that
        # the outcome of the ASPA verification can be observed
        # independently of the RPKI BGP Origin Validation one.
        # They are announced by AS1 with a two hops AS_PATH, because
        # a route originated by the announcing client itself can
        # never be ASPA INVALID.
        "AS1_aspa_valid":                   "193.0.9.0/24",
        "AS1_aspa_invalid":                 "193.0.8.0/24",
        "AS1_aspa_unknown":                 "193.0.10.0/24"
    }

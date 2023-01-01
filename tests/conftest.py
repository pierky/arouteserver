# Copyright (C) 2017-2023 Pier Carlo Chiodi
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

# To show the output of pytest using the description of the test case.
def pytest_itemcollected(item):
    par = item.parent.obj

    short_descr = getattr(par, "SHORT_DESCR", "")

    node = item.obj

    suf = node.__doc__.strip() if node.__doc__ else node.__name__

    if suf:
        item._nodeid = suf.format(short_descr)

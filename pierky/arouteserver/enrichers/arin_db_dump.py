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

from .irr_db_dump import GenericIRRWhoisDBDumpEnricher
from ..arin_db_dump import ARINWhoisDBDump

class ARINWhoisDBDumpEnricher(GenericIRRWhoisDBDumpEnricher):

    DESCR = "ARIN"
    DIR_NAME = "arin_db"
    CONFIG_SECTION_NAME = "use_arin_bulk_whois_data"
    PARSER_CLASS = ARINWhoisDBDump
    BUILDER_TARGET_DICT_NAME = "arin_whois_records"

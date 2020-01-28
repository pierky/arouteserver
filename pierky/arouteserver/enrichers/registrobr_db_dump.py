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

from .irr_db_dump import GenericIRRWhoisDBDumpEnricher
from ..registro_br_db_dump import RegistroBRWhoisDBDump

class RegistroBRWhoisDBDumpEnricher(GenericIRRWhoisDBDumpEnricher):

    DESCR = "Registro.br"
    DIR_NAME = "registrobr_db"
    CONFIG_SECTION_NAME = "use_registrobr_bulk_whois_data"
    PARSER_CLASS = RegistroBRWhoisDBDump
    BUILDER_TARGET_DICT_NAME = "registrobr_whois_records"

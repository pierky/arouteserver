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

from .tpl_rendering import HTMLCommand, DumpTemplateContextCommand, \
                          BIRDCommand, OpenBGPDCommand, BuildCommand
from .check_new_release import CheckNewRelease
from .clients_from_peeringdb import ClientsFromPeeringDBCommand
from .clients_from_euroix import ClientsFromEuroIXCommand
from .setup import SetupCommand
from .setup_templates import SetupTemplatesCommand
from .verify_templates import VerifyTemplatesCommand
from .init_scenario import InitScenarioCommand
from .configure import ConfigureCommand
from .show_config import ShowConfigCommand
from .ixf_member_list_from_clients import IXFMemberListFromClientsCommand

all_commands = [
    BuildCommand,
    BIRDCommand,
    OpenBGPDCommand,
    HTMLCommand,
    DumpTemplateContextCommand,
    ClientsFromPeeringDBCommand,
    ClientsFromEuroIXCommand,
    SetupCommand,
    SetupTemplatesCommand,
    VerifyTemplatesCommand,
    ConfigureCommand,
    ShowConfigCommand,
    IXFMemberListFromClientsCommand,
    InitScenarioCommand,
    CheckNewRelease
]

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

class ARouteServerError(Exception):

    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.please_open_issue = False
        self._extra_info = None
        self.traceback = None

    @property
    def extra_info(self):
        return self._extra_info

class ConfigError(ARouteServerError):
    pass

class MissingArgumentError(ARouteServerError):

    def __init__(self, arg):
        ARouteServerError.__init__(self)
        self.arg = arg

    def __str__(self):
        return "Missing argument: {}".format(self.arg)

class MissingFileError(ARouteServerError):

    def __init__(self, path):
        ARouteServerError.__init__(self)
        self.path = path

    def __str__(self):
        return "The file {} does not exist".format(self.path)

class MissingDirError(ARouteServerError):

    def __init__(self, path):
        ARouteServerError.__init__(self)
        self.path = path

    def __str__(self):
        return "The directory {} does not exist".format(self.path)

class CachedObjectsError(ARouteServerError):
    pass

class IRRDBToolsError(ARouteServerError):
    pass

class PeeringDBError(ARouteServerError):
    pass

class PeeringDBNoInfoError(ARouteServerError):
    pass

class EuroIXError(ARouteServerError):
    pass

class EuroIXSchemaError(EuroIXError):

    def __init__(self, msg):
        EuroIXError.__init__(self, msg)
        self._extra_info = ("It's possible that the JSON schema used by the IX "
                            "to export its members list is not aligned with "
                            "the one recognized by this version of the "
                            "program, or that it contains errors.")

class IXFDBError(ARouteServerError):
    pass

class IXFDBSchemaError(IXFDBError):

    def __init__(self, msg):
        IXFDBError.__init__(self, msg)
        self._extra_info = ("It's possible that the JSON schema used in the "
                            "IX-F database is not aligned with "
                            "the one recognized by this version of the "
                            "program, or that it contains errors.")

class BuilderError(ARouteServerError):
    pass

class CompatibilityIssuesError(BuilderError):

    @property
    def extra_info(self):
        return(
            "Please check the errors reported above for more details.\n"
            "To ignore those errors, use the '--ignore-issues' command "
            "line argument and list the IDs of the issues you want to "
            "ignore."
        )

class TemplateRenderingError(BuilderError):

    def __init__(self, msg, traceback=None, templates_not_aligned=False):
        BuilderError.__init__(self, msg)
        self.traceback = traceback
        self.please_open_issue = True
        self.templates_not_aligned = templates_not_aligned

    @property
    def extra_info(self):
        if self.templates_not_aligned:
            return("One or more template files are not "
                   "aligned with those distributed with the current "
                   "version of the program (maybe they need to be "
                   "updated after an upgrade), it's possible that this "
                   "issue is due to this reason.\n"
                   "Please consider running the "
                   "'arouteserver verify-templates' command and, if "
                   "suggested, to install the distributed version of the "
                   "templates.")

class ResourceNotFoundError(ARouteServerError):

    def __init__(self, err):
        ARouteServerError.__init__(self)
        self.err = err

    def __str__(self):
        return "Resource not found: {}".format(self.err)

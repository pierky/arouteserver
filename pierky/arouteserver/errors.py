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
    pass

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

class BuilderError(ARouteServerError):
    pass

class ResourceNotFoundError(ARouteServerError):

    def __init__(self, err):
        ARouteServerError.__init__(self)
        self.err = err

    def __str__(self):
        return "Resource not found: {}".format(self.err)

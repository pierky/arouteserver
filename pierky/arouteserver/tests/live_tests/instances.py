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


class InstanceError(Exception):
    pass

class InstanceNotRunning(InstanceError):
    def __init__(self, name, *args, **kwargs):
        InstanceError.__init__(self, *args, **kwargs)
        self.name = name

    def __str__(self):
        return "Instance '{}' is not running.".format(self.name)

class BGPSpeakerInstance(object):
    """This class abstracts a BGP speaker instance.

    Currently, the ``start``, ``stop``, ``is_running`` and
    ``run_cmd`` methods are implemented by the
    :class:`DockerInstance` derived class, while the ``reload_config``,
    ``bgp_session_is_up``, ``get_routes`` and ``log_contains`` by the
    DockerInstance-derived :class:`BIRDInstance` class.
    """

    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

    def set_var_dir(self, var_dir):
        self.var_dir = var_dir

    def is_running(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def reload_config(self):
        raise NotImplementedError()

    def run_cmd(self, args):
        raise NotImplementedError()

    def bgp_session_is_up(self, other_inst, force_update=False):
        """Check if a BGP session with ``other_inst`` is up.

        Args:
            other_inst: the
                :class:`BGPSpeakerInstance`
                instance that the current instance is expected to have a
                running BGP session with.

            force_update (bool): if True, the instance must bypass
                any caching mechanism used to keep the BGP sessions status.

        Returns:
            True if the current instance has a running BGP
            session with ``other_inst``; False otherwise.
        """
        raise NotImplementedError()

    def get_routes(self, prefix, include_filtered=False, only_best=False):
        """Get a list of all the known routes for ``prefix``.

        Args:
            prefix (str): the IP prefix that returned routes
                must match.

            include_filtered (bool): include filtered routes / rejected
                prefixes in the result.

            only_best (bool): include only the best route toward
                ``prefix``.

        Returns:
            list of :class:`Route` objects.
        """
        raise NotImplementedError()

    def log_contains(self, s):
        """Verifies if the BGP speaker's logs contain the expected message.

        Args:
            s (str): the message that is expected to be found in
                the BGP speaker's logs.

        Returns:
            True or False if the message is found or not.
        """
        raise NotImplementedError()

class Route(object):
    """Details about a route.

    Attributes:

        prefix (str): the IPv4/IPv6 prefix.

        via (str): the IP address of the peer from which the
            route has been received.

        as_path (str): the AS_PATH attribute of the route, in
            the "<asn> <asn> <asn>..." format (example: "1 2 345").

        next_hop (str): the NEXT_HOP attribute of the route.

        filtered (bool): True if the route has been rejected/filtered.

        std_comms (list): list of standard BGP communities (strings in
            the "x:y" format).

        lrg_comms (list): list of large BGP communities (strings in the
            "x:y:z" format).

        ext_comms (list): list of extended BGP communities (strings in
            the "[rt|ro]:x:y" format).
    """


    @staticmethod
    def _parse_bgp_communities(communities):
        if not communities:
            return []

        def parse_bgp_community(c):
            v = c
            if v.startswith("("):
                v = v[1:]
            if v.endswith(")"):
                v = v[:-1]
            return ":".join(
                [part.strip() for part in v.split(",")]
            )

        res = []
        for bgp_comm in communities.split(") ("):
            res.append(parse_bgp_community(bgp_comm))
        return res

    def __init__(self, prefix, **kwargs):
        self.prefix = prefix
        self.via = kwargs.get("via", None)
        self.as_path = kwargs.get("as_path", None)
        self.next_hop = kwargs.get("next_hop", None)
        self.filtered = kwargs.get("filtered", False)
        self.std_comms = self._parse_bgp_communities(kwargs.get("std_comms", None))
        self.lrg_comms = self._parse_bgp_communities(kwargs.get("lrg_comms", None))
        self.ext_comms = self._parse_bgp_communities(kwargs.get("ext_comms", None))

    def __str__(self):
        return str({
            "prefix": self.prefix,
            "via": self.via,
            "as_path": self.as_path,
            "next_hop": self.next_hop,
            "filtered": self.filtered,
            "std_comms": self.std_comms,
            "lrg_comms": self.lrg_comms,
            "ext_comms": self.ext_comms,
        })

    def __repr__(self):
        return self.__str__()

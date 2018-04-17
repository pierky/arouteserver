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


import os
import sys

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
    :class:`DockerInstance` and :class:`KVMInstance` derived classes,
    while the ``restart``, ``reload_config``, ``get_bgp_session``,
    ``get_routes`` and ``log_contains`` methods by the
    [Docker|KVM]Instance-derived :class:`BIRDInstance` and
    :class:`OpenBGPDInstance` classes.
    """

    MESSAGE_LOGGING_SUPPORT = True

    DEBUG = False

    @classmethod
    def debug(cls, s):
        if cls.DEBUG or "DEBUG" in os.environ:
            sys.stderr.write("DEBUG: {}\n".format(s))

    def __init__(self, name, ip, mount=[], **kwargs):
        self.name = name
        self.ip = ip
        self.mount = mount

    def set_var_dir(self, var_dir):
        self.var_dir = var_dir

    def get_mounts(self):
        for mount in self.mount:
            res = {}
            res["host"] = mount[0]
            res["container"] = mount[1]
            res["host_filename"] = os.path.split(mount[0])[1]
            res["var_path"] = "{}/{}".format(self.var_dir,
                                             res["host_filename"])
            yield res

    def is_running(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()

    def reload_config(self):
        raise NotImplementedError()

    def run_cmd(self, args):
        raise NotImplementedError()

    def get_bgp_session(self, other_inst, force_update=False):
        """Get information about the BGP session with ``other_inst``.

        Args:
            other_inst: the
                :class:`BGPSpeakerInstance`
                instance that the current instance is expected to have a
                running BGP session with.

            force_update (bool): if True, the instance must bypass
                any caching mechanism used to keep the BGP sessions status.

        Returns:
            None if the BGP session is not found, otherwise a dictionary
            containing information about the BGP session:

            - "ip": "neighbor IP address",
            - "is_up": [True|False]
        """
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
        bgp_session_info = self.get_bgp_session(other_inst, force_update)
        if bgp_session_info:
            return bgp_session_info["is_up"]
        raise Exception(
            "Can't get BGP session status for {} on {} "
            "(looking for {})".format(
                other_inst.name, self.name, other_inst.ip
            )
        )

    def get_routes(self, prefix, include_filtered=False, only_best=False):
        """Get a list of all the known routes for ``prefix``.

        Args:
            prefix (str): the IP prefix that returned routes
                must match. If None, all the routes are returned.

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

    def log_contains_errors(self, allowed_errors=[], list_errors=False):
        """Returns True if the BGP speaker's log contains warning/errors.

        Args:
            allowed_errors (list): list of strings representing errors
                that are allowed to be found within the BGP speaker's log.

            list_errors (bool): when set to True, the functions returns
                a touple (errors_found, list_of_errors).

        Returns:
            When ``list_errors`` is False: True of False if error messages
            or warnings are found within the BGP speaker's logs.
            When ``list_errors`` is True, a touple (bool, str).
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

        localpref (int): local-pref.

        reject_reasons (list): list of integers that identify the reasons
            for which the route is considered to be rejected.
    """

    def _parse_bgp_communities(self, communities):
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

    def _parse_std_bgp_communities(self, communities):
        return self._parse_bgp_communities(communities)

    def _parse_ext_bgp_communities(self, communities):
        return self._parse_bgp_communities(communities)

    def _parse_lrg_bgp_communities(self, communities):
        return self._parse_bgp_communities(communities)

    def __init__(self, prefix, **kwargs):
        self.prefix = prefix
        self.via = kwargs.get("via", None)
        self.as_path = kwargs.get("as_path", None)
        self.next_hop = kwargs.get("next_hop", None)
        self.localpref = kwargs.get("localpref", None)
        if self.localpref:
            self.localpref = int(self.localpref)
        self.filtered = kwargs.get("filtered", False)
        self.best = kwargs.get("best", None)
        self.std_comms = self._parse_std_bgp_communities(kwargs.get("std_comms", None))
        self.lrg_comms = self._parse_lrg_bgp_communities(kwargs.get("lrg_comms", None))
        self.ext_comms = self._parse_ext_bgp_communities(kwargs.get("ext_comms", None))
        self.reject_reasons = []

    def process_reject_cause(self, re_pattern, announced_by_pattern):
        # If a route is marked to be rejected using the 'reject_cause'
        # community it must be also set with LOCAL_PREF == 0.
        if self.localpref != 1:
            return

        reject_cause_zero_found = False
        reasons = []

        # Iterating over the original list (from which the 'reject_cause'
        # community will be removed) and its copy (to keep consistent the
        # set of values over which iterate).
        # Looking for reject reason community.
        for orig_list, dup_list in [(self.std_comms, list(self.std_comms)),
                                    (self.lrg_comms, list(self.lrg_comms)),
                                    (self.ext_comms, list(self.ext_comms))]:
            for comm in dup_list:
                match = re_pattern.match(comm)

                if not match:
                    continue

                reason = int(match.group(1))

                if reason == 0:
                    reject_cause_zero_found = True
                else:
                    reasons.append(reason)

                orig_list.remove(comm)

        if reject_cause_zero_found and announced_by_pattern:
            self.reject_reasons = reasons
            self.filtered = True

            # Looking for rejected_route_announce_by community.
            for orig_list, dup_list in [(self.std_comms, list(self.std_comms)),
                                        (self.lrg_comms, list(self.lrg_comms)),
                                        (self.ext_comms, list(self.ext_comms))]:
                for comm in dup_list:
                    match = announced_by_pattern.match(comm)

                    if match:
                        orig_list.remove(comm)
                        return

    def to_dict(self):
        return {
            "prefix": self.prefix,
            "via": self.via,
            "as_path": self.as_path,
            "next_hop": self.next_hop,
            "localpref": self.localpref,
            "filtered": self.filtered,
            "reject_reasons": ", ".join(map(str, sorted(self.reject_reasons))),
            "best": self.best,
            "std_comms": ", ".join(sorted(self.std_comms)),
            "lrg_comms": ", ".join(sorted(self.lrg_comms)),
            "ext_comms": ", ".join(sorted(self.ext_comms)),
        }

    def dump(self, f):
        s = (
            "{prefix}, AS_PATH: {as_path}, NEXT_HOP: {next_hop}, via {via}\n"
            "  std comms: {std_comms}\n"
            "  ext comms: {ext_comms}\n"
            "  lrg comms: {lrg_comms}\n"
            "  best: {best}, LOCAL_PREF: {localpref}\n"
            "  filtered: {filtered} ({reject_reasons})\n".format(
                **self.to_dict()
            )
        )
        for line in s.split("\n"):
            f.write(line.rstrip() + "\n")

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()

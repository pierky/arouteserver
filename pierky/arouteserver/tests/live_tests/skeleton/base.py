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

from pierky.arouteserver.tests.live_tests.base import LiveScenario
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4, \
                                                      BIRDInstanceIPv6
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPD60Instance, \
                                                          OpenBGPD61Instance

# -----------------------------------------------------------------------
# FULL DOCUMENTATION ON
#
# https://arouteserver.readthedocs.io/en/latest/LIVETESTS.html#how-to-build-custom-scenarios
# -----------------------------------------------------------------------

class SkeletonScenario(LiveScenario):
    """The base class that describes your scenario.

    A multi level structure of parent/child classes allows to decuple
    test functions (that is, the scenario expectations) from the BGP
    speakers configuration and IP addresses and prefixes that are used
    to build the scenario.

    The example structure looks like the following:

    - base.py: a base class (this one) where test functions are implemented
      in an IP version independent way;

    - test_XXX.py: BGP speaker specific and IP version specific
      classes where the real IP addresses and prefixes are provided
      in a dictionary made of ``prefix_ID: real_IP_prefix`` entries.

    If it's needed by the scenario, the derived classes must also fill the
    ``AS_SET`` and ``R_SET`` dictionaries with the expected content of any
    expanded AS-SETs used in IRRDB validation:

    - ``AS_SET``'s items must be in the format
      ``<AS_SET_name>: <list_of_authorized_origin_ASNs>``.

    - ``R_SET``'s items must be in the format
      ``<AS_SET_name>: <list_of_authorized_prefix_IDs>`` (where prefix
      IDs are those reported in the ``DATA`` dictionary).

    Example::

      AS_SET = {
          "AS-AS1": [1],
          "AS-AS1_CUSTOMERS": [101],
          "AS-AS2": [2],
          "AS-AS2_CUSTOMERS": [101]
      }
      R_SET = {
          "AS-AS1": [
              "AS1_allowed_prefixes"
          ],
          "AS-AS1_CUSTOMERS": [
              "AS101_prefixes"
          ]
      }

    Finally, this class must implement all the tests that are shared between
    the IPv4 and the IPv6 version of this scenario.

    Writing test functions
    ----------------------

    Test functions names must start with "test_"; tests are processed in
    alphabetical order; each test is independent from the others.

    Some helper functions can be used to define expectations.

    - ``self.session_is_up()``: test if a BGP session between the two
        instances is up.

        Details here (URL wraps):

        http://arouteserver.readthedocs.io/en/latest/LIVETESTS_CODEDOC.html#
        pierky.arouteserver.tests.live_tests.base.LiveScenario.session_is_up

    - ``self.receive_route()``: test if the BGP speaker receives the expected
        route(s).

        Details here (URL wraps):

        http://arouteserver.readthedocs.io/en/latest/LIVETESTS_CODEDOC.html#
        pierky.arouteserver.tests.live_tests.base.LiveScenario.receive_route


    - ``self.log_contains()``: test if the BGP speaker's log contains the
        expected message.

        Details here (URL wraps):

        http://arouteserver.readthedocs.io/en/latest/LIVETESTS_CODEDOC.html#
        pierky.arouteserver.tests.live_tests.base.LiveScenario.log_contains
    """

    # Leave this to False to avoid nose to use this abstract class to run
    # tests. Only derived, more specific classes (test_XXX.py) must have
    # this set to True.
    __test__ = False

    # This allows to use files and directories paths which are relative
    # to this scenario root directory.
    MODULE_PATH = __file__

    # The following attributes must be setted in derived classes.
    CONFIG_BUILDER_CLASS = None
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    IP_VER = None

    # If needed for IRRDB validation, fill this dictionary with pairs
    # in the format "<AS_SET_name>": [<list_of_authorized_origin_ASNs>].
    # See the example in the class docstring above.
    AS_SET = {
    }

    # If needed for IRRDB validation, fill this dictionary with pairs
    # in the format "<AS_SET_name>": [<list_of_authorized_prefix_IDs>].
    # See the example in the class docstring above.
    R_SET = {
    }

    @classmethod
    def _setup_instances(cls):
        """Declare the BGP speaker instances that are used in this scenario.

        The ``cls.INSTANCES`` attribute is a list of all the instances that
        are used in this scenario. It is used to render local Jinja2 templates
        and to transform them into real BGP speaker configuration files.

        The ``cls.RS_INSTANCE_CLASS`` and ``cls.CLIENT_INSTANCE_CLASS``
        attributes are set by the derived classes (test_XXX.py) and
        represent the route server class and the other BGP speakers class
        respectively.

        - The first argument is the instance name.

        - The second argument is the IP address that is used to run the
          instance. Here, the ``cls.DATA`` dictionary is used to lookup the
          real IP address to use, which is configured in the derived classes
          (test_XXX.py).

        - The third argument is a list of files that are mounted from the local
          host (where Docker is running) to the container (the BGP speaker).
          The list is made of pairs in the form
          ``(local_file, container_file)``.
          The ``cls.build_rs_cfg`` and ``cls.build_other_cfg`` helper functions
          allow to render Jinja2 templates and to obtain the path of the local
          output files.

          For the route server, the configuration is built using ARouteServer's
          library on the basis of the options given in the YAML files.

          For the other BGP speakers, the configuration must be provided in the
          Jinja2 files within the scenario directory.
        """

        cls.INSTANCES = [
            cls._setup_rs_instance(),

            cls.CLIENT_INSTANCE_CLASS(
                "AS1",
                cls.DATA["AS1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS1.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS2",
                cls.DATA["AS2_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS2.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            )
        ]

    @classmethod
    def _setup_rs_instance(cls):
        if cls.RS_INSTANCE_CLASS is OpenBGPD60Instance:
            return cls.RS_INSTANCE_CLASS(
                "rs",
                cls.DATA["rs_IPAddress"],
                [
                    (
                        cls.build_rs_cfg("openbgpd", "main.j2", "rs.conf", None,
                                         target_version="6.0"),
                        "/etc/bgpd.conf"
                    )
                ]
            )
        if cls.RS_INSTANCE_CLASS is OpenBGPD61Instance:
            return cls.RS_INSTANCE_CLASS(
                "rs",
                cls.DATA["rs_IPAddress"],
                [
                    (
                        cls.build_rs_cfg("openbgpd", "main.j2", "rs.conf", None,
                                         target_version="6.1"),
                        "/etc/bgpd.conf"
                    )
                ]
            )
        if cls.RS_INSTANCE_CLASS is BIRDInstanceIPv4 or \
            cls.RS_INSTANCE_CLASS is BIRDInstanceIPv6:
            return cls.RS_INSTANCE_CLASS(
                "rs",
                cls.DATA["rs_IPAddress"],
                [
                    (
                        cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER),
                        "/etc/bird/bird.conf"
                    )
                ]
            )
        raise NotImplementedError("RS_INSTANCE_CLASS unknown: {}".format(
            cls.RS_INSTANCE_CLASS.__name__))

    def set_instance_variables(self):
        """Simply set local attributes for an easier usage later
        
        The argument of ``self._get_instance_by_name()`` must be one of
        the instance names used in ``_setup_instances()``.
        """
        self.AS1 = self._get_instance_by_name("AS1")
        self.AS2 = self._get_instance_by_name("AS2")
        self.rs = self._get_instance_by_name("rs")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)

    def test_030_rs_receives_AS2_prefix(self):
        """{}: rs receives AS2 prefix"""
        self.receive_route(self.rs, self.DATA["AS2_prefix1"],
                           other_inst=self.AS2, as_path="2")

    def test_030_rs_rejects_bogon(self):
        """{}: rs rejects bogon prefix"""
        self.log_contains(self.rs,
                          "prefix is bogon - REJECTING {}".format(
                              self.DATA["AS2_bogon1"]))
        self.receive_route(self.rs, self.DATA["AS2_bogon1"],
                           other_inst=self.AS2, as_path="2",
                           filtered=True)
        # AS1 should not receive the bogon prefix from the route server
        with self.assertRaisesRegexp(AssertionError, "Routes not found"):
            self.receive_route(self.AS1, self.DATA["AS2_bogon1"])

    def test_030_custom_test(self):
        """{}: custom test"""

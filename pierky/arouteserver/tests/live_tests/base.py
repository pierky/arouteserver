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

from jinja2 import Environment, FileSystemLoader
import os
import re
import time
import yaml

from .docker import InstanceError

from pierky.arouteserver.ipaddresses import IPAddress, IPNetwork
from pierky.arouteserver.tests.base import ARouteServerTestCase
from pierky.arouteserver.tests.mocked_env import MockedEnv
from pierky.arouteserver.tests.live_tests.instances import BGPSpeakerInstance
from pierky.arouteserver.tests.live_tests.bird import BIRDInstanceIPv4, \
                                                      BIRDInstanceIPv6
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPD60Instance, \
                                                          OpenBGPD61Instance, \
                                                          OpenBGPD62Instance, \
                                                          OpenBGPD63Instance


class LiveScenario(ARouteServerTestCase):
    """An helper class to run tests for a given scenario.

    This class must be derived by scenario-specific classes that
    must:

    - set the ``MODULE_PATH`` attribute to ``__file__``, in order
      to correctly locate files needed by the scenario.

    - fill the ``INSTANCES`` list with a list of
      :class:`BGPSpeakerInstance`
      (or derived) instances representing all the BGP speakers involved in the
      scenario.

    - set the ``SHORT_DESCR`` with a short description of the
      scenario; it will be used to print tests description in the
      format "<SHORT_DESCR>: <test function docstring>".

    - fill the ``DATA`` dictionary with IP prefixes IDs that
      represent all the IP addresses used by the scenario; this
      is useful to decouple real IP addresses from what they
      represent or are used to and to have a single definition
      of the tests functions and scenario configuration that can
      be used for both IPv4 and IPv6 tests.

      Example::

        DATA = {
            "rs_IPAddress": "192.0.2.2",
            "AS1_IPAddress": "192.0.2.11",
            "AS1_allowed_prefixes": "1.0.0.0/8",
            "AS1_good_prefix": "1.0.1.0/24",
            "AS101_prefixes": "101.0.0.0/8"
        }

    - optionally, if it's needed by the scenario, the derived classes
      must also fill the ``AS_SET`` and ``R_SET`` dictionaries with
      the expected content of any expanded AS-SETs used in IRRDB
      validation:

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

    - optionally, if it's needed by the scenario, the derived classes
      can also set the ``RTT`` dictionary with the values of the RTTs
      of the clients. Keys can be IP addresses of clients or the
      prefix IDs used in the ``DATA`` dictionary to represent them.

      Example::

        RTT = {
            "192.0.2.11": 14,
            "2001:db8::11": 165,
            "AS1_IPAddress": 44
        }

    - optionally, if it's needed by the scenario, the derived classes
      can also set the ``REJECT_CAUSE_COMMUNITY`` attribute with the
      pattern followed by BGP communities used to tag routes that are
      considered to be rejected (see the ``filtering.reject_policy``
      general configuration section and the ``reject_cause``
      community).
      The value of this attribute must be a regular expression that
      matches the standard, extended or large BGP communities used to
      tag invalid routes. For example, if the standard BGP community
      ``65520:dyn_val`` is used, the value must be ``^65520:(\d+)$``.
      If this attribute is not None, routes that have LOCAL_PREF == 1
      and the ``reject_cause`` BGP community with ``dyn_val == 0``
      are considered as filtered.
      The ``REJECTED_ROUTE_ANNOUNCED_BY_COMMUNITY`` attribute can also
      be set to match the community used to track the announcing ASN of
      invalid routes.

    - implement the ``set_instance_variables`` method, used to set
      local instance attributes for the instances used within the
      tests functions.

      Example::

        def set_instance_variables(self):
            self.AS1 = self._get_instance_by_name("AS1")
            self.AS2 = self._get_instance_by_name("AS2")
            self.AS131073 = self._get_instance_by_name("AS131073")
            self.rs = self._get_instance_by_name("rs")

    Set the ``__test__`` attribute of derived classes to False to avoid them
    to be used directly by ``nose`` to run tests; only the specific IPv4/IPv6
    class (the one where the ``DATA`` dictionary is set) must have
    ``__test__`` == True.
    """

    MODULE_PATH = None
    SHORT_DESCR = ""

    DATA = {}
    AS_SET = {}
    R_SET = {}
    RTT = {}
    INSTANCES = []

    DEBUG = False
    DO_NOT_STOP_INSTANCES = False

    CONFIG_BUILDER_CLASS = None

    MOCK_PEERING_DB = True
    MOCK_RIPE_RPKI_CACHE = True
    MOCK_IRRDB = True
    MOCK_RTTGETTER = True
    MOCK_ARIN_DB_DUMP = True

    # regex: for example ^65520:(\d+)$
    REJECT_CAUSE_COMMUNITY = None
    REJECTED_ROUTE_ANNOUNCED_BY_COMMUNITY = None

    ALLOWED_LOG_ERRORS = []

    @classmethod
    def _get_module_dir(cls):
        return os.path.dirname(cls.MODULE_PATH)

    @classmethod
    def _get_local_file_path(cls, filename):
        return os.path.join(cls._get_module_dir(), filename)

    @classmethod
    def _get_instance_by_name(cls, name):
        for instance in cls.INSTANCES:
            if instance.name == name:
                return instance
        raise Exception("Instance not found: {}.".format(name))

    @classmethod
    def _create_var_dir(cls):
        var_dir = "{}/var".format(cls._get_module_dir())
        if not os.path.exists(var_dir):
            os.mkdir(var_dir)
        return var_dir

    @classmethod
    def _do_not_stop_instances(cls):
        return cls.DO_NOT_STOP_INSTANCES or "REUSE_INSTANCES" in os.environ

    @classmethod
    def build_other_cfg(cls, tpl_name):
        """Builds configuration files for BGP speakers which are not the route server.

        Args:
            tpl_name (str): the name of the Jinja2 template file
                relative to the scenario directory.

        Returns:
            the path of the local rendered file.

        To render the template, one attribute is used and consumed by Jinja2:

        - ``data``, the scenario's ``DATA`` dictionary.

        The resulting file is saved into the local ``var`` directory
        and its absolute path is returned.
        """
        cls.debug("Building config from {}/{}".format(
            cls._get_module_dir(), tpl_name))

        env = Environment(
            loader=FileSystemLoader(cls._get_module_dir()),
            trim_blocks=True,
            lstrip_blocks=True
        )
        tpl = env.get_template(tpl_name)
        cfg = tpl.render(data=cls.DATA)

        var_dir = cls._create_var_dir()
        cfg_file_path = "{}/{}.config".format(var_dir, tpl_name)

        with open(cfg_file_path, "w") as f:
            f.write(cfg)

        return cfg_file_path

    @classmethod
    def _get_cfg_general(cls, filename=None):
        return filename or "general.yml"

    @classmethod
    def build_rs_cfg(cls, tpl_dir_name, tpl_name, out_file_name, ip_ver,
                      cfg_general=None, cfg_bogons="bogons.yml",
                      cfg_clients="clients.yml", **kwargs):
        """Builds configuration file for the route server.

        Args:
            tpl_dir_name (str): the directory where Jinja2
                templates are located, relative to the current scenario.

            tpl_name (str): the name of the template to be
                rendered.

            out_file_name (str): the name of the destination
                file.

            ip_ver (int): the IP version for which this route server
                will operate. Use None if the configuration is valid
                for both IPv4 and IPv6.

            cfg_general (str), cfg_bogons (str), cfg_clients (str): the
                name of the 3 main files containing route server's
                options and policies, clients definition and bogons
                IP addresses. File names are relative to the scenario
                directory.

        Returns:
            the path of the local rendered file.

        The resulting file is saved into the local ``var`` directory
        and its absolute path is returned.
        """

        cls.debug("Building config from {}/{}".format(
            tpl_dir_name, tpl_name)
        )

        var_dir = cls._create_var_dir()

        builder = cls.CONFIG_BUILDER_CLASS(
            template_dir="{}/{}".format(cls._get_module_dir(), tpl_dir_name),
            template_name=tpl_name,
            cache_dir=var_dir,
            cfg_general="{}/{}".format(cls._get_module_dir(),
                                       cfg_general or cls._get_cfg_general()),
            cfg_bogons="{}/{}".format(cls._get_module_dir(), cfg_bogons),
            cfg_clients="{}/{}".format(cls._get_module_dir(), cfg_clients),
            ip_ver=ip_ver,
            ignore_errors=["*"],
            live_tests=True,
            **kwargs
        )

        cfg_file_path = "{}/{}".format(var_dir, out_file_name)

        with open(cfg_file_path, "w") as f:
            builder.render_template(f)

        cls.rs_cfg_file_path = cfg_file_path

        return cfg_file_path

    @classmethod
    def use_static_file(cls, local_filename):
        """Prepare the local file in order to use it later.

        Args:
            filename (str): the name of the local file,
                relative to the scenario directory.

        Returns:
            the path of the file to be used
        """

        var_dir = cls._create_var_dir()
        var_path = os.path.join(var_dir, local_filename)
        local_path = os.path.join(cls._get_module_dir(), local_filename)
        with open(local_path, "r") as src:
            with open(var_path, "w") as dst:
                dst.write(src.read())
        return var_path

    @classmethod
    def _setUpClass(cls):
        for prefix_name in cls.DATA:
            prefix = cls.DATA[prefix_name]
            net = IPNetwork(prefix) if "/" in prefix else IPAddress(prefix)
            if str(net) != prefix:
                raise ValueError(
                    "Prefix '{}' is not represented in its canonical form: "
                    "'{}' used, '{}' expected.".format(
                        prefix_name, prefix, str(net)
                    )
                )

        cls.info("{}: setting instances up...".format(cls.SHORT_DESCR))

        MockedEnv(cls, base_dir=cls._get_module_dir(),
                  peering_db=cls.MOCK_PEERING_DB,
                  ripe_rpki_cache=cls.MOCK_RIPE_RPKI_CACHE,
                  irrdb=cls.MOCK_IRRDB,
                  rttgetter=cls.MOCK_RTTGETTER,
                  arin_db_dump=cls.MOCK_ARIN_DB_DUMP)

        cls.rs_cfg_file_path = None

        try:
            cls._setup_instances()
        except:
            cls.tearDownClass()
            raise

        if "BUILD_ONLY" in os.environ or \
            (cls.SKIP_ON_TRAVIS and "TRAVIS" in os.environ):
            cls.debug("Skipping starting instances")
            return

        try:
            for instance in cls.INSTANCES:
                instance.set_var_dir("{}/var".format(cls._get_module_dir()))

                if cls._do_not_stop_instances() and instance.is_running():
                    cls.debug("Instance '{}' already running, reloading config".format(instance.name))
                    if not instance.reload_config():
                        raise InstanceError("An error occurred while reloading '{}' configuration.".format(instance.name))
                    continue

                cls.debug("Starting instance '{}'...".format(instance.name))
                instance.start()
        except:
            cls.tearDownClass()
            raise

    @staticmethod
    def get_instance_tag(instance_or_class):
        if isinstance(instance_or_class, BGPSpeakerInstance):
            _class = instance_or_class.__class__
        else:
            _class = instance_or_class

        if _class is BIRDInstanceIPv4 or \
            _class is BIRDInstanceIPv6:
            tag = "bird16"
        elif _class is OpenBGPD60Instance:
            tag = "openbgpd60"
        elif _class is OpenBGPD61Instance:
            tag = "openbgpd61"
        elif _class is OpenBGPD62Instance:
            tag = "openbgpd62"
        elif _class is OpenBGPD63Instance:
            tag = "openbgpd63"
        else:
            msg = "Unknown instance type: "
            if isinstance(instance_or_class, BGPSpeakerInstance):
                msg += instance_or_class.name
            else:
                msg += instance_or_class.__name__
            raise ValueError(msg)

        return tag

    @classmethod
    def dump_routes(cls):
        rs_tag = cls.get_instance_tag(cls.RS_INSTANCE_CLASS)

        dest_dir = os.path.join(cls._get_module_dir(), "routes", cls.__name__, rs_tag)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        for instance in cls.INSTANCES:
            path = os.path.join(dest_dir, "{}.txt".format(instance.name))
            routes = instance.get_routes(None, include_filtered=True)
            sorted_routes = sorted(routes,
                                   key = lambda route: (route.prefix,
                                                        route.as_path,
                                                        route.next_hop,
                                                        route.via))
            with open(path, "w") as f:
                for route in sorted_routes:
                    route.dump(f)

    @classmethod
    def dump_rs_config(cls):
        if not cls.rs_cfg_file_path:
            return

        dest_dir = os.path.join(cls._get_module_dir(), "configs", cls.__name__)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        tag = cls.get_instance_tag(cls.RS_INSTANCE_CLASS)

        path = os.path.join(dest_dir, "{}.conf".format(tag))
        with open(path, "w") as dst:
            with open(cls.rs_cfg_file_path, "r") as src:
                dst.write(src.read())

    @classmethod
    def _tearDownClass(cls):
        MockedEnv.stopall()

        if "TRAVIS" not in os.environ:
            cls.info("{}: dumping rs config...".format(cls.SHORT_DESCR))
            cls.dump_rs_config()

        if "BUILD_ONLY" in os.environ or \
            (cls.SKIP_ON_TRAVIS and "TRAVIS" in os.environ):
            cls.debug("Skipping stopping instances")
            return

        if "TRAVIS" not in os.environ:
            cls.info("{}: dumping routes...".format(cls.SHORT_DESCR))
            cls.dump_routes()

        if cls._do_not_stop_instances():
            cls.debug("Skipping stopping instances")
            return

        cls.info("{}: stopping instances...".format(cls.SHORT_DESCR))

        for instance in cls.INSTANCES:
            cls.debug("Stopping instance '{}'...".format(instance.name))
            instance.stop()

    def set_instance_variables(self):
        raise NotImplementedError()

    def _setUp(self):
        if "BUILD_ONLY" in os.environ:
            self.skipTest("Build only")

        if self.SKIP_ON_TRAVIS and "TRAVIS" in os.environ:
            self.skipTest("not supported on Travis CI")

        self.set_instance_variables()

    def process_reject_cause_routes(self, routes):
        if self.REJECT_CAUSE_COMMUNITY is not None:
            re_pattern = re.compile(self.REJECT_CAUSE_COMMUNITY)
            rejected_route_announced_by_pattern = None
            if self.REJECTED_ROUTE_ANNOUNCED_BY_COMMUNITY:
                rejected_route_announced_by_pattern = \
                    re.compile(self.REJECTED_ROUTE_ANNOUNCED_BY_COMMUNITY)

            for route in routes:
                route.process_reject_cause(re_pattern,
                                           rejected_route_announced_by_pattern)

    def _instance_log_contains_errors_warning(self, inst):
        if inst.log_contains_errors(self.ALLOWED_LOG_ERRORS):
            return "\nWARNING: {} log contains errors".format(inst.name)
        return ""

    def receive_route(self, inst, prefix, other_inst=None, as_path=None,
                      next_hop=None, std_comms=None, lrg_comms=None,
                      ext_comms=None, local_pref=None,
                      filtered=None, only_best=None, reject_reason=None):
        """Test if the BGP speaker receives the expected route(s).

        If no routes matching the given criteria are found, the
        ``TestCase.fail()`` method is called and the test fails.

        Args:
            inst: the :class:`BGPSpeakerInstance` instance where the routes
                are searched on.

            prefix (str): the IPv4/IPv6 prefix of the routes to search for.

            other_inst: if given, only routes received from this
                :class:`BGPSpeakerInstance` instance are considered.

            as_path (str): if given, only routes with this AS_PATH are
                considered.

            next_hop: can be a string or a :class:`BGPSpeakerInstance`
                instance; if given, only routes that have a NEXT_HOP
                address matching this one are considered.

            std_comms, lrg_comms, ext_comms (list): if given, only routes
                that carry these BGP communities are considered. Use an
                empty list ([]) to consider only routes with no BGP comms.

            local_pref (int): if given, only routes with local-pref equal
                to this value are considered.

            filtered (bool): if given, only routes that have been (not)
                filtered are considered.

            only_best (bool): if given, only best routes are considered.

            reject_reason (int): valid only if `filtered` is True: if given
                the route must be reject with this reason code.
                It can be also a set of codes: in this case, the route must
                be rejected with one of those codes.

                The list of valid codes is reported in docs/CONFIG.rst or at
                https://arouteserver.readthedocs.io/en/latest/CONFIG.html#reject-policy
        """
        assert isinstance(inst, BGPSpeakerInstance), \
            "inst must be of class BGPSpeakerInstance"

        try:
            IPNetwork(prefix)
        except:
            raise AssertionError("prefix must be a valid IPv4/IPv6 prefix")

        if other_inst:
            assert isinstance(other_inst, BGPSpeakerInstance), \
                "other_inst must be of class BGPSpeakerInstance"

        if as_path:
            try:
                if not isinstance(as_path, str):
                    raise AssertionError()
                for asn in as_path.split(" "):
                    assert asn.strip().isdigit()
            except:
                raise AssertionError("as_path must be a string in the format "
                                     "'<asn1> <asn2>' with <asnX> positive "
                                     "integers")

        next_hop_ip = None
        if next_hop:
            assert isinstance(next_hop, (str, BGPSpeakerInstance)), \
                ("next_hop must be a string representing one IP address or "
                 "a BGPSpeakerInstance object")
            next_hop_ip = next_hop if isinstance(next_hop, str) else next_hop.ip
            try:
                IPAddress(next_hop_ip)
            except:
                raise AssertionError("Invalid next_hop IP address: {}".format(
                    next_hop_ip
                ))

        if std_comms:
            assert isinstance(std_comms, list), \
                ("std_comms must be a list of strings representing "
                 "BGP standard communities")

        if ext_comms:
            assert isinstance(ext_comms, list), \
                ("ext_comms must be a list of strings representing "
                 "BGP extended communities")

        if lrg_comms:
            assert isinstance(lrg_comms, list), \
                ("lrg_comms must be a list of strings representing "
                 "BGP large communities")

        if local_pref:
            assert isinstance(local_pref, int), \
                "local_pref must be an integer >= 0"
            assert local_pref >= 0, \
                "local_pref must be an integer >= 0"

        if reject_reason is not None and not filtered:
            raise AssertionError(
                "reject_reason can be set only if filtered is True"
            )

        reject_reasons = None
        if reject_reason is not None:
            if isinstance(reject_reason, int):
                reject_reasons = [reject_reason]
            else:
                reject_reasons = list(reject_reason)
            for code in reject_reasons:
                assert code in range(1,15), "invalid reject_reason"

        include_filtered = filtered if filtered is not None else False
        best_only = only_best if only_best is not None else False

        routes = inst.get_routes(prefix,
                                 include_filtered=include_filtered,
                                 only_best=best_only)
        self.process_reject_cause_routes(routes)

        errors = []
        if not routes:
            errors.append("{inst} does not receive {prefix} at all.")
        else:
            for route in routes:
                err = False
                if other_inst and route.via != other_inst.ip:
                    errors.append("{{inst}} receives {{prefix}} from {via} and not from {{other_inst}}.".format(via=route.via))
                    err = True
                if as_path and route.as_path != as_path:
                    errors.append("{{inst}} receives {{prefix}} with AS_PATH {as_path} and not with {{as_path}}.".format(as_path=route.as_path))
                    err = True
                if next_hop_ip and route.next_hop != next_hop_ip:
                    errors.append("{{inst}} receives {{prefix}} with NEXT_HOP {next_hop} and not with {{next_hop_ip}}.".format(next_hop=route.next_hop))
                    err = True
                if std_comms is not None and sorted(route.std_comms) != sorted(std_comms):
                    errors.append("{{inst}} receives {{prefix}} with std comms {comms} and not with {{std_comms}}.".format(comms=route.std_comms))
                    err = True
                if lrg_comms is not None and sorted(route.lrg_comms) != sorted(lrg_comms):
                    errors.append("{{inst}} receives {{prefix}} with lrg comms {comms} and not with {{lrg_comms}}.".format(comms=route.lrg_comms))
                    err = True
                if ext_comms is not None and sorted(route.ext_comms) != sorted(ext_comms):
                    errors.append("{{inst}} receives {{prefix}} with ext comms {comms} and not with {{ext_comms}}.".format(comms=route.ext_comms))
                    err = True
                if local_pref is not None and route.localpref != local_pref:
                    errors.append("{{inst}} receives {{prefix}} with local-pref {local_pref} and not with {{local_pref}}.".format(local_pref=route.localpref))
                    err = True
                if filtered is not None and route.filtered != filtered:
                    errors.append(
                        "{{inst}} receives {{prefix}} from {via}, AS_PATH {as_path}, NEXT_HOP {next_hop} "
                        "but it is {filtered_status} while it is expected to be {filtered_exp}.".format(
                            via=route.via,
                            as_path=route.as_path,
                            next_hop=route.next_hop,
                            filtered_status="filtered" if route.filtered else "not filtered",
                            filtered_exp="filtered" if filtered else "not filtered"
                        )
                    )
                    err = True
                if filtered is True and route.filtered and \
                    reject_reasons is not None and len(route.reject_reasons) > 0:

                    reject_reason_found = False
                    for real_reason in route.reject_reasons:
                        if real_reason in reject_reasons:
                            reject_reason_found = True

                    if not reject_reason_found:
                        if len(reject_reasons) == 1:
                            exp_reason = reject_reasons[0]
                        else:
                            exp_reason = "one of {}".format(", ".join(map(str, reject_reasons)))

                        errors.append(
                            "{{inst}} receives {{prefix}} from {via}, AS_PATH {as_path}, NEXT_HOP {next_hop}, "
                            "it is filtered but reject reasons don't match: real reasons {reason}, "
                            "expected reason {exp_reason}.".format(
                                via=route.via,
                                as_path=route.as_path,
                                next_hop=route.next_hop,
                                reason=", ".join(map(str, route.reject_reasons)),
                                exp_reason=exp_reason
                            )
                        )
                        err = True
                if not err:
                    return route

        if errors:
            criteria = []
            if other_inst:
                criteria.append("from {} ({})".format(other_inst.ip, other_inst.name))
            if as_path:
                criteria.append("with AS_PATH {}".format(as_path))
            if next_hop_ip:
                criteria.append("with next-hop {}".format(next_hop_ip))
            if std_comms:
                criteria.append("with std comms {}".format(std_comms))
            if lrg_comms:
                criteria.append("with lrg comms {}".format(lrg_comms))
            if ext_comms:
                criteria.append("with ext comms {}".format(ext_comms))
            if local_pref:
                criteria.append("with local-pref {}".format(local_pref))
            if filtered is True:
                criteria.append("filtered")
            if reject_reasons:
                if len(reject_reasons) == 1:
                    criteria.append(
                        "with reject reason {}".format(reject_reasons[0])
                    )
                else:
                    criteria.append(
                        "with reject reason in {}".format(
                            ", ".join(map(str, reject_reasons))
                        )
                    )

            failure = "Routes not found.\n"
            failure += "Looking for {prefix} on {inst} {criteria}:\n\t".format(
                prefix=prefix,
                inst=inst.name,
                criteria=", ".join(criteria)
            )
            failure += "\n\t".join([
                err_msg.format(
                    inst=inst.name,
                    prefix=prefix,
                    other_inst="{} ({})".format(other_inst.ip, other_inst.name) if other_inst else "",
                    as_path=as_path,
                    next_hop_ip=next_hop_ip,
                    std_comms=std_comms,
                    lrg_comms=lrg_comms,
                    ext_comms=ext_comms,
                    local_pref=local_pref,
                ) for err_msg in errors
            ])
            failure += self._instance_log_contains_errors_warning(inst)
            self.fail(failure)

    def log_contains(self, inst, msg, instances={}):
        """Test if the BGP speaker's log contains the expected message.

        This only works for BGP speaker instances that support message
        logging: currently only BIRD.

        If no log entries are found, the ``TestCase.fail()`` method is
        called and the test fails.

        Args:

            inst: the :class:`BGPSpeakerInstance` instance where the
                expected message is searched on.

            msg (str): the text that is expected to be found within
                BGP speaker's log.

            instances (dict): a dictionary of pairs
                "<macro>: <BGPSpeakerInstance>" used to expand macros on
                the *msg* argument. Macros are expanded using the BGP
                speaker's specific client ID or protocol name.

        Example
        ---------

        Given *self.rs* the instance of the route server, and *self.AS1* the
        instance of one of its clients, the following code expands the "{AS1}"
        macro using the BGP speaker specific name for the instance *self.AS1*
        and then looks for it within the route server's log:

            ``self.log_contains(self.rs, "{AS1} bad ASN", {"AS1": self.AS1})``

        On BIRD, "{AS1}" will be expanded using the "protocol name" that BIRD
        uses to identify the BGP session with AS1.
        """
        if not inst.MESSAGE_LOGGING_SUPPORT:
            return

        expanded_msg = msg

        macros_dict = {}
        for inst_name in instances:
            other_inst = instances[inst_name]
            # BAD THING: using a BIRD specific method to understand
            # what's the other instance's name on 'inst'.
            proto_name = inst.get_protocol_name_by_ip(other_inst.ip)
            macros_dict[inst_name] = proto_name

        if macros_dict:
            expanded_msg = expanded_msg.format(**macros_dict)

        if not inst.log_contains(expanded_msg):
            self.fail(
                "Expected message not found on {} logs:\n\t{}".format(
                    inst.name, expanded_msg
                ) + self._instance_log_contains_errors_warning(inst)
            )

    def session_exists(self, inst_a, inst_b_or_ip):
        """Test if a BGP session between the two instances exists.

        Args:
            inst_a: the :class:`BGPSpeakerInstance` instance where the
                BGP session is looked for.

            inst_b_or_ip: the :class:`BGPSpeakerInstance` instance or an
                IP address that *inst_a* is expected to peer with.
        """

        if inst_a.get_bgp_session(inst_b_or_ip) is None:
            self.fail(
                "A BGP session between '{}' ({}) and '{}' "
                "does not exist.".format(
                    inst_a.name, inst_a.ip,
                    "{} ({})".format(
                        inst_b_or_ip.name, inst_b_or_ip.ip
                    ) if isinstance(inst_b_or_ip, BGPSpeakerInstance)
                    else inst_b_or_ip
                ) + self._instance_log_contains_errors_warning(inst_a)
            )

    def session_is_up(self, inst_a, inst_b):
        """Test if a BGP session between the two instances is up.

        If a BGP session between the two instances is not up, the
        ``TestCase.fail()`` method is called and the test fails.

        Args:
            inst_a: the :class:`BGPSpeakerInstance` instance where the
                BGP session is looked for.

            inst_b: the :class:`BGPSpeakerInstance` instance that *inst_a* is
                expected to peer with.
        """

        self.session_exists(inst_a, inst_b)

        for _ in range(5):
            if inst_a.bgp_session_is_up(inst_b):
                return
            time.sleep(1)
        for _ in range(20):
            if inst_a.bgp_session_is_up(inst_b, force_update=True):
                return
            time.sleep(1)
        self.fail(
            "BGP session between '{}' ({}) and '{}' ({}) is not up.".format(
                inst_a.name, inst_a.ip, inst_b.name, inst_b.ip
            ) + self._instance_log_contains_errors_warning(inst_a)
        )

    def test_010_setup(self):
        # Referenced by utils/update_tests, used when BUILD_ONLY=1
        raise NotImplementedError()

    def test_999_log_contains_errors(self):
        """{}: log contains errors"""
        try:
            errors_found, errors = self.rs.log_contains_errors(
                self.ALLOWED_LOG_ERRORS, True
            )
            if errors_found:
                self.fail("rs log contains errors:\n{}".format(errors))
        except AttributeError:
            raise NotImplementedError("self.rs does not exist here")
        except NotImplementedError:
            raise

class LiveScenario_TagRejectPolicy(object):
    """Helper class to run a scenario as if reject_policy is set to 'tag'.

    When a scenario inherits this class, its route server is configured as
    if the ``reject_policy.policy`` is ``tag``, the ``65520:dyn_val``
    value is used for the ``reject_cause`` BGP community and the
    ``rt:65520:dyn_val`` value for the ``rejected_route_announced_by`` one.

    The ``general.yml`` file, or the file given in the ``orig_file`` argument
    of ``_get_cfg_general`` method, is cloned and reconfigured with the
    aforementioned settings.

    This class is mostly used for OpenBGPD tests since the underlaying
    mechanism allows to track the reason that brought to consider the route as
    rejected and to test filters out during test cases execution.

    This class should be used in multiple inheritance:

    Example
    ---------

        ``class SkeletonScenario_OpenBGPDIPv4(LiveScenario_TagRejectPolicy, SkeletonScenario):``

    """

    REJECT_CAUSE_COMMUNITY = "^65520:(\d+)$"
    REJECTED_ROUTE_ANNOUNCED_BY_COMMUNITY = "^rt:65520:(\d+)$"

    @classmethod
    def _get_cfg_general(cls, orig_file="general.yml"):
        orig_path = "{}/{}".format(cls._get_module_dir(), orig_file)
        dest_rel_path = "var/general.yml"
        dest_path = "{}/{}".format(cls._get_module_dir(), dest_rel_path)

        with open(orig_path, "r") as f:
            cfg = yaml.safe_load(f.read())

        cfg["cfg"]["filtering"]["reject_policy"] = {"policy": "tag"}
        if "communities" not in cfg["cfg"]:
            cfg["cfg"]["communities"] = {}
        cfg["cfg"]["communities"]["reject_cause"] = {"std": "65520:dyn_val"}
        cfg["cfg"]["communities"]["rejected_route_announced_by"] = {"ext": "rt:65520:dyn_val"}

        with open(dest_path, "w") as f:
            yaml.safe_dump(cfg, f, default_flow_style=False)

        return dest_rel_path

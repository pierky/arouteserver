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

import ipaddr
from jinja2 import Environment, FileSystemLoader
import mock
import os
import time

from docker import InstanceError
from ..base import ARouteServerTestCase
from ..mock_peeringdb import mock_peering_db

from pierky.arouteserver.builder import BIRDConfigBuilder
from pierky.arouteserver.config.validators import ValidatorPrefixListEntry
from pierky.arouteserver.rpsl import ASSet, RSet


class LiveScenario(ARouteServerTestCase):

    MODULE_PATH = None
    SHORT_DESCR = ""

    IP_VER = None
    DATA = {}
    AS_SET = {}
    R_SET = {}
    INSTANCES = []

    DEBUG = False
    DO_NOT_STOP_INSTANCES = False

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder

    @classmethod
    def _get_module_dir(cls):
        return os.path.dirname(cls.MODULE_PATH)

    @classmethod
    def _get_instance_by_name(cls, name):
        for instance in cls.INSTANCES:
            if instance.name == name:
                return instance
        raise Exception("Instance not found: {}".format(name))

    @classmethod
    def _create_var_dir(cls):
        var_dir = "{}/var".format(cls._get_module_dir())
        try:
            os.mkdir(var_dir)
        except OSError:
            pass
        return var_dir

    @classmethod
    def _do_not_stop_instances(cls):
        return cls.DO_NOT_STOP_INSTANCES or "REUSE_INSTANCES" in os.environ

    @classmethod
    def _build_other_cfg(cls, tpl_name):
        cls.debug("Building config from {}/{} - IPv{}".format(
            cls._get_module_dir(), tpl_name, cls.IP_VER))

        env = Environment(
            loader=FileSystemLoader(cls._get_module_dir()),
            trim_blocks=True,
            lstrip_blocks=True
        )
        tpl = env.get_template(tpl_name)
        cfg = tpl.render(ip_ver=cls.IP_VER, data=cls.DATA)

        var_dir = cls._create_var_dir()
        cfg_file_path = "{}/{}.config".format(var_dir, tpl_name)

        with open(cfg_file_path, "w") as f:
            f.write(cfg)

        return cfg_file_path

    @classmethod
    def _build_rs_cfg(cls, tpl_dir_name, tpl_name, out_file_name,
                      cfg_general="general.yml", cfg_bogons="bogons.yml",
                      cfg_clients="clients.yml", cfg_roas=None):
        cls.debug("Building config from {}/{} - IPv{}".format(tpl_dir_name, tpl_name, cls.IP_VER))

        var_dir = cls._create_var_dir()

        builder = cls.CONFIG_BUILDER_CLASS(
            template_dir="{}/{}".format(cls._get_module_dir(), tpl_dir_name),
            template_name=tpl_name,
            cache_dir=var_dir,
            cfg_general="{}/{}".format(cls._get_module_dir(), cfg_general),
            cfg_bogons="{}/{}".format(cls._get_module_dir(), cfg_bogons),
            cfg_clients="{}/{}".format(cls._get_module_dir(), cfg_clients),
            cfg_roas="{}/{}".format(cls._get_module_dir(), cfg_roas) if cfg_roas else None,
            ip_ver=cls.IP_VER
        )

        cfg_file_path = "{}/{}".format(var_dir, out_file_name)

        cfg = builder.render_template()
        with open(cfg_file_path, "w") as f:
            f.write(cfg)

        return cfg_file_path

    @classmethod
    def mock_rpsl(cls):
        def _mock_load_data_from_cache(*args, **kwargs):
            return False

        def _mock_RSet__get_data(self):
    
            def add_prefix_to_list(prefix_name, lst):
                obj = ipaddr.IPNetwork(cls.DATA[prefix_name])
                lst.append(
                    ValidatorPrefixListEntry().validate({
                        "prefix": str(obj.ip),
                        "length": obj.prefixlen,
                        "comment": self.object_name
                    })
                )

            res = []

            if self.object_name in cls.R_SET:
                for prefix_name in cls.R_SET[self.object_name]:
                    add_prefix_to_list(prefix_name, res)
            return res

        def _mock_ASSet__get_data(self):
            if self.object_name in cls.AS_SET:
                return cls.AS_SET[self.object_name]

        mock_RPSLTools_load_data_from_cache = mock.patch.object(
            RSet, "load_data_from_cache"
        ).start()
        mock_RPSLTools_load_data_from_cache.side_effect = _mock_load_data_from_cache

        mock_ASSet__get_data = mock.patch.object(
            ASSet, "_get_data", autospec=True
        ).start()
        mock_ASSet__get_data.side_effect = _mock_ASSet__get_data

        mock_RSet__get_data = mock.patch.object(
            RSet, "_get_data", autospec=True
        ).start()
        mock_RSet__get_data.side_effect = _mock_RSet__get_data

    @classmethod
    def _setUpClass(cls):
        print("{}: setting instances up...".format(cls.SHORT_DESCR))

        mock_peering_db(cls._get_module_dir() + "/peeringdb_data")
        cls.mock_rpsl()
        cls._setup_instances()
        try:
            for instance in cls.INSTANCES:
                instance.set_var_dir("{}/var".format(cls._get_module_dir()))

                if cls._do_not_stop_instances() and instance.is_running():
                    cls.debug("Instance '{}' already running, reloading config".format(instance.name))
                    instance.remount()
                    if not instance.reload_config():
                        raise InstanceError("An error occurred while reloading '{}' configuration.".format(instance.name))
                    continue
                cls.debug("Starting instance '{}'...".format(instance.name))
                instance.start()
        except:
            cls.tearDownClass()
            raise

    @classmethod
    def _tearDownClass(cls):
        mock.patch.stopall()

        if cls._do_not_stop_instances():
            cls.debug("Skipping instances stopping")
            return
        print("{}: stopping instances...".format(cls.SHORT_DESCR))
        for instance in cls.INSTANCES:
            cls.debug("Stopping instance '{}'...".format(instance.name))
            instance.stop()

    def set_instance_variables(self):
        raise NotImplementedError()

    def _setUp(self):
        self.set_instance_variables()

    def receive_route_from(self, inst, prefix, other_inst=None, as_path=None,
                           next_hop=None, std_comms=None, lrg_comms=None,
                           ext_comms=None, filtered=None, only_best=None):
        routes = inst.get_routes(prefix,
                                 include_filtered=filtered if filtered is not None else False,
                                 only_best=only_best if only_best is not None else False)

        next_hop_ip = None
        if next_hop:
            next_hop_ip = next_hop if isinstance(next_hop, str) else next_hop.ip

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
                if next_hop and route.next_hop != next_hop_ip:
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
                if not err:
                    return

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
            if filtered is True:
                criteria.append("filtered")

            failure = "Looking for {prefix} on {inst} {criteria}:\n\t".format(
                prefix=prefix,
                inst=inst.name,
                criteria=", ".join(criteria)
            )
            failure += "\n\t".join([
                err.format(
                    inst=inst.name,
                    prefix=prefix,
                    other_inst="{} ({})".format(other_inst.ip, other_inst.name) if other_inst else "",
                    as_path=as_path,
                    next_hop_ip=next_hop_ip,
                    std_comms=std_comms,
                    lrg_comms=lrg_comms,
                    ext_comms=ext_comms,
                ) for err in errors
            ])
            self.fail(failure)

    def log_contains(self, inst, msg, instances={}):
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
            self.fail("Expected message not found on {} logs:\n\t{}".format(inst.name, expanded_msg))

    def session_is_up(self, inst_a, inst_b):
        if inst_a.bgp_session_is_up(inst_b):
            return
        time.sleep(5)
        if inst_a.bgp_session_is_up(inst_b, force_update=True):
            return
        self.fail("BGP session between '{}' ({}) and '{}' ({}) is not up.".format(
            inst_a.name, inst_a.ip, inst_b.name, inst_b.ip
        ))

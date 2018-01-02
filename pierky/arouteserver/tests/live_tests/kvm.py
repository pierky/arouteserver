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
import subprocess
import time

from .instances import InstanceError, BGPSpeakerInstance, InstanceNotRunning

class KVMInstance(BGPSpeakerInstance):

    MAX_BOOT_TIME = 60
    VIRSH_DOMAINNAME = None

    SSH_USERNAME = "root"
    SSH_KEY_PATH = "~/.ssh/arouteserver"

    @classmethod
    def _get_ssh_user(cls):
        if "SSH_USERNAME" in os.environ:
            return os.environ["SSH_USERNAME"]
        return cls.SSH_USERNAME

    @classmethod
    def _get_ssh_key_path(cls):
        if "SSH_KEY_PATH" in os.environ:
            path = os.environ["SSH_KEY_PATH"]
        else:
            path = cls.SSH_KEY_PATH
        return os.path.expanduser(path)

    @classmethod
    def _get_virsh_domainname(cls):
        if "VIRSH_DOMAINNAME" in os.environ:
            return os.environ["VIRSH_DOMAINNAME"]
        return cls.VIRSH_DOMAINNAME

    def __init__(self, *args, **kwargs):
        super(KVMInstance, self).__init__(*args, **kwargs)
        self.domain_name = self._get_virsh_domainname()

        # If set, the VM is always considered up and SSH connections
        # are established toward this IP address.
        self.remote_ip = kwargs.get("remote_ip", None)
        if self.remote_ip:
            self.remote_ip = self.remote_ip.strip()
        self.is_remote = self.remote_ip != "" and self.remote_ip

    @classmethod
    def _run(cls, cmd):
        cls.debug("Executing '{}'".format(cmd))
        try:
            dev_null = open(os.devnull, "w")
            stdout = subprocess.check_output(
                cmd.split(), stderr=dev_null
            ).decode("utf-8")
            return stdout
        except subprocess.CalledProcessError as e:
            raise InstanceError(
                "Error executing the following command:\n"
                "\t{}\n"
                "Output follows:\n\n"
                "{}".format(cmd, e.output)
            )

    def is_running(self):
        if self.is_remote:
            return True

        res = self._run("virsh list --name --state-running")
        return self.domain_name in res

    def _check_env(self):
        if not self.is_remote:
            vms_list_raw = self._run("virsh list --name --all")
            vms_list = vms_list_raw.split("\n")
            found = False
            for vm in vms_list:
                if vm.strip() == self.domain_name:
                    found = True
                    break
            if not found:
                raise Exception(
                    "The virsh domain '{}' does not appear to "
                    "be in the list of configured domains: "
                    "'virsh list --all'. Please check that the KVM "
                    "virtual machine used by the live test framework "
                    "is configured correctly. To use a different "
                    "VM name, set the VIRSH_DOMAINNAME environment "
                    "variable before running the tests.".format(
                        self.domain_name
                    )
                )

        key_file = self._get_ssh_key_path()
        if not os.path.exists(key_file) or not os.path.isfile(key_file):
            raise Exception(
                "The SSH key file needed to connect to the "
                "virtual machine used by the live test framework "
                "does not exist: {}. To use a different path, "
                "set the SSH_USERNAME environment variable before "
                "running the tests.".format(key_file)
            )

    def start(self):
        need_to_start = True

        if self.is_remote:
            need_to_start = False
        else:
            if self.is_running():
                if "REUSE_KVM_INSTANCES" in os.environ:
                    need_to_start = False
                else:
                    raise InstanceError("Instance '{}' already running.".format(self.name))

        if need_to_start:
            self._check_env()

            res = self._run("virsh start {}".format(self.domain_name))

            if "error:" in res:
                raise InstanceError(
                    "Can't run instance '{}'; "
                    "an error occurred while starting virsh domain '{}':\n"
                    "{}".format(self.name, self.domain_name, res)
                )
            time.sleep(3)

            if not self.is_running():
                raise InstanceError(
                    "The virsh domain '{}' failed to start".format(
                        self.domain_name
                    )
                )

            running = False
            for i in range(self.MAX_BOOT_TIME // 2):
                time.sleep(2)
                try:
                    res = self.run_cmd("true")
                    running = True
                    break
                except:
                    pass

            if not running:
                raise InstanceError(
                    "Instance '{}' seems not running after {} seconds".format(
                        self.name, self.MAX_BOOT_TIME
                    )
                )

        # The VM is now up and bgpd should be started too,
        # but configuration files have not been updated yet,
        # so call restart() in order to push them
        # to the VM and restart the daemon.
        self.restart()

    def _graceful_shutdown(self):
        return False

    def stop(self):
        if self.is_remote:
            return

        if not self.is_running():
            return

        if "REUSE_KVM_INSTANCES" in os.environ:
            return

        self._graceful_shutdown()

        for i in range(30 // 2):
            time.sleep(2)
            if not self.is_running():
                return

        if self.is_running() and not self.is_remote:
            try:
                self._run("virsh shutdown {}".format(self.domain_name))
                for i in range(30 // 2):
                    time.sleep(2)
                    if not self.is_running():
                        return
            except:
                pass

        if self.is_running() and not self.is_remote:
            try:
                self._run("virsh destroy {}".format(self.domain_name))
            except:
                pass

    def run_cmd(self, args):
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        cmd = ("ssh -o BatchMode=yes -o ConnectTimeout=5 "
               "-o StrictHostKeyChecking=no "
               "-o ServerAliveInterval=10 {user}@{ip} -i {path_to_key} "
               "{cmd}").format(
            user=self._get_ssh_user(),
            ip=self.remote_ip if self.is_remote else self.ip,
            path_to_key=self._get_ssh_key_path(),
            cmd=" ".join(args) if isinstance(args, list) else args
        )
        res = self._run(cmd)
        return res

    def _mount_files(self):
        for mount in self.get_mounts():
            ip = self.remote_ip if self.is_remote else self.ip
            local_file = mount["host"]
            remote_file = mount["container"]

            gzipped = local_file.endswith(".gz")
            if gzipped:
                remote_file += ".gz"

            cmd = ("scp -i {path_to_key} "
                   "-o StrictHostKeyChecking=no "
                   "{host_file} {user}@{ip}:{container_file} ".format(
                       host_file=local_file,
                       user=self._get_ssh_user(),
                       ip="[{}]".format(ip) if ":" in ip else ip,
                       container_file=remote_file,
                       path_to_key=self._get_ssh_key_path()
                    ))
            self._run(cmd)

            if gzipped:
                self.run_cmd("gunzip -f {}".format(remote_file))

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

import os
import subprocess
import time

from instances import InstanceError, BGPSpeakerInstance

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

    @classmethod
    def _run(cls, cmd):
        cls.debug("Executing '{}'".format(cmd))
        try:
            dev_null = open(os.devnull, "w")
            stdout = subprocess.check_output(
                cmd.split(), stderr=dev_null
            )
            return stdout
        except subprocess.CalledProcessError as e:
            raise InstanceError(
                "Error executing the following command:\n"
                "\t{}\n"
                "Output follows:\n\n"
                "{}".format(cmd, e.output)
            )

    def is_running(self):
        res = self._run("virsh list --name --state-running")
        return self.domain_name in res

    def _check_env(self):
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
        if not self.is_running():
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
            for i in range(self.MAX_BOOT_TIME / 5):
                time.sleep(5)
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
            # so call reload_config() in order to push them
            # to the VM and reload the daemon.
            self.reload_config()
        else:
            raise InstanceError("Instance '{}' already running.".format(self.name))

    def _graceful_shutdown(self):
        return False

    def stop(self):
        if not self.is_running():
            return

        if self._graceful_shutdown():
            time.sleep(10)

        for i in range(20 / 5):
            if not self.is_running():
                return
            time.sleep(5)

        if self.is_running():
            try:
                self._run("virsh shutdown {}".format(self.domain_name))
                for i in range(30 / 5):
                    if not self.is_running():
                        return
                    time.sleep(5)
            except:
                pass

        if self.is_running():
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
            ip=self.ip,
            path_to_key=self._get_ssh_key_path(),
            cmd=" ".join(args) if isinstance(args, list) else args
        )
        res = self._run(cmd)
        return res

    def _mount_files(self):
        for mount in self.get_mounts():
            cmd = ("scp -i {path_to_key} "
                   "-o StrictHostKeyChecking=no "
                   "{host_file} {user}@{ip}:{container_file} ".format(
                       host_file=mount["host"],
                       user=self._get_ssh_user(),
                       ip="[{}]".format(self.ip) if ":" in self.ip else self.ip,
                       container_file=mount["container"],
                       path_to_key=self._get_ssh_key_path()
                    ))
            res = self._run(cmd)

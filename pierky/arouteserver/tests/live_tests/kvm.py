# Copyright (C) 2017-2019 Pier Carlo Chiodi
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
import time

from .instances import InstanceError, BGPSpeakerInstance, InstanceNotRunning

class KVMInstance(BGPSpeakerInstance):

    MAX_BOOT_TIME = 60
    VIRSH_DOMAINNAME = None

    SSH_USERNAME = "root"
    SSH_KEY_PATH = "~/.ssh/arouteserver"

    def _get_ssh_user(self):
        if "SSH_USERNAME" in os.environ:
            return os.environ["SSH_USERNAME"]
        return self.SSH_USERNAME

    def _get_ssh_key_path(self):
        if "SSH_KEY_PATH" in os.environ:
            path = os.environ["SSH_KEY_PATH"]
        else:
            path = self.SSH_KEY_PATH
        return os.path.expanduser(path)

    def _get_virsh_domainname(self):
        if "VIRSH_DOMAINNAME" in os.environ:
            return os.environ["VIRSH_DOMAINNAME"]
        return self.VIRSH_DOMAINNAME

    def __init__(self, *args, **kwargs):
        super(KVMInstance, self).__init__(*args, **kwargs)
        self.domain_name = self._get_virsh_domainname()

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

        if self.remote_execution_server_ip:
            try:
                self._run("true")
            except Exception as e:
                raise Exception(
                    "An error occurred while testing the SSH connection "
                    "toward the remote server that will be used to run "
                    "the current scenario ({}): {}".format(
                        self.remote_execution_server_ip, str(e)
                    )
                )
                raise e

        if not self.remote_execution_server_ip:
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
        """Perform graceful shutdown; must be implemented by children"""
        return False

    def stop(self):
        if not self.is_running():
            return

        if "REUSE_KVM_INSTANCES" in os.environ:
            return

        self._graceful_shutdown()

        for i in range(30 // 2):
            time.sleep(2)
            if not self.is_running():
                return

        if self.is_running():
            try:
                self._run("virsh shutdown {}".format(self.domain_name))
                for i in range(30 // 2):
                    time.sleep(2)
                    if not self.is_running():
                        return
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

        if self.remote_execution_server_ip:
            # Using the -J for the jump-host, in order to
            # spin up a local SSH process that will use
            # self.remote_execution_server_* as jump-host to
            # run the command directly on the KVM VM.
            cmd = (
                "ssh "
                "-o BatchMode=yes "
                "-o ConnectTimeout=5 "
                "-o ServerAliveInterval=10 "
                "-J {remote_server_user}@{remote_server_ip} "
                "{kvm_vm_user}@{kvm_vm_ip} "
                "{cmd}"
            ).format(
                remote_server_user=self.remote_execution_server_user,
                remote_server_ip=self.remote_execution_server_ip,
                kvm_vm_user=self._get_ssh_user(),
                kvm_vm_ip=self.ip,
                cmd=" ".join(args) if isinstance(args, list) else args
            )
        else:
            cmd = (
                "ssh "
                "-o BatchMode=yes "
                "-o ConnectTimeout=5 "
                "-o ServerAliveInterval=10 "
                "{user}@{ip} -i {path_to_key} "
                "{cmd}"
            ).format(
                user=self._get_ssh_user(),
                ip=self.ip,
                path_to_key=self._get_ssh_key_path(),
                cmd=" ".join(args) if isinstance(args, list) else args
            )

        res = self._run_local(cmd)
        return res

    def _mount_files(self):
        for mount in self.get_mounts():
            ip = self.ip
            local_file = mount["host"]
            remote_file = mount["container"]

            gzipped = local_file.endswith(".gz")
            if gzipped:
                remote_file += ".gz"

            if self.remote_execution_server_ip:
                # Copy the file from the host where the CI suite is running to
                # the remote server where the KVM is running using the jump-host.
                cmd = [
                    "scp",
                    "-o", "BatchMode=yes",
                    "-o", "ConnectTimeout=5",
                    "-o", "ServerAliveInterval=10",
                    "-o", "ProxyCommand ssh {remote_server_user}@{remote_server_ip} nc %h %p".format(
                        remote_server_user=self.remote_execution_server_user,
                        remote_server_ip=self.remote_execution_server_ip,
                    ),
                    "{host_file}".format(
                        host_file=local_file
                    ),
                    "{kvm_vm_user}@{kvm_vm_ip}:{remote_file}".format(
                        kvm_vm_user=self._get_ssh_user(),
                        kvm_vm_ip="[{}]".format(self.ip) if ":" in self.ip else self.ip,
                        remote_file=remote_file,
                    )
                ]
            else:
                cmd = (
                    "scp -i {path_to_key} "
                    "{host_file} {user}@{ip}:{remote_file} ".format(
                        host_file=local_file,
                        user=self.remote_execution_server_user,
                        ip=self.remote_execution_server_ip,
                        remote_file=remote_file,
                        path_to_key=self.remote_execution_server_key
                    )
                )

            self._run_local(cmd)

            if gzipped:
                self.run_cmd("gunzip -f {}".format(remote_file))

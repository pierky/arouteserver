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
import subprocess
import time
import random
import string

from .instances import InstanceError, BGPSpeakerInstance, InstanceNotRunning

class DockerInstance(BGPSpeakerInstance):

    DOCKER_PATH = "docker"
    DOCKER_INSTANCE_PREFIX = "ars_"
    DOCKER_NETWORK_NAME = "arouteserver"
    DOCKER_NETWORK_SUBNET_IPv4 = "192.0.2.0/24"
    DOCKER_NETWORK_SUBNET_IPv6 = "2001:db8:1:1::/64"

    def __init__(self, *args, **kwargs):
        super(DockerInstance, self).__init__(*args, **kwargs)
        self.image = self.DOCKER_IMAGE

    def _instance_is_running(self, name):
        cmd = '{docker} ps -f name={prefix}{name} --format="{{{{.ID}}}}"'.format(
            docker=self.DOCKER_PATH,
            prefix=self.DOCKER_INSTANCE_PREFIX, name=name
        )
        res = self._run(cmd)
        if not res:
            return False
        else:
            return True

    def _docker_image_exists(self):
        cmd = '{docker} images {image} --format="{{{{.Repository}}}}"'.format(
            docker=self.DOCKER_PATH,
            image=self.image
        )
        res = self._run(cmd)
        if res is None:
            raise InstanceError("Can't get the list of Docker images")
        else:
            return len(res.strip()) > 0

    def _setup_networking(self):
        network_details = None
        try:
            network_details = self._run("{} network inspect {}".format(
                self.DOCKER_PATH,
                self.DOCKER_NETWORK_NAME)
            )
        except:
            # network does not exist
            pass

        if network_details is not None:
            try:
                if self.DOCKER_NETWORK_SUBNET_IPv4 not in network_details:
                    raise InstanceError("IPv4")
                if self.DOCKER_NETWORK_SUBNET_IPv6 not in network_details:
                    raise InstanceError("IPv6")
            except InstanceError as e:
                raise InstanceError(
                    "The Docker network used by ARouteServer live tests "
                    "('{net}') already exists but is on a "
                    "wrong {v} subnet. Plase consider removing it "
                    "with '{docker} network rm {net}'.".format(
                        net=self.DOCKER_NETWORK_NAME,
                        v=str(e),
                        docker=self.DOCKER_PATH
                    )
                )
            return

        try:
            self._run("{} network create --ipv6 --subnet={} --subnet={} {}".format(
                self.DOCKER_PATH,
                self.DOCKER_NETWORK_SUBNET_IPv4,
                self.DOCKER_NETWORK_SUBNET_IPv6,
                self.DOCKER_NETWORK_NAME
            ))
        except Exception as e:
            raise InstanceError(
                "Error while creating Docker network '{}': {}.".format(
                    self.DOCKER_NETWORK_NAME, str(e)
                )
            )

    def is_running(self):
        return self._instance_is_running(self.name)

    def _get_start_cmd(self):
        raise NotImplementedError()

    def get_mounts(self):

        def random_string(str_len):
            """Generate a random string with the combination of lowercase and uppercase letters """
            letters = string.ascii_letters
            return ''.join(random.choice(letters) for i in range(str_len))

        # When the Docker host is remote, the local file must be uploaded
        # before it can be mounted inside the container.
        for mount in BGPSpeakerInstance.get_mounts(self):
            if self.remote_execution_server_ip:
                res = mount

                remote_server_file = "/tmp/ars." + res["host_filename"] + "." + random_string(6)
                cmd = (
                    "scp "
                    "{host_file} {remote_server_user}@{remote_server_ip}:{remote_file}".format(
                        host_file=res["host"],
                        remote_server_user=self.remote_execution_server_user,
                        remote_server_ip=self.remote_execution_server_ip,
                        remote_file=remote_server_file
                    )
                )
                self._run_local(cmd)
                res["var_path"] = remote_server_file

                yield res
            else:
                yield mount

    def start(self):
        self._setup_networking()

        if not self.is_running():

            if not self._docker_image_exists():
                raise InstanceError(
                    "Docker image '{image}' is not present on this system. "
                    "Build it using "
                    "'docker build -t {image} -f PATH_TO_DOCKERFILE .' "
                    "or pull it from DockerHub using "
                    "'docker pull {image}'.".format(image=self.image)
                )

            cmd = ('{docker} run {detached_flag} --rm '
                   '--net={net_name} {ip_arg}={ip} '
                   '--name={prefix}{name} '
                   '{mounts} {image} {start_cmd}'.format(
                        docker=self.DOCKER_PATH,
                        detached_flag="-d" if self.remote_execution_server_ip else "",
                        net_name=self.DOCKER_NETWORK_NAME,
                        ip_arg="--ip6" if ":" in self.ip else "--ip",
                        ip=self.ip,
                        name=self.name,
                        prefix=self.DOCKER_INSTANCE_PREFIX,
                        mounts=" ".join([
                            "-v{host}:{container}".format(
                                host=mount["var_path"],
                                container=mount["container"]
                            )
                            for mount in self.get_mounts()
                        ]),
                        image=self.image,
                        start_cmd=self._get_start_cmd()
                    )
            )

            self._run(
                cmd,
                detached=True if not self.remote_execution_server_ip else False
            )
            time.sleep(3)
            if not self.is_running():
                process = subprocess.Popen(
                    cmd.split(),
                    stdin=None,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = process.communicate()
                print("cmd:", cmd)
                print("STDOUT:")
                print(stdout)
                print("STDERR:")
                print(stderr)

                raise InstanceError(
                    "Can't run detached instance: {}\n"
                    "cmd:\n"
                    "{}".format(self.name, cmd)
                )
        else:
            raise InstanceError("Instance '{}' already running.".format(self.name))

    def stop(self):
        if not self.is_running():
            return

        cmd = '{docker} stop --time=2 {prefix}{name}'.format(
            docker=self.DOCKER_PATH,
            prefix=self.DOCKER_INSTANCE_PREFIX,
            name=self.name
        )
        res = self._run(cmd)
        return res

    def run_cmd(self, args):
        if not self.is_running():
            raise InstanceNotRunning(self.name)

        cmd = '{docker} exec -i {prefix}{name} {args}'.format(
            docker=self.DOCKER_PATH,
            prefix=self.DOCKER_INSTANCE_PREFIX,
            name=self.name,
            args=" ".join(args) if isinstance(args, list) else args
        )
        res = self._run(cmd)
        return res

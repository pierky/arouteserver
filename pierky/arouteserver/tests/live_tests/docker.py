# Copyright (C) 2017-2020 Pier Carlo Chiodi
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

class DockerInstance(BGPSpeakerInstance):

    DOCKER_PATH = "docker"
    DOCKER_INSTANCE_PREFIX = "ars_"
    DOCKER_NETWORK_NAME = "arouteserver"
    DOCKER_NETWORK_SUBNET_IPv4 = "192.0.2.0/24"
    DOCKER_NETWORK_SUBNET_IPv6 = "2001:db8:1:1::/64"

    def __init__(self, *args, **kwargs):
        super(DockerInstance, self).__init__(*args, **kwargs)
        self.image = self.DOCKER_IMAGE

    @classmethod
    def _run(cls, cmd, detached=False):
        try:
            if detached:
                dev_null = open(os.devnull, "w")
                subprocess.Popen(
                    cmd.split(),
                    stdin=None,
                    stdout=dev_null,
                    stderr=dev_null
                )
                return None
            else:
                stdout = subprocess.check_output(cmd.split()).decode("utf-8")
                return stdout
        except subprocess.CalledProcessError as e:
            raise InstanceError(
                "Error executing the following command:\n"
                "\t{}\n"
                "Output follows:\n\n"
                "{}".format(cmd, e.output)
            )

    @classmethod
    def _instance_is_running(cls, name):
        cmd = '{docker} ps -f name={prefix}{name} --format="{{{{.ID}}}}"'.format(
            docker=cls.DOCKER_PATH,
            prefix=cls.DOCKER_INSTANCE_PREFIX, name=name
        )
        res = cls._run(cmd)
        if not res:
            return False
        else:
            return True

    def _docker_image_exists(self):
        cmd = '{docker} images {image} --format="{{{{.Repository}}}}'.format(
            docker=self.DOCKER_PATH,
            image=self.image
        )
        res = self._run(cmd)
        if res is None:
            raise InstanceError("Can't get the list of Docker images")
        else:
            return len(res.strip()) > 0

    @classmethod
    def _setup_networking(cls):
        network_details = None
        try:
            network_details = cls._run("{} network inspect {}".format(
                cls.DOCKER_PATH,
                cls.DOCKER_NETWORK_NAME)
            )
        except:
            # network does not exist
            pass

        if network_details is not None:
            try:
                if cls.DOCKER_NETWORK_SUBNET_IPv4 not in network_details:
                    raise InstanceError("IPv4")
                if cls.DOCKER_NETWORK_SUBNET_IPv6 not in network_details:
                    raise InstanceError("IPv6")
            except InstanceError as e:
                raise InstanceError(
                    "The Docker network used by ARouteServer live tests "
                    "('{net}') already exists but is on a "
                    "wrong {v} subnet. Plase consider removing it "
                    "with '{docker} network rm {net}'.".format(
                        net=cls.DOCKER_NETWORK_NAME,
                        v=str(e),
                        docker=cls.DOCKER_PATH
                    )
                )
            return

        try:
            cls._run("{} network create --ipv6 --subnet={} --subnet={} {}".format(
                cls.DOCKER_PATH,
                cls.DOCKER_NETWORK_SUBNET_IPv4,
                cls.DOCKER_NETWORK_SUBNET_IPv6,
                cls.DOCKER_NETWORK_NAME
            ))
        except Exception as e:
            raise InstanceError(
                "Error while creating Docker network '{}': {}.".format(
                    cls.DOCKER_NETWORK_NAME, str(e)
                )
            )

    def is_running(self):
        return self._instance_is_running(self.name)

    def _get_start_cmd(self):
        raise NotImplementedError()

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

            cmd = ('{docker} run --rm '
                   '--net={net_name} {ip_arg}={ip} '
                   '--name={prefix}{name} '
                   '{mounts} {image} {start_cmd}'.format(
                        docker=self.DOCKER_PATH,
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

            self._run(cmd, detached=True)
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

        cmd = '{docker} exec -it {prefix}{name} {args}'.format(
            docker=self.DOCKER_PATH,
            prefix=self.DOCKER_INSTANCE_PREFIX,
            name=self.name,
            args=" ".join(args) if isinstance(args, list) else args
        )
        res = self._run(cmd)
        return res

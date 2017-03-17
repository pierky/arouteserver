Live tests
==========

Live tests are used to validate configurations built by ARouteServer.

A mix of Python's unittest and Docker (and KVM too for OpenBGPD tests) allows to create scenarios where some instances of BGP speakers connect to a route server that has been configured using this program in order to test compliance between expected and real results.

Example: in a configuration where blackhole filtering is enabled, an instance of a route server client (AS1) is used to announce some tagged prefixes (203.0.113.1/32) and the instances representing other clients (AS2, AS3) are queried to ensure they receive those prefixes with the expected blackhole NEXT_HOP (192.0.2.66).

.. code:: python

  def test_071_blackholed_prefixes_as_seen_by_enabled_clients(self):
    for inst in (self.AS2, self.AS3):
      self.receive_route(inst, "203.0.113.1/32", self.rs,
                         next_hop="192.0.2.66",
                         std_comms=["65535:666"], lrg_comms=[])

Travis CI log file contains the latest built-in live tests results: https://travis-ci.org/pierky/arouteserver/
Since (AFAIK) OpenBGPD can't be run on Travis CI platform, the full live tests results including those run on OpenBGPD can be found on `this file <https://github.com/pierky/arouteserver/blob/master/tests/last>`_.

How to run built-in live tests
-------------------------------

To run built-in live tests, the full repository must be cloned locally and Docker and KVM must be present on the system.

1. Build the Docker image (or pull it from `Dockerhub <https://hub.docker.com/r/pierky/bird/>`_):

   .. code:: bash

      # build the image using the Dockerfile
      # from https://github.com/pierky/dockerfiles
      mkdir ~/dockerfiles
      cd ~/dockerfiles
      curl -o Dockerfile.bird -L https://raw.githubusercontent.com/pierky/dockerfiles/master/bird/1.6.3/Dockerfile
      docker build -t pierky/bird:1.6.3 -f Dockerfile.bird .

      # or pull it from Dockerhub
      docker pull pierky/bird:1.6.3

2. (optional, needed to run tests on OpenBGPD)

   Setup and install a KVM virtual-machine with OpenBSD 6.0.
   By default, the VM name must be "arouteserver_openbgpd"; this can be changed by setting the ``VIRSH_DOMAINNAME`` environment variable before running the tests.
   This VM will be started and stopped many times during tests: don't use a production VM.

   .. code:: bash

      # on this example the virtual disk will be stored in ~/vms
      sudo virsh pool-define-as --name vms_pool --type dir --target ~/vms
      sudo virsh pool-start vms_pool

      # the VM will be reachable by connecting to any IP address
      # of the host via VNC; the installation disk image is expected
      # to be found in the install60.iso file
      sudo virt-install \
        -n arouteserver_openbgpd \
        -r 512 \
        --vcpus=1 \
        --os-variant=openbsd4 \
        --accelerate \
        -v -c install60.iso \
        -w bridge:br-2d2956ce4b64 \
        --graphics vnc,listen=0.0.0.0 \
        --disk path=~/vms/arouteserver_openbgpd.qcow2,size=5,format=qcow2

      # add the current user to the libvirtd group to allow
      # management of the VM
      sudo adduser `id -un` libvirtd

   To interact with this VM, the live tests framework will use SSH; by default, the connection will be established using the ``root`` username and the local key file ``~/.ssh/arouteserver``, so the VM must be configured to accept SSH connections using SSH keys:

   .. code:: bash

      mkdir /root/.ssh
      cat << EOF > .ssh/authorized_keys
      ssh-rsa [public_key_here] arouteserver
      EOF

   The SSH username and key file path can be changed by setting the ``SSH_USERNAME`` and ``SSH_KEY_PATH`` environment variables before running the tests.

   Be sure the ``bgpd`` daemon and the ``bgpctl`` tool can be executed correctly.

3. Run the Python unittest using ``nose``:

   .. code:: bash

      # from within the repository's root
      nosetests -vs tests/live_tests/

How it works
------------

Each directory in ``tests/live_tests/scenarios`` represents a scenario: the route server configuration is stored in the usual ``general.yml`` and ``clients.yml`` files, while other BGP speaker instances (route server clients and their peers) are configured through the ``ASxxx.j2`` files.
These files are Jinja2 templates and are expanded by the Python code at runtime. Containers' configuration files are saved in the local ``var`` directory and are used to mount the BGP speaker configuration file (currenly, ``/etc/bird/bird.conf`` for BIRD and ``/etc/bgpd.conf`` for OpenBGPD).
The unittest code sets up a Docker network (with name ``arouteserver``) used to attach instances and finally brings instances up. Regular Python unittest tests are then performed and can be used to match expectations to real results.

Details about the code behind the live tests can be found in the :doc:`LIVETESTS_CODEDOC` section.

Live tests
==========

Live tests are used to validate configurations built by ARouteServer and to test compliance between expected and real results.

A mix of Python unittest and Docker (and KVM too for OpenBGPD tests) allows to create scenarios where some instances of BGP speakers (the clients) connect to a route server whose configuration has been generated using this tool.

Some built-in tests are included within the project and have been used during the development of the tool; new :ref:`custom scenarios <LiveTestsCustomScenarios>` can be easily built by users and IXP managers to test their own policies.

Example: in a configuration where blackhole filtering is enabled, an instance of a route server client (AS1) is used to announce some tagged prefixes (203.0.113.1/32) and the instances representing other clients (AS2, AS3) are queried to ensure they receive those prefixes with the expected blackhole NEXT_HOP (192.0.2.66).

.. code:: python

  def test_071_blackholed_prefixes_as_seen_by_enabled_clients(self):
    for inst in (self.AS2, self.AS3):
      self.receive_route(inst, "203.0.113.1/32", self.rs,
                         next_hop="192.0.2.66",
                         std_comms=["65535:666"], lrg_comms=[])

`Travis CI log file <https://travis-ci.org/pierky/arouteserver/>`_ contains the latest built-in live tests results.
Since (AFAIK) OpenBGPD can't be run on Travis CI platform, the full live tests results, including those run on OpenBGPD, can be found on `this file <https://github.com/pierky/arouteserver/blob/master/tests/last>`_.
Starting with version 6.5, the Portable edition of OpenBGPD has been used to run some tests on TravisCI too.

Setting up the environment to run live tests
--------------------------------------------

1. To run live tests, Docker must be present on the system. Some info about its installation can be found on the :ref:`External programs` installation section.

2. In order to have instances of the route server and its clients to connect each other, a common network must be used. Live tests are expected to be run on a Docker bridge network with name ``arouteserver`` and subnet ``192.0.2.0/24``/``2001:db8:1:1::/64``.
   The following command can be used to create this network:

  .. code:: bash

     docker network create --ipv6 --subnet=192.0.2.0/24 --subnet=2001:db8:1:1::/64 arouteserver

3. Route server client instances used in live tests are based on BIRD 1.6.4, as well as the BIRD-based version of the route server used in built-in live tests; the ``pierky/bird:1.6.4`` image is expected to be found on the local Docker repository. Also, for OpenBGPD Portable edition tests, ``pierky/openbgpd:6.5p0`` must be there.
   Build the Docker image (or pull it from `Dockerhub <https://hub.docker.com/r/pierky/bird/>`_):

   .. code:: bash

      # build the image using the Dockerfile
      # from https://github.com/pierky/dockerfiles
      mkdir ~/dockerfiles
      cd ~/dockerfiles
      curl -o Dockerfile.bird -L https://raw.githubusercontent.com/pierky/dockerfiles/master/bird/1.6.4/Dockerfile
      docker build -t pierky/bird:1.6.4 -f Dockerfile.bird .
      curl -o Dockerfile.openbgpd -L https://raw.githubusercontent.com/pierky/dockerfiles/master/openbgpd/6.5p0/Dockerfile
      docker build -t pierky/openbgpd:6.5p0 -f Dockerfile.openbgpd .

      # or pull it from Dockerhub
      docker pull pierky/bird:1.6.4
      docker pull pierky/openbgpd:6.5p0

If there is no plan to run tests on the OpenBGPD-based version of the route server, no further settings are needed.
To run tests on the OpenBGPD-based version too, the following steps must be done as well.

OpenBGPD live-tests environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. To run an instance of OpenBGPD, KVM is needed. Some info about its installation can be found on the :ref:`External programs` installation section.

2. Setup and install a KVM virtual-machine running one of the supported versions of OpenBSD. This VM will be started and stopped many times during tests: don't use a production VM.

   - By default, the VM name must be ``arouteserver_openbgpd60`` or ``arouteserver_openbgpd61`` or ``arouteserver_openbgpd62``; this can be changed by setting the ``VIRSH_DOMAINNAME`` environment variable before running the tests.

   - The VM must be connected to the same Docker network created above: the commands ``ip link show`` and ``ifconfig`` can be used to determine the local network name needed when creating the VM:

   .. code-block:: console

      $ ifconfig
      br-2d2956ce4b64 Link encap:Ethernet  HWaddr 02:42:57:82:bc:91
        inet addr:192.0.2.1  Bcast:0.0.0.0  Mask:255.255.255.0
        inet6 addr: fe80::42:57ff:fe82:bc91/64 Scope:Link
        inet6 addr: 2001:db8:1:1::1/64 Scope:Global
        inet6 addr: fe80::1/64 Scope:Link
        UP BROADCAST MULTICAST  MTU:1500  Metric:1
        ...

   - In order to run built-in live test scenarios, the VM must be reachable at 192.0.2.2/24 and 2001:db8:1:1::2/64.

   On the following example, the virtual disk will be stored in ~/vms, the VM will be reachable by connecting to any IP address of the host via VNC, the installation disk image is expected to be found in the install60.iso file and the network name used is **br-2d2956ce4b64**:

   .. code:: bash

      sudo virsh pool-define-as --name vms_pool --type dir --target ~/vms
      sudo virsh pool-start vms_pool
      sudo virt-install \
        -n arouteserver_openbgpd60 \
        -r 512 \
        --vcpus=1 \
        --os-variant=openbsd4 \
        --accelerate \
        -v -c install60.iso \
        -w bridge:br-2d2956ce4b64 \
        --graphics vnc,listen=0.0.0.0 \
        --disk path=~/vms/arouteserver_openbgpd.qcow2,size=5,format=qcow2

   Finally, add the current user to the libvirtd group to allow management of the VM:

   .. code:: bash

      sudo adduser `id -un` libvirtd

3. To interact with this VM, the live tests framework will use SSH; by default, the connection will be established using the ``root`` username and the local key file ``~/.ssh/arouteserver``, so the VM must be configured to accept SSH connections using SSH keys:

   .. code:: bash

      mkdir /root/.ssh
      cat << EOF > .ssh/authorized_keys
      ssh-rsa [public_key_here] arouteserver
      EOF

   The ``StrictHostKeyChecking`` option is disabled via command line argument in order to allow to connect to multiple different VMs with the same IP address.

   The SSH username and key file path can be changed by setting the ``SSH_USERNAME`` and ``SSH_KEY_PATH`` environment variables before running the tests.

   Be sure that the ``bgpd`` daemon will startup automatically at boot and that the ``bgpctl`` tool can be executed correctly on the OpenBSD VM:

   .. code:: bash

      echo "bgpd_flags=" >> /etc/rc.conf.local
      chmod 0555 /var/www/bin/bgpctl

How to run built-in live tests
------------------------------

To run built-in live tests, the full repository must be cloned locally and the environment must be configured as reported above.

To test both the BIRD- and OpenBGPD-based route servers, run the Python unittest using ``nose``:

   .. code:: bash

      # from within the repository's root
      nosetests -vs tests/live_tests/

How it works
------------

Each directory in ``tests/live_tests/scenarios`` represents a scenario: the route server configuration is stored in the usual ``general.yml`` and ``clients.yml`` files, while other BGP speaker instances (route server clients and their peers) are configured through the ``ASxxx.j2`` files.
These files are Jinja2 templates and are expanded by the Python code at runtime. Containers' configuration files are saved in the local ``var`` directory and are used to mount the BGP speaker configuration file (currenly, ``/etc/bird/bird.conf`` for BIRD and ``/etc/bgpd.conf`` for OpenBGPD).
The unittest code sets up a Docker network (with name ``arouteserver``) used to attach instances and finally brings instances up. Regular Python unittest tests are then performed and can be used to match expectations to real results.

Details about the code behind the live tests can be found in the :doc:`LIVETESTS_CODEDOC` section.

.. include:: LIVETESTS_TOC.rst

.. _LiveTestsCustomScenarios:

How to build custom scenarios
-----------------------------

A live test scenario skeleton is provided in the ``pierky/arouteserver/tests/live_tests/skeleton`` directory.

It seems to be a complex thing but actually most of the work is already done in the underlying Python classes and prepared in the skeleton.

To configure the route server and its clients, please consider that the Docker network used by the framework is on 192.0.2.0/24 and 2001:db8:1:1::/64 subnets.

1. Initialize the new scenario into a new directory:

   - using the ``init-scenario`` command:

   .. code:: bash

      arouteserver init-scenario ~/ars_scenarios/myscenario

   - manually, by cloning the provided skeleton directory:

   .. code:: bash

      mkdir -p ~/ars_scenarios/myscenario
      cp pierky/arouteserver/tests/live_tests/skeleton/* ~/ars_scenarios/myscenario

2. Document the scenario, for example in the ``README.rst`` file: write down which BGP speakers are involved, how they are configured, which prefixes they announce and what the expected result should be with regards of the route server's configuration and its policies.

3. Put the ``general.yml``, ``clients.yml`` and ``bogons.yml`` configuration files you want to test in the new directory.

4. Configure your scenario and write your test functions in the ``base.py`` file.

   - Declare the BGP speakers you want to use in the ``_setup_rs_instance()`` and ``_setup_instances()`` methods of the base class.

        .. automethod:: pierky.arouteserver.tests.live_tests.skeleton.base.SkeletonScenario._setup_instances
                :noindex:

        Example:

	.. code-block:: python

	    @classmethod
	    def _setup_instances(cls):
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
	            ...
                ]

   - To ease writing the test functions, set instances names in the ``set_instance_variables()`` method.

        .. automethod:: pierky.arouteserver.tests.live_tests.skeleton.base.SkeletonScenario.set_instance_variables
                :noindex:

        Example:

	.. code-block:: python

            def set_instance_variables(self):
                self.AS1 = self._get_instance_by_name("AS1")
                self.AS2 = self._get_instance_by_name("AS2")
                self.rs = self._get_instance_by_name("rs")

   - Write test functions to verify that scenario's expectations are met.

     Some helper functions can be used:

     -
        .. automethod:: pierky.arouteserver.tests.live_tests.base.LiveScenario.session_is_up
                :noindex:

        Example:

        .. literalinclude:: ../pierky/arouteserver/tests/live_tests/skeleton/base.py
                :pyobject: SkeletonScenario.test_020_sessions_up

     -
        .. automethod:: pierky.arouteserver.tests.live_tests.base.LiveScenario.receive_route
                :noindex:

        Example:

        .. literalinclude:: ../pierky/arouteserver/tests/live_tests/skeleton/base.py
                :pyobject: SkeletonScenario.test_030_rs_receives_AS2_prefix

     -
        .. automethod:: pierky.arouteserver.tests.live_tests.base.LiveScenario.log_contains
                :noindex:

        Example:

        .. literalinclude:: ../pierky/arouteserver/tests/live_tests/skeleton/base.py
                :pyobject: SkeletonScenario.test_030_rs_rejects_bogon

5. Edit IP version specific and BGP speaker specific classes within the ``test_XXX.py`` files and set the prefix ID / real IP addresses mapping schema.

   .. autoclass:: pierky.arouteserver.tests.live_tests.skeleton.test_bird4.SkeletonScenario_BIRDIPv4
        :noindex:

   Example:

   .. code-block:: python

      class SkeletonScenario_BIRDIPv4(SkeletonScenario):

          # Leave this to True in order to allow nose to use this class
          # to run tests.
          __test__ = True

          SHORT_DESCR = "Live test, BIRD, skeleton, IPv4"
          CONFIG_BUILDER_CLASS = BIRDConfigBuilder
          RS_INSTANCE_CLASS = BIRDInstanceIPv4
          CLIENT_INSTANCE_CLASS = BIRDInstanceIPv4
          IP_VER = 4

          DATA = {
              "rs_IPAddress":             "99.0.2.2",
              "AS1_IPAddress":            "99.0.2.11",
              "AS2_IPAddress":            "99.0.2.22",

              "AS2_prefix1":              "2.0.1.0/24",
              "AS2_bogon1":               "192.168.2.0/24"
          }

6. Edit (or add) the template files that, once rendered, will produce the configuration files for the other BGP speakers (route server clients) that are involved in the scenario (the skeleton includes two template files, ``AS1.j2`` and ``AS2.j2``).

   Example:

   .. literalinclude:: ../pierky/arouteserver/tests/live_tests/skeleton/AS2.j2

7. Run the tests using ``nose``:

   .. code:: bash

      nosetests -vs ~/ars_scenarios/myscenario

Details about the code behind the live tests can be found in the :doc:`LIVETESTS_CODEDOC` section.

Debugging live tests scenarios
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To debug custom scenarios some utilities are provided:

- the ``REUSE_INSTANCES`` environment variable can be set when executing nose to avoid Docker instances to be torn down at the end of a run.
  When this environment variable is set, BGP speaker instances are started only the first time tests are executed, then are left up and running to allow debugging. When tests are executed again, the BGP speakers' configuration is rebuilt and reloaded. **Be careful**: this mode can be used only when running tests of the same scenario, otherwise Bad Things (tm) may happen.

  Example:

  .. code:: bash

        REUSE_INSTANCES=1 nosetests -vs tests/live_tests/scenarios/global/test_bird4.py

- once the BGP speaker instances are up (using the ``REUSE_INSTANCES`` environment variable seen above), they can be queried using standard Docker commands:

  .. code-block:: console

        $ # list all the running Docker instances
        $ docker ps
        CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
        142f88379428        pierky/bird:1.6.3   "bird -c /etc/bird..."   18 minutes ago      Up 18 minutes       179/tcp             ars_AS101
        26a9ec58dcf1        pierky/bird:1.6.3   "bird -c /etc/bird..."   18 minutes ago      Up 18 minutes       179/tcp             ars_AS2

        $ # run 'birdcl show route' on ars_AS101
        $ docker exec -it 142f88379428 birdcl show route


  Some utilities are provided whitin the ``/utils`` directory to ease these tasks:

  .. code:: bash

        # execute the 'show route' command on the route server BIRD Docker instance
        ./utils/birdcl rs show route

        # print the log of the route server
        ./utils/run rs cat /var/log/bird.log

  The first argument ("rs" in the examples above) is the name of the instance as set in the ``_setup_instances()`` method.

- the ``BUILD_ONLY`` environment variable can be set to skip all the tests and only build the involved BGP speakers' configurations.
  Docker instances are not started in this mode.

  Example:

  .. code:: bash

        BUILD_ONLY=1 nosetests -vs tests/live_tests/scenarios/global/test_bird4.py

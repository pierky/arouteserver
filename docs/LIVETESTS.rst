Live tests
==========

Live tests are used to validate configurations built by ARouteServer and to test compliance between expected and real results.

A mix of Python unittest and Docker allows to create scenarios where some instances of BGP speakers (the clients) connect to a route server whose configuration has been generated using this tool.

Some built-in tests are included within the project and have been used during the development of the tool; new :ref:`custom scenarios <LiveTestsCustomScenarios>` can be easily built by users and IXP managers to test their own policies.

Example: in a configuration where blackhole filtering is enabled, an instance of a route server client (AS1) is used to announce some tagged prefixes (203.0.113.1/32) and the instances representing other clients (AS2, AS3) are queried to ensure they receive those prefixes with the expected blackhole NEXT_HOP (192.0.2.66).

.. code:: python

  def test_071_blackholed_prefixes_as_seen_by_enabled_clients(self):
    for inst in (self.AS2, self.AS3):
      self.receive_route(inst, "203.0.113.1/32", self.rs,
                         next_hop="192.0.2.66",
                         std_comms=["65535:666"], lrg_comms=[])

`GitHub Actions log file <https://github.com/pierky/arouteserver/actions/workflows/cicd.yml>`_ contains the latest built-in live tests results, including those for the OpenBGPD Portable edition, which is the only OpenBGPD edition used by the live tests suite.
The full live tests results can also be found on `this file <https://github.com/pierky/arouteserver/blob/master/tests/last>`_.

A summary of the integration testing results and the BGP speakers which are tested can be found on the :ref:`Integration testing coverage` section of this documentation.

Setting up the environment to run live tests
--------------------------------------------

1. To run live tests, Docker must be present on the system. Some info about its installation can be found on the :ref:`External programs` installation section.

2. In order to have instances of the route server and its clients to connect each other, a common network must be used. Live tests are expected to be run on a Docker bridge network with name ``arouteserver`` and subnet ``192.0.2.0/24``/``2001:db8:1:1::/64``.
   The following command can be used to create this network:

  .. code:: bash

     docker network create --ipv6 --subnet=192.0.2.0/24 --subnet=2001:db8:1:1::/64 arouteserver

3. Route server client instances used in live tests are based on BIRD 1.6.8, regardless of which version is used for the BIRD-based route server itself; the ``pierky/bird:1.6.8`` image is expected to be found on the local Docker repository. The BIRD-based route server is tested against ``pierky/bird:2.19.2``, ``pierky/bird:3.2.3`` and ``pierky/bird:3.3.2``, which must also be present locally. The OpenBGPD-based route server is tested against the Portable edition only, using the ``pierky/openbgpd:8.7`` and ``pierky/openbgpd:9.2`` images, which must also be present locally.
   Build the Docker image (or pull it from `Dockerhub <https://hub.docker.com/r/pierky/bird/>`_):

   .. code:: bash

      # build the image using the Dockerfile
      # from https://github.com/pierky/dockerfiles
      mkdir ~/dockerfiles
      cd ~/dockerfiles
      curl -o Dockerfile.bird -L https://raw.githubusercontent.com/pierky/dockerfiles/master/bird/1.6.8/Dockerfile
      docker build -t pierky/bird:1.6.8 -f Dockerfile.bird .

      # or pull it from Dockerhub
      docker pull pierky/bird:1.6.8
      docker pull pierky/openbgpd:8.7
      docker pull pierky/openbgpd:9.2

How to run built-in live tests
------------------------------

To run built-in live tests, the full repository must be cloned locally and the environment must be configured as reported above.

To test both the BIRD- and OpenBGPD-based route servers, run the Python unittest using ``pytest``:

   .. code:: bash

      # from within the repository's root
      pytest -vs tests/live_tests/

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

          # Leave this to True in order to allow pytest to use this class
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

7. Run the tests using ``pytest``:

   .. code:: bash

      pytest -vs ~/ars_scenarios/myscenario

Details about the code behind the live tests can be found in the :doc:`LIVETESTS_CODEDOC` section.

Debugging live tests scenarios
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To debug custom scenarios some utilities are provided:

- the ``REUSE_INSTANCES`` environment variable can be set when executing pytest to avoid Docker instances to be torn down at the end of a run.
  When this environment variable is set, BGP speaker instances are started only the first time tests are executed, then are left up and running to allow debugging. When tests are executed again, the BGP speakers' configuration is rebuilt and reloaded. **Be careful**: this mode can be used only when running tests of the same scenario, otherwise Bad Things (tm) may happen.

  Example:

  .. code:: bash

        REUSE_INSTANCES=1 pytest -vs tests/live_tests/scenarios/global/test_bird4.py

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

        BUILD_ONLY=1 pytest -vs tests/live_tests/scenarios/global/test_bird4.py

How to build custom scenarios
-----------------------------

A live test scenario skeleton is provided in the ``pierky/arouteserver/tests/live_tests/skeleton`` directory.

It seems to be a complex thing but actually most of the work is already done in the underlying Python classes and prepared in the skeleton.

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

   - Declare the BGP speakers you want to use in the ``_setup_instances()`` method of the base class.

        .. automethod:: pierky.arouteserver.tests.live_tests.skeleton.base.SkeletonScenario._setup_instances
                :noindex:

        Example:

	.. code-block:: python

	    @classmethod
	    def _setup_instances(cls):
                cls.INSTANCES = [
                    cls.RS_INSTANCE_CLASS(
                        "rs",
                        cls.DATA["rs_IPAddress"],
                        [
                            (
                                cls.build_rs_cfg("bird", "main.j2", "rs.conf"),
                                "/etc/bird/bird.conf"
                            )
                        ]
                    ),
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

5. Edit IP version specific classes within the ``test_bird4.py`` and ``test_bird6.py`` files and set the prefix ID / real IP addresses mapping schema.

   .. autoclass:: pierky.arouteserver.tests.live_tests.skeleton.test_bird4.SkeletonScenario_BIRDIPv4
        :noindex:

   Example:

   .. code-block:: python

      class SkeletonScenario_BIRDIPv4(SkeletonScenario):
      
          # Leave this to True in order to allow nose to use this class
          # to run tests.
          __test__ = True
      
          SHORT_DESCR = "Live test, BIRD, skeleton, IPv4"
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

6. Edit (or add) the template files that, once rendered, will produce the configuration files for the other BGP speakers that are involved in the scenario (the skeleton includes two template files, ``AS1.j2`` and ``AS2.j2``).

   Example:

   .. literalinclude:: ../pierky/arouteserver/tests/live_tests/skeleton/AS2.j2

7. Run the tests using ``nose``:

   .. code:: bash

      nosetests -vs ~/ars_scenarios/myscenario

Details about the code behind the live tests can be found in the :doc:`LIVETESTS_CODEDOC` section.

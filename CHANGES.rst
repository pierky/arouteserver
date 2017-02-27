Change log
==========

v0.2.0
------

- ``setup-templates`` command to just sync local templates with those distributed within a new release.
- Multithreading support for tasks that acquire data from external sources (IRRDB info, PeeringDB max-prefix).

  Can be set using the ``threads`` option in the ``arouteserver.yml`` configuration file.
- New ``template-context`` command, useful to dump the list of context variables and data that can be used inside a template.
- New empty AS-SETs handling: if an AS-SET is empty, no errors are given but only a warning is logged and the configuration building process goes on.

  Any client with IRRDB enforcing enabled and whose AS-SET is empty will have its routes rejected by the route server.

v0.1.2
------

- Fix local files usage among IPv4/IPv6 processes.

  Before of this release, only *.local* files were included into the route server configuration, for both the IPv4 and IPv6 configurations.
  After this, *.local* files continue to be used for both the address families but *.local4* and *.local6* files can also be used to include IP version specific options, depending on the IP version used to build the configuration. Details `here <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#site-specific-custom-configuration-files>`_.

To upgrade:

.. code:: bash

        # pull from GitHub master branch or use pip:
        pip install --upgrade arouteserver

        # install the new template files into local system
        arouteserver setup

v0.1.1
------

- Add local static files into the route server's configuration.

v0.1.0
------

- First beta version.

v0.1.0a11
---------

- The ``filtering.rpsl`` section of general and clients configuration files has been renamed into ``filtering.irrdb``.
- The command line argument ``--template-dir`` has been renamed into ``--templates-dir``.
- New options in the program's configuration file: ``bgpq3_host`` and ``bgpq3_sources``, used to set bgpq3 ``-h`` and ``-S`` arguments when gathering info from IRRDBs.

v0.1.0a10
---------

- New command to build textual representations of configurations: ``html``.

v0.1.0a9
--------

- New command to initialize a custom live test scenario: ``init-scenario``.

v0.1.0a8
--------

- New feature: selective path prepending via BGP communities.
- The ``control_communities`` general option has been removed: it was redundant.

v0.1.0a7
--------

- Improved communities configuration and handling.
- Fix issue on standard communities matching against 32-bit ASNs.
- Fix issue on IPv6 prefix validation.

v0.1.0a6
--------

- New feature: RPKI-based filtering/tagging.
  
v0.1.0a5
--------

- New feature: transit-free ASNs filtering.
- Program command line: subcommands + ``clients-from-peeringdb``.
- More logging and some warning.

v0.1.0a4
--------

- Fix issue with GTSM default value.
- Add default route to bogons.
- Better as-sets handling and cache handling.
- Config syntax change: clients 'as' -> 'asn'.
- AS-SETs at AS-level.
- Live tests: path hiding mitigation scenario.
- Improvements in templates.

v0.1.0a3
--------

- Fix some cache issues.

v0.1.0a2
--------

- Packaging.
- System setup via ``arouteserver --setup``.

v0.1.0a1
--------

First push on GitHub.

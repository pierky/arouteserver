Change log
==========

.. note:: **Upgrade notes**: after upgrading, run the ``arouteserver setup-templates`` command to sync the local templates with those distributed with the new version. More details on the `Upgrading <https://arouteserver.readthedocs.io/en/latest/INSTALLATION.html#upgrading>`_ section of the documentation.

v0.6.0
------

- OpenBGPD 6.1 support: enable large BGP communities support.
- Improvement: the ``clients-from-peeringdb`` command now uses the `IX-F database <http://www.ix-f.net/ixp-database.html>`_ to show a list of IXP and their PeeringDB ID.
- Improvement: enable NEXT_HOP rewriting for IPv6 blackhole filtering requests on OpenBGPD after `OpenBSD 6.1 fixup <https://github.com/openbsd/src/commit/f1385c8f4f9b9e193ff65d9f2039862d3e230a45>`_.

  Related: `issue #3 <https://github.com/pierky/arouteserver/issues/3>`_.
- Improvement: BIRD, client-level `.local file <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#site-specific-custom-config>`_.
- Improvement: next-hop checks, the ``authorized_addresses`` option allows to authorize IP addresses of non-client routers for NEXT_HOP attribute of routes received from a client.

v0.5.0
------

- Fix: avoid the use of standard communities in the range 65535:x.
- Improvement: option to set max-prefix restart timer for OpenBGPD.
- Deleted feature: tagging of routes à la RPKI-Light has been removed.

  - The ``reject_invalid`` flag, that previously was on general scope only, now can be set on a client-by-client basis.
  - The ``roa_valid``, ``roa_invalid``, and ``roa_unknown`` communities no longer exist.

  Related: `issue #4 on GitHub <https://github.com/pierky/arouteserver/issues/4>`_

  This **breaks backward compatibility**.

- New feature: `BIRD hooks <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#bird-hooks>`_ to add site-specific custom implementations.
- Improvement: `BIRD local files <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#site-specific-custom-config>`_.

  This **breaks backward compatibility**: previously, \*.local, \*.local4 and \*.local6 files that were found in the same directory where the BIRD configuration was stored were automatically included. Now, only the header([4|6]).local and footer([4|6]).local files are included, depending on the values passed to the ``--use-local-files`` command line argument.
- Improvement: ``setup`` command and program's configuration file.

  The default path of the cache directory (*cache_dir* option) has changed: it was ``/var/lib/arouteserver`` and now it is ``cache``, that is a directory which is relative to the *cfg_dir* option (by default, the directory where the program's configuration file is stored).

v0.4.0
------

- OpenBGPD support (some `limitations <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#caveats-and-limitations>`_ apply).
- Add MD5 password support on clients configuration.
- The ``build`` command used to generate route server configurations has been removed in favor of BGP-speaker-specific sub-commands: ``bird`` and ``openbgpd``.

v0.3.0
------

- New ``--test-only`` flag for builder commands.
- New ``--clients-from-euroix`` `command <https://arouteserver.readthedocs.io/en/latest/USAGE.html#create-clients-yml-file-from-euro-ix-member-list-json-file>`_ to build the ``clients.yml`` file on the basis of records from an `Euro-IX member list JSON file <https://github.com/euro-ix/json-schemas>`_.

  This also allows the `integration <https://arouteserver.readthedocs.io/en/latest/USAGE.html#ixp-manager-integration>`_ with `IXP-Manager <https://github.com/inex/IXP-Manager>`_.
- New BGP communities: add NO_EXPORT and/or NO_ADVERTISE to any client or to specific peers.
- New option (set by default) to automatically add the NO_EXPORT community to blackhole filtering announcements.

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

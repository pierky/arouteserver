Change log
==========

.. note:: **Upgrade notes**: after upgrading, run the ``arouteserver setup-templates`` command to sync the local templates with those distributed with the new version. More details on the `Upgrading <https://arouteserver.readthedocs.io/en/latest/INSTALLATION.html#upgrading>`__ section of the documentation.

v0.14.1
-------

- Fix: BIRD, "Unknown instruction 8574 in same (~)" error when reloading IPv6 configurations.

  A `missing case <http://bird.network.cz/pipermail/bird-users/2017-January/010880.html>`__ for the ``!~`` operator triggers this bug when neighbors are established and trying to reload bird6 configuration.

  Related: `issue #20 on GitHub <https://github.com/pierky/arouteserver/issues/20>`_.

v0.14.0
-------

This release **breaks backward compatibility** (OpenBGPD configs only): for OpenBGPD configurations, starting with this release the Site of Origin Extended BGP communities in the range 65535:* (``soo 65535:*``) are reserved for internal reasons.

- New feature: use RPKI ROAs as if they were route objects.

  This feature allows to accept those routes whose origin ASN is authorized by a client AS-SET, whose prefix is not but it is covered by a RPKI ROA for the same origin ASN.

  Related: `issue #19 on GitHub <https://github.com/pierky/arouteserver/issues/19>`_.

- New feature: automatic checking for new releases.

  This can be disabled by setting ``check_new_release`` to False in ``arouteserver.yml``.

- Improvement: routes accepted solely because of a ``white_list_route`` entry are now tagged with the ``route_validated_via_white_list`` BGP community.

- Fix: on OpenBGPD configurations, in case of duplicate definition of a client's AS-SETs, duplicate BGP informational communities were added after the IRR validation process.

v0.13.0
-------

- New feature: an option to set RFC1997 well-known communities (NO_EXPORT/NO_ADVERTISE) handling policy: pass-through or strict RFC1997 behaviour.

  This **breaks backward compatibility**: previously, NO_EXPORT/NO_ADVERTISE communities were treated accordingly to the default implementation of the BGP speaker daemon (BIRD, OpenBGPD). Now, ARouteServer's default setting is to treat routes tagged with those communities transparently, that is to announce them to other clients and to pass-through the original RFC1997 communities.

- Improvement: when using PeeringDB records to configure the max-prefix limits, a margin is took into account to accomodate networks that fill the PeeringDB records with their exact route announcement count.

  This **breaks backward compatibility**: if using max-prefix from PeeringDB, current limits will be raised by the default increment values (+100, +15%): this behaviour can be reverted to the pre-v0.13.0 situation by explicitly setting the ``max_prefix.peering_db.increment`` configuration section to ``0/0``.

  Related: `issue #12 on GitHub <https://github.com/pierky/arouteserver/issues/12>`_.

- New feature: client-level white lists for IRRdb-based filters.

  This allows to manually enter routes that must always be accepted by IRRdb-level checks and prefixes and ASNs that must be treated as if they were included within client's AS-SETs.

  Related: `issue #16 on GitHub <https://github.com/pierky/arouteserver/issues/16>`_.

v0.12.3
-------

- Improvement: always take the AS*n* macro into account when building IRRdb-based filters.

  Related: `issue #15 on GitHub <https://github.com/pierky/arouteserver/issues/15>`_.
  
v0.12.2
-------

- Fix: an issue on OpenBGPD builder class was preventing features offered via large BGP communities only from being actually implemented into the final configuration.

  Related: `issue #11 on GitHub <https://github.com/pierky/arouteserver/issues/11>`_.

v0.12.1
-------

- Fix an issue that was impacting templates upgrading under certain circumstances.

  Related: `issue #10 on GitHub <https://github.com/pierky/arouteserver/issues/10>`_.

v0.12.0
-------

- OpenBGPD 6.2 support.

- New feature: `Graceful BGP session shutdown <https://tools.ietf.org/html/draft-ietf-grow-bgp-gshut-11>`_ support, to honor GRACEFUL_SHUTDOWN communities received from clients and also to perform graceful shutdown of the route server itself (``--perform-graceful-shutdown`` `command line argument <https://arouteserver.readthedocs.io/en/latest/USAGE.html#perform-graceful-shutdown>`__).

v0.11.0
-------

- Python 3.4 support.

- Improvement: GT registry removed from the sources used to gather info from IRRDB.

  Related: `PR #8 on GitHub <https://github.com/pierky/arouteserver/pull/8>`_.

- Improvement: multiple AS-SETs used for the same client are now grouped together and queried at one time.
  This allows to leverage bgpq3's ability and speed to aggregate results in order to have smaller configuration files.

v0.10.0
-------

- New feature: when IRRDB-based filters are enabled and no AS-SETs are configured for a client, if the ``cfg.filtering.irrdb.peering_db`` option is set ARouteServer tries to fetch their values from the client's ASN record on PeeringDB.

  Related: `issue #7 on GitHub <https://github.com/pierky/arouteserver/issues/7>`_.

- Improvement: config building process performances,

  - reduced memory consumption by moving IRRDB information from memory to temporary files;

  - responses for empty/missing resources are also cached;

  - fix a wrong behaviour that led to multiple PeeringDB requests for the same ASN.

- Improvement: ``clients-from-euroix`` command, the new ``--merge-from-peeringdb`` option can be used to integrate missing information into the output clients list by fetching AS-SETs and max-prefix limit from PeeringDB.

v0.9.3
------

- Fix: OpenBGPD, an issue was causing values > 65535 to be used in standard BGP communities matching.

v0.9.2
------

- Fix: remove quotes from clients description.

- Fix: OpenBGPD, syntax error for prefix lists with 'range X - X' format.

- Fix: ``clients-from-euroix`` command, members with multiple ``vlan`` objects with the same ``vlan_id`` were not properly listed in the output, only the first object was used.

v0.9.1
------

- Improvement: BIRD, new default debug options (``states, routes, filters, interfaces, events``, was ``all``).

  If needed, they can be overwritten using the ``header`` `custom .local file <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#site-specific-custom-config>`_.

- Fix: *enrichers* errors handling reported a generic message with no further details.

- Fix: HTTP 404 error handling for "Entity not found" error from PeeringDB.

- Fix: OpenBGPD, large prefix lists were causing a "string too long" error.

- Fix: OpenBGPD, clients descriptions longer than 31 characters were not properly truncated.

v0.9.0
------

- New feature: RTT-based communities to control propagation of routes on the basis of peers round trip time.

- Improvement: in conjunction with the "tag" reject policy, the ``rejected_route_announced_by`` BGP community can be used to track the ASN of the client that announced an invalid route to the server.

- Fix: when the "tag" reject policy is used, verify that the ``reject_cause`` BGP community is also set.

v0.8.1
------

- Fix: default user configuration path not working.

v0.8.0
------

- New feature: `reject policy <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#reject-policy>`_ configuration option, to control how invalid routes must be treated: immediately discarded or kept for troubleshooting purposes, analysis or statistic reporting.

- New tool: `invalid routes reporter <https://arouteserver.readthedocs.io/en/latest/TOOLS.html>`_.

- Fix: the following networks have been removed from the bogons.yml file: 193.239.116.0/22, 80.249.208.0/21, 164.138.24.80/29.

v0.7.0
------

- New feature: `custom BGP communities <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#custom-bgp-communities>`_ can be configured on a client-by-client basis to tag routes entering the route server (for example, for informative purposes).
- Fix: validation of BGP communities configuration for OpenBGPD.

  Error is given if a peer-AS-specific BGP community overlaps with another community, even if the last part of the latter is a private/reserved ASN.
- Improvement: the custom ``!include <filepath>`` statement can be used now in YAML configuration files to include other files.

  More details `here <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#yaml-files-inclusion>`__.
- Improvement: IRRDB-based filters can be configured to allow more specific prefixes (``allow_longer_prefixes`` option).

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
  After this, *.local* files continue to be used for both the address families but *.local4* and *.local6* files can also be used to include IP version specific options, depending on the IP version used to build the configuration. Details `here <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#site-specific-custom-configuration-files>`__.

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

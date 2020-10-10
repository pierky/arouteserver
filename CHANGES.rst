Change log
==========

.. note:: **Upgrade notes**: after upgrading, run the ``arouteserver setup-templates`` command to sync the local templates with those distributed with the new version. More details on the `Upgrading <https://arouteserver.readthedocs.io/en/latest/INSTALLATION.html#upgrading>`__ section of the documentation.

v1.0.0
------

- No changes, just make it "stable"!

v0.26.0
-------

- New: Add support for OpenBGPD/OpenBSD 6.7 and OpenBGPD Portable 6.7p0, also added to the integration testing suite.

v0.25.1
-------

- Fix: BIRD, use ``bgp_path.last``  since it's consistent with `RFC 6907 7.1.9-11 <https://tools.ietf.org/html/rfc6907#section-7.1.9>` (RPKI BOV of routes whose AS_PATH ends with an AS_SET).

  More info: https://www.mail-archive.com/bird-users@network.cz/msg05152.html

  Related: `PR #56 on GitHub <https://github.com/pierky/arouteserver/pull/56>`_.

v0.25.0
-------

- New feature: ``tag_and_reject`` reject policy for BIRD.

  Invalid routes can be tagged with informational BGP communities and then discarded by BIRD.
  With this option, alice-lg reject reasons are supported nicely, whilst keeping ``show routes all filtered`` working to keep birdwatcher happy.

  Related: `PR #57 on GitHub <https://github.com/pierky/arouteserver/pull/57>`_.

- Improvement: ``clients-from-euroix`` command, option ``--merge-from-custom-file`` to customise the list of clients generated from an Euro-IX JSON file.

  More details on how to use this option can be found running ``arouteserver clients-from-euroix --help-merge-from-custom-file``.

v0.24.1
-------

- Improvement: add support for `bgpq4 <https://github.com/bgp/bgpq4>`_.

  At least version 0.0.5 is required.

  Related: `PR #53 on GitHub <https://github.com/pierky/arouteserver/pull/53>`_.

- Fix: ``clients-from-euroix`` command, route server detection on Euro-IX schema versions 0.7 and 1.0.

  In version 0.7 and 1.0 of the `Euro-IX member list JSON file <https://github.com/euro-ix/json-schemas>`_ the way the route server information are exported changed. The ``clients-from-euroix`` command was no longer able to filter out the IP addresses that represent the route server of the same IXP for which the members are processed, basically generating a client entry for the same route server being configured.

v0.24.0
-------

- New feature: *never via route-servers* ASNs filtering.

  To drop routes containing an ASN which is classified as "never via route-servers" on PeeringDB (`info_never_via_route_servers` `attribute <https://github.com/peeringdb/peeringdb/issues/394>`_).

  **Please note**: this feature is enabled by default.

  Related: `issue #55 on GitHub <https://github.com/pierky/arouteserver/issues/55>`_.

- Improvement: add `alice-lg/birdwatcher <https://github.com/alice-lg/birdwatcher>`_ support to BIRD configs.

  Changes the default BIRD time format to support `alice-lg/birdwatcher <https://github.com/alice-lg/birdwatcher>`_ out of the box.

- Improvement: include a table with the reject codes in the HTML output.

  Related: `issue #54 on GitHub <https://github.com/pierky/arouteserver/issues/54>`_.

v0.23.0
-------

- New: add support for BIRD v2.

  **Please note**: BIRD v2 support is in early stages. Before moving any production platform to instances of BIRD v2 configured with this tool, please review the configurations carefully and run some simulations.

- New: OpenBGPD/OpenBSD 6.6, OpenBGPD Portable 6.6p0 and BIRD 1.6.8 added to the integration testing suite.

v0.22.2
-------

- Fix: prevent environment variables with unknown escapes (like `\u`) from interrupting the execution.

  Related: `issue #50 on GitHub <https://github.com/pierky/arouteserver/issues/50>`_.

v0.22.1
-------

- Fix: handle more formats for ROAs exported from the public instances of RIPE and NTT validators.

  A new way of representing ASNs (without the "AS" prefix) and new TA names which were not matched by the default values of ``rpki_roas.allowed_trust_anchors`` prevented ROAs from being imported and correctly processed when the default settings were used.

v0.22.0
-------

This is the last release of ARouteServer for which Python 2.7 compatibility is guaranteed. From the next release, any new feature will not be tested against that version of Python.

- New: `OpenBGPD Portable <https://github.com/openbgpd-portable/openbgpd-portable>` (release 6.5p1) also supported.

  Release 6.5p1 of OpenBGPD Portable edition passed the integration testing suite.

- New: add support for OpenBGPD/OpenBSD 6.5 enhancements.

  Support for matching multiple communities at the same time allows to create more readable configurations.

- Improvement: OpenBGPD, some filters refinement.

  Avoid checking AS0 in AS_PATH since 6.4.
  No needs to check routes of an address family different than the one used for the session.

As announced with release 0.20.0, OpenBGPD/OpenBSD 6.2 is no longer tested. Also OpenBGPD/OpenBSD 6.3 tests have been decommissioned.
Starting with this release, tests will be executed only against the 2 most recent releases of OpenBGPD/OpenBSD and against the last release of the supported major versions of BIRD.
The implementation of new features may break compatibility of the configurations built for unsupported releases.

v0.21.1
-------

- Deprecation: SAVVIS IRR removed from the list of default sources used by bgpq3.

- Fix (minor): truncate the max length of AS-SET names to 64 characters.

  BIRD supports only names no longer than 64 characters.

  Related: `issue #47 on GitHub <https://github.com/pierky/arouteserver/issues/47>`_.

v0.21.0
-------

- Improvement: when ``ripe-rpki-validator-cache`` is set as the source of ROAs, multiple URLs can now be specified to fetch data from.

  URLs will be tried in the same order as they are configured; if the attempt to download ROAs from the first URL fails, the second URL will be tried, an so on.

  By default, the `RIPE NCC public instance <https://rpki-validator.ripe.net/>`_ of the RIPE RPKI Validator will be tried first, then the `NTT instance <https://rpki.gin.ntt.net/>`_. The list of URLs can be set in the ``general.yml`` configuration file, ``roas.ripe_rpki_validator_url`` option.

v0.20.0
-------

This is the last release of ARouteServer for which OpenBGPD/OpenBSD 6.1 and 6.2 CI tests are ran. From the next release, any new feature will not be tested against these versions of OpenBGPD. Users are encouraged to move to newer releases.

- New: add support for OpenBGPD/OpenBSD 6.4 `enhancements <https://ripe77.ripe.net/presentations/143-openbsd-status.pdf>`_.

  Use new sets for prefixes, ASNum, and origins (prefix + source-as), and also RPKI ROA sets.

- Improvement: OpenBGPD, reduce the number of rules by combining some into the same rule.

- Improvement: route server policies definition files built using the ``configure`` command now have RPKI BGP Origin Validation and "use-ROAs-as-route-objects" enabled by default.

As announced with release 0.19.0, OpenBGPD/OpenBSD 6.0 is no longer tested.
The implementation of new features may break compatibility of the configurations built for unsupported releases.

Most of this release is based on the work made by `Claudio Jeker <https://github.com/cjeker>`_.

v0.19.1
-------

- Fix (BIRD configuration only): change ``bgp_path.last`` with ``bgp_path.last_nonaggregated``.

  When a route is originated from the aggregation of two different routes using the AS_SET, ``bgp_path.last`` always returns 0, so the origin ASN validation against IRR always fails.

  Related: `issue #34 on GitHub <https://github.com/pierky/arouteserver/issues/34>`_.

v0.19.0
-------

This is the last release of ARouteServer for which OpenBGPD/OpenBSD 6.0 CI tests are ran. Starting with the next release, any new feature will not be tested against version 6.0 of OpenBGPD. Users are encouraged to move to newer releases.

- New: use NIC.BR Whois data from Registro.br to enrich the dataset used for route validation.

  Details: `RIPE76, Practical Data Sources For BGP Routing Security <https://ripe76.ripe.net/presentations/43-RIPE76_IRR101_Job_Snijders.pdf>`_.

  Related: `issue #28 on GitHub <https://github.com/pierky/arouteserver/issues/28>`_.

- New: introduce support for OpenBGPD/OpenBSD 6.4.

  OpenBSD 6.4 is not released yet, this is just in preparation of it.

  Related: `issue #31 on GitHub <https://github.com/pierky/arouteserver/issues/31>`_.

- Fix (minor): RIPE NCC RPKI Validator v3 expects ``Accept: text/json`` as HTTP header.

  Related: `PR #29 on GitHub <https://github.com/pierky/arouteserver/issues/29>`_.

v0.18.0
-------

- New: add support for BIRD 1.6.4 and OpenBGPD/OpenBSD 6.3.

  This release **breaks backward compatibility** (OpenBGPD configs only): the default target version used to build OpenBGPD configurations (when the ``--target-version`` argument is not given) is now 6.2; previously it was 6.0. Use the ``--target-version 6.0`` command line argument to build 6.0 compatible configurations.

- Improvement: transit-free ASNs filters are applied also to sessions toward transit-free peers.

  Related: `issue #21 on GitHub <https://github.com/pierky/arouteserver/issues/21>`_.

- Fix (minor): better handling of user answers in ``configure`` and ``setup`` commands.

- Fix: ``clients-from-peeringdb``, list of IXPs retrieved from PeeringDB and no longer from IXFDB.

v0.17.3
-------

- Fix: ``clients-from-euroix`` command, use the configured cache directory.

v0.17.2
-------

- Fix: ``configure`` command, omit extended communities for OpenBGPD configurations.

  This is to avoid the need of using the ``--ignore-issues extended_communities`` command line argument.

- Improvement: environment variables expansion when YAML configuration files are read.

v0.17.1
-------

- Fix: minor installation issues.

v0.17.0
-------

- New feature: allow to set the source of IRR objects.

  AS-SETs can be prepended with an optional source: ``RIPE::AS-FOO``, ``RIPE::AS64496:AS-FOO``.

- New feature: support for RPKI-based Origin Validation added to OpenBGPD configurations.

  RPKI ROAs must be loaded from a RIPE RPKI Validator cache file (local or via HTTP).
  Mostly inspired by Job Snijders' tool https://github.com/job/rtrsub

- Improvement: RPKI ROAs can be loaded from a local file too.

  The file must be in RIPE RPKI Validator cache format.

- Fix (minor): remove internal communities before accepting blackhole routes tagged with a custom blackhole community.

  This bug did not affect routes tagged with the BLACKHOLE community; anyway, the internal communities were scrubbed before routes were announced to clients.

v0.16.2
-------

- Fix: avoid empty lists of prefixes when a client's ``white_list_pref`` contains only prefixes for an IP version different from the current one.

v0.16.1
-------

- Fix: handle the new version of the JSON schema built by `arin-whois-bulk-parser <https://github.com/NLNOG/arin-whois-bulk-parser>`__.

v0.16.0
-------

- Improvement: OpenBGPD, more flexibility for inbound communities values.

  This allows to use inbound 'peer_as' communities which overlap with other inbound communities whose last *part* is a private ASN.

- New feature: use ARIN Whois database dump to authorize routes.

  This feature allows to accept those routes whose origin ASN is authorized by a client AS-SET, whose prefix has not a corresponding route object but is covered by an ARIN Whois record for the same origin ASN.

- Improvement: extend the use of *RPKI ROAs as route objects* and *ARIN Whois database dump* to ``tag_as_set``-only mode.

  Before of this, the *RPKI ROAs as route objects* and *ARIN Whois DB dump* features were used only when origin AS and prefix enforcing was set.
  Starting with this release they are used even when enforcing is not configured and only the ``tag_as_set`` mode is used.

v0.15.0
-------

- New feature: ``configure`` and ``show_config`` *support* commands.

  - ``configure``: it can be used to quickly generate a route server policy definition file (``general.yml``) on the basis of best practices and suggestions.

  - ``show_config``: to display current configuration settings and also options that have been left to their default values.

- New feature: ``ixf-member-export`` command, to build `IX-F Member Export JSON files <https://ml.ix-f.net/>`__ from the list of clients.

- Improvement: cache expiry time values can be set for each external resource type: PeeringDB info, IRR data, ...

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
- Deleted feature: tagging of routes a' la RPKI-Light has been removed.

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

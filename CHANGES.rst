Change log
==========

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

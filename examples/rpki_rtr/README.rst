BIRD v2/v3 and OpenBGPD RPKI RTR configuration
----------------------------------------------

This is an example of how to use BIRD v2/v3 or OpenBGPD with an external source for RPKI ROAs and ASPAs based on the RTR protocol.

BIRD v2/v3 and OpenBGPD (starting with release 6.9) have built-in support for the RTR protocol, that allows to connect the BGP daemon directly to a local cache (a "validator").

To configure the daemons with ARouteServer in order to fetch ROAs and ASPAs using RTR, the ``rpki_roas.source`` and ``rpki_aspas.source`` options must be set to ``rtr`` and a local *rpki_rtr_config.local* file must be placed inside the same directory where the main configuration file is created (*/etc/bird* or */etc/bgpd* by default, or a custom one set using the ``--local-files-dir`` command line argument of ARouteServer).

The *rpki_rtr_config.local* file is expected to contain the snippet of BIRD or OpenBGPD config needed to setup one or more RTR sessions:

- BIRD v2/v3: https://bird.network.cz/?get_doc&v=20&f=bird-6.html#ss6.13

  **Please note:** the names of the tables where ROAs will be injected into must be ``RPKI4`` and ``RPKI6``; the one used for ASPAs must be ``ASPA``.

- OpenBGPD: https://man.openbsd.org/bgpd.conf#rtr

**Please note:** ASPA payloads only exist in version 2 of the RTR protocol (RFC6810 and RFC8210 carry ROAs only). When ``rpki_aspas.source`` is set to ``rtr``, the RTR session configured in the *rpki_rtr_config.local* file must be set to negotiate version 2, using ``min version 2;`` on BIRD and ``min-version 2`` on OpenBGPD. The RPKI validator in use must also be configured to produce ASPAs (for example, Routinator needs the ``enable-aspa`` option).

**Please note:** on OpenBGPD, ASPA verification is performed only on sessions for which a role is set, so ``filtering.roles`` must be enabled as well; ARouteServer raises an error otherwise.

Example configurations are reported in the *rpki_rtr_config.local.BIRD* and *rpki_rtr_config.local.OpenBGPD* files that can be found within this directory.

BIRD v2 RPKI RTR configuration
------------------------------

This is an example of using BIRD v2 with an external source for RPKI ROAs.

BIRD v2 has built-in support for the RTR protocol, that allows to connect the BGP daemon directly to a local cache (a "validator").

To configure BIRD v2 with ARouteServer in order to fetch ROAs using RTR, the ``rpki_roas.source`` option must be set to ``rtr`` and a local *rpki_rtr_config.local* file must be placed inside the same directory where the main BIRD configuration file is created (*/etc/bird* by default, or a custom one set using the ``--local-files-dir`` command line argument of ARouteServer).

The *rpki_rtr_config.local* file is expected to contain the snippet of BIRD config needed to setup a *rpki protocol*, accordingly to what is documented in the official BIRD web site: https://bird.network.cz/?get_doc&v=20&f=bird-6.html#ss6.13

The names of the tables where ROAs will be injected into must be ``RPKI4`` and ``RPKI6``.

An example configuration is reported in the *rpki_rtr_config.local* file that can be found within this directory.

.. DO NOT EDIT: this file is automatically created by /utils/build_doc

Testing realistic scenarios
===========================

Some *realistic* scenarios have been tested using ARouteServer by feeding it with lists of clients pulled from actual IXPs' members lists.

- **Euro-IX JSON member list** files exposed by the IXPs reported below have been used to automatically generate **ARouteServer clients.yml** file.
  AS-SETs and max-prefix limits from PeeringDB have been taken into account when they were not available in the Euro-IX JSON file.

  List of IXPs used to run these tests:

  - AMS-IX, VLAN ID 501 ("ISP")

  - BCIX, VLAN ID 1 ("BCIX Peering LAN")

  - BIX, VLAN ID 1 ("IPv4 Peeing LAN") and 2 ("IPv6 Peeing LAN")

  - GR-IX

  - INEX, VLAN ID 2 ("Peering VLAN #1")

  - LONAP, VLAN ID 1 ("LONAP Peering LAN #1")

  - SIX, VLAN ID 2 ("MTU 1500")

  - STHIX - Stockholm

  - SwissIX
  
  The files produced by the ``clients-from-euroix`` command can be found within the *tests/real/clients* directory (see it `on GitHub <https://github.com/pierky/arouteserver/tree/master/tests/real/clients>`__).

- A **rich ARouteServer setup** has been used to build BIRD and OpenBGPD configurations, in order to enable as many features as possible: filters based on "same AS" NEXT_HOP, invalid AS_PATHs, transit-free ASNs, IRRDB information, and also max-prefix limits and BGP communities for blackhole filtering, selective announcement, prepending...

  The `full description <_static/tests_real_general.html>`__ of the configuration can be found in the *general.html* file, automatically generated from the `general.yml file <https://github.com/pierky/arouteserver/blob/master/tests/real/general.yml>`__.

- For each IXP, configurations for BIRD and OpenBGPD (both 6.0 and 6.2) have been finally built using ARouteServer and loaded into an instance of their respective daemon, to verify that no errors occurred:

  - for BIRD, a Docker container has been used;

  - for OpenBGPD 6.0, a virtual server has been instantiated on `Vultr <https://www.vultr.com/>`__ in order to have enough resources to process the configuration;

  - for OpenBGPD 6.2, only a few configurations were tested because of lack of resources on my machines :-/

**Results** can be found within the *tests/real/last* file `(here on GitHub <https://github.com/pierky/arouteserver/blob/master/tests/real/last>`__).
They are also reported below.

.. literalinclude:: _static/tests_real_results.last

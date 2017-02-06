Configuration
=============

The following files, by default located in ``/etc/arouteserver``, contain configuration options for the program and for the route server's configuration:

- ``arouteserver.yml``: program's options and paths to other files are configured here.
  See its default content on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/arouteserver.yml>`_.

- ``general.yml``: the route server's configuration options and policies.
  See its default content on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/general.yml>`_.

- ``clients.yml``: the list of route server's clients and their options and policies.
  See its default content on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/clients.yml>`_.

- ``bogons.yml``: the list of bogon prefixes automatically discarded by the route server.
  See its default content on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/bogons.yml>`_.

Route server's configuration
----------------------------

Route server's general configuration and policies are outlined in the ``general.yml`` file. 

Configuration details and options can be found within the distributed `general <https://github.com/pierky/arouteserver/blob/master/config.d/general.yml>`_ and `clients <https://github.com/pierky/arouteserver/blob/master/config.d/clients.yml>`_ configuration files on GitHub.

Details about some particular topics are reported below.

.. contents::
   :local:

Client-level options inheritance
********************************

Clients, which are configured in the ``clients.yml`` file, inherit most of their options from those provided in the ``general.yml`` file, unless their own configuration sets more specific values.

Options that are inherited by clients and that can be overwritten by their configuration are highlighted in the ``general.yml`` template file that is distributed with the project.

Example:

**general.yml**

.. code:: yaml

   cfg:
     rs_as: 999
     router_id: "192.0.2.2"
     passive: True
     gtsm: True

**clients.yml**

.. code:: yaml

   clients:
     - asn: 11
       ip: "192.0.2.11"
     - asn: 22
       ip: "192.0.2.22"
       passive: False
     - asn: 33
       ip: "192.0.2.33"
       passive: False
       gtsm: False

In this scenario, the route server's configuration will look like this:

- a passive session with GTSM enabled toward AS11 client;
- an active session with GTSM enabled toward AS22 client;
- an active session with GTSM disabled toward AS33 client.

IRRDBs-based filtering
**********************

The ``filtering.rpsl`` section of the configuration files allows to use IRRDBs information to filter or to tag prefixes entering the route server. Information are acquired using the external program `bgpq3 <https://github.com/snar/bgpq3>`_: installations details on :doc:`INSTALLATION` page.

One or more AS-SETs can be used to gather information about authorized origin ASNs and prefixes that a client can announce to the route server. AS-SETs can be set in the ``clients.yml`` file on a two levels basis:

- within the ``asns`` section, one or more AS-SETs can be given for each ASN of the clients configured in the rest of the file;

- for each client, one or more AS-SETs can be configured in the ``cfg.filtering.rpsl`` section.

To gather information from the IRRDBs, at first the script uses the AS-SETs provided in the client-level configuration; if no AS-SETs are provided there, it looks to the ASN configuration. If no AS-SETs are found in both the client and the ASN configuration, only the ASN's autnum object will be used.

Example:

**clients.yml**

.. code:: yaml

   asns:
     AS22:
       as_sets:
         - "AS-AS22MAIN"
     AS33:
       as_sets:
         - "AS-AS33GLOBAL"
   clients:
     - asn: 11
       ip: "192.0.2.11"
       cfg:
         filtering:
           rpsl:
             as_sets:
               - "AS-AS11NETS"
     - asn: 22
       ip: "192.0.2.22"
     - asn: 33
       ip: "192.0.2.33"
       cfg:
         filtering:
           rpsl:
             as_sets:
               - "AS-AS33CUSTOMERS"
     - asn: 44
       ip: "192.0.2.44"

With this configuration, the following values will be used to run the bgpq3 program:

- **AS-AS11NETS** will be used for 192.0.2.11 (it's configured at client-level for that client);
- **AS-AS22MAIN** for the 192.0.2.22 client (it's inherited from the ``asns``-level configuration of AS22, client's AS);
- **AS-AS33CUSTOMERS** for the 192.0.2.33 client (the ``asns``-level configuration is ignored because a more specific one is given at client-level);
- **AS44** for the 192.0.2.44 client, because no AS-SETs are given at any level.

RPKI-based filtering
********************

RPKI-based validation of prefixes can be configured using the general ``filtering.rpki`` section. Depending on the ``reject_invalid`` configuration, prefixes can be rejected or tagged with BGP communities.

To acquire RPKI data and load them into BIRD, a couple of external tools from the `rtrlib <http://rpki.realmv6.org/>`_ suite are used: `rtrlib <https://github.com/rtrlib>`_ and `bird-rtrlib-cli <https://github.com/rtrlib/bird-rtrlib-cli>`_. One or more trusted local validating caches should be used to get and validate RPKI data before pushing them to BIRD. An overview is provided on the `rtrlib GitHub wiki <https://github.com/rtrlib/rtrlib/wiki/Background>`_, where also an `usage guide <https://github.com/rtrlib/rtrlib/wiki/Usage-of-the-RTRlib>`_ can be found.

BGP Communities
***************

BGP communities can be used for many features in the configurations built using ARouteServer: blackhole filtering, AS_PATH prepending, announcement control, various informative purposes (valid ASN, RPKI status, ...) and more. All these communities are referenced by *name* (or *tag*) in the configuration files and their real values are reported only once, in the ``communities`` section of the ``general.yml`` file.
For each community, values can be set for any of the three *formats*: standard (`RFC1997 <https://tools.ietf.org/html/rfc1997>`_), extended (`RFC4360 <https://tools.ietf.org/html/rfc4360>`_/`RFC5668 <https://tools.ietf.org/html/rfc5668>`_) and large (`draft-ietf-idr-large-community <https://tools.ietf.org/html/draft-ietf-idr-large-community>`_).

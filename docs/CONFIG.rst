Configuration
=============

Program configuration
---------------------

ARouteServer needs the following files to read its own configuration and to determine the policies to be implemented in the route server:

- ``arouteserver.yml``: the main ARouteServer configuration file; it contains options and paths to other files (templates, cache directory, external tools...). By default, ARouteServer looks for this file in ``~/arouteserver`` and ``/etc/arouteserver``. This path can be changed using the ``--cfg`` command line argument. See its default content on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/arouteserver.yml>`__.

  The ``logging_config_file`` parameter here included can be used to :doc:`configure logging <LOGGING>`.

  For details regarding the ``rtt_getter_path`` option please see :doc:`RTT_GETTER`.

- ``general.yml``: this is the most important configuration file, where the route server's options and policies are configured.
  By default, it is located in the same directory of the main configuration file; its path can be set with the ``cfg_general`` option in ``arouteserver.yml``.
  See its default content on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/general.yml>`__.

  An automatically generated *reStructuredText* version of the file with all its options and comments can be found in the :doc:`GENERAL` page.

- ``clients.yml``: the list of route server's clients and their options and policies.
  By default, it is located in the same directory of the main configuration file; its path can be set with the ``cfg_clients`` option in ``arouteserver.yml``.
  See its default content on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/clients.yml>`__.

- ``bogons.yml``: the list of bogon prefixes automatically discarded by the route server.
  By default, it is located in the same directory of the main configuration file; its path can be set with the ``cfg_bogons`` option in ``arouteserver.yml``.
  See its default content on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/bogons.yml>`__.

The ``arouteserver setup`` command can be used to setup the environment where ARouteServer is executed and to install the aforementioned files in the proper places.

Route server's configuration
----------------------------

Route server's general configuration and policies are outlined in the ``general.yml`` file.

Configuration details and options can be found within the distributed `general <https://github.com/pierky/arouteserver/blob/master/config.d/general.yml>`__ and `clients <https://github.com/pierky/arouteserver/blob/master/config.d/clients.yml>`__ configuration files on GitHub or in the :doc:`GENERAL` page.

Details about some particular topics are reported below.

.. contents::
   :local:

YAML files inclusion and environment variables expansion
********************************************************

ARouteServer's YAML configuration files can contain a custom directive (``!include <filepath>``) that can be used to include other files.
Moreover, environment variables (``${VAR_NAME}``) are expanded when the configuration files are loaded.
This can be useful, for example, when the same configuration is shared by two route servers that differ only in their router ID.

Example with environment variables expansion:

**general.yml**

.. code:: yaml

   cfg:
     router_id: "${ROUTER_ID}"
     rs_as: 999
     passive: True
     gtsm: True
     filtering:
       [...]

Example with file inclusion:

**general-rs1.yml**

.. code:: yaml

   cfg:
     router_id: "192.0.2.1"
     !include general-shared.yml

**general-rs2.yml**

.. code:: yaml

   cfg:
     router_id: "192.0.2.2"
     !include general-shared.yml

**general-shared.yml**

.. code:: yaml

   #cfg:
   # keep the indentation level of the line where
   # the !include statement is placed
     rs_as: 999
     passive: True
     gtsm: True
     filtering:
       [...]

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
       cfg:
         passive: False
         gtsm: False

In this scenario, the route server's configuration will look like this:

- a passive session with GTSM enabled toward AS11 client;
- an active session with GTSM enabled toward AS22 client;
- an active session with GTSM disabled toward AS33 client.

IRRDBs-based filtering
**********************

The ``filtering.irrdb`` section of the configuration files allows to use IRRDBs information to filter or to tag routes entering the route server. Information are acquired using the external program `bgpq3 <https://github.com/snar/bgpq3>`_ or `bgpq4 <https://github.com/bgp/bgpq4>`_: installations details on :doc:`INSTALLATION` page.

One or more AS-SETs can be used to gather information about authorized origin ASNs and prefixes that a client can announce to the route server. AS-SETs can be set in the ``clients.yml`` file on a two levels basis:

- within the ``asns`` section, one or more AS-SETs can be given for each ASN of the clients configured in the rest of the file;

- for each client, one or more AS-SETs can be configured in the ``cfg.filtering.irrdb`` section.

To gather information from the IRRDBs, at first the script uses the AS-SETs provided in the client-level configuration; if no AS-SETs are provided there, it looks to the ASN configuration.
If no AS-SETs are found in both the client and the ASN configuration, if the ``cfg.filtering.irrdb.peering_db`` option is set to True the AS-SET from PeeringDB is used ("IRR Record" field).
The ASN's autnum object will be used in any case.

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
           irrdb:
             as_sets:
               - "AS-AS11NETS"
     - asn: 22
       ip: "192.0.2.22"
     - asn: 33
       ip: "192.0.2.33"
       cfg:
         filtering:
           irrdb:
             as_sets:
               - "AS-AS33CUSTOMERS"
     - asn: 44
       ip: "192.0.2.44"

With this configuration, the following values will be used to run the bgpq3/bgpq4 program:

- **AS-AS11NETS** will be used for 192.0.2.11 (it's configured at client-level for that client);
- **AS-AS22MAIN** for the 192.0.2.22 client (it's inherited from the ``asns``-level configuration of AS22, client's AS);
- **AS-AS33CUSTOMERS** for the 192.0.2.33 client (the ``asns``-level configuration is ignored because a more specific one is given at client-level);
- **AS44** for the 192.0.2.44 client, because no AS-SETs are given at any level. In this case, if the ``cfg.filtering.irrdb.peering_db`` was set to True, the AS-SET from PeeringDB would be used.

Optionally, the source that must be used to expand the AS macro can be prepended, followed by two colon characters: **RIPE::AS-FOO**, **RADB::AS64496:AS-FOO**.

Use RPKI ROAs as if they were route objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the ``filtering.irrdb.use_rpki_roas_as_route_objects`` option is enabled, RPKI ROAs are used as if they were route objects to validate routes whose origin ASN is already authorized by a client's AS-SET but whose prefix is not. A lookup into the ROA table is made on the basis of the route origin ASN and, if a covering ROA is found, the route is validated. In this case, if the ``filtering.irrdb.tag_as_set`` general option is True the ``prefix_validated_via_rpki_roas`` informative community is added to the route.

Please refer to `ROAs sources`_ in order to configure the source that should be used to gather RPKI ROAs.

Use ARIN Whois database to accept routes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similarly to the previous option, ``filtering.irrdb.use_arin_bulk_whois_data`` allows to support IRR-based filters with additional data. Records from the ARIN Whois database are used to accept those routes whose origin ASN is authorized by the client's AS-SET but whose prefix has not a registered route object. In this case, a lookup into the ARIN Whois database is made on the basis of the origin ASN and if a covering entry is found the route is accepted.

The ARIN Whois database can be obtained by signing an `agreement with ARIN <https://www.arin.net/resources/request/bulkwhois.html>`__. It must be then converted into the appropriate JSON format that ARouteServer expects to find; the `arin-whois-bulk-parser <https://github.com/NLNOG/arin-whois-bulk-parser>`__ script can be used for this purpose.

A parsed version of the database dump is offered by `NLNOG <https://nlnog.net/>`__ at the following URL: http://irrexplorer.nlnog.net/static/dumps/arin-whois-originas.json.bz2

Further details can be found in `this message <https://mailman.nanog.org/pipermail/nanog/2017-December/093525.html>`__ appeared on the NANOG mailing list.

White lists
~~~~~~~~~~~

In addition to prefixes and ASNs gathered as said above, white lists can be configured at client level to manually enter prefixes and origin ASNs that will be treated as if they were included within clients' AS-SET.

If the ``filtering.irrdb.tag_as_set`` general option is also set to True, routes that fail the basic IRR filters but that are accepted solely because they match a white list entry are tagged with the ``prefix_not_present_in_as_set`` and ``origin_not_present_in_as_set`` informational communities.

Example:

.. code:: yaml

   clients:
     - asn: 11
       ip: "192.0.2.11"
       cfg:
         filtering:
           irrdb:
             as_sets:
               - "AS-AS11NETS"
             white_list_route:
               - prefix: "203.0.113.0"
                 length: 24
                 asn: 65534

This configuration allows to authorize routes for 203.0.113.0/24{24-32} with origin ASN 65534 received from the client.

RPKI
****

ROAs sources
~~~~~~~~~~~~

A couple of methods can be used to acquire RPKI data (ROAs):

- (BIRD and OpenBGPD) the builtin method based on `RIPE RPKI Validator format <https://rpki-validator.ripe.net>`__ JSON export file (also generated by other validators like Routinator, rpki-client, OctoRPKI): the URL of a local and trusted instance of a RPKI validator should be provided to ensure that a trusted dataset is used. By default, the URLs of some  public instances are used.

- (BIRD only) external resources can be used to pull ROAs from using the RTR protocol:

  - BIRD 1.6.x: the `rtrlib <http://rpki.realmv6.org/>`_ suite: `rtrlib <https://github.com/rtrlib>`__ and `bird-rtrlib-cli <https://github.com/rtrlib/bird-rtrlib-cli>`__.

  - BIRD v2: the `built-in RTR protocol <https://bird.network.cz/?get_doc&v=20&f=bird-6.html#ss6.13>`_ implementation.

  One or more trusted local validating caches should be used to get and validate ROAs before pushing them to BIRD. An overview is provided on the `rtrlib GitHub wiki <https://github.com/rtrlib/rtrlib/wiki/Background>`__, where also an `usage guide <https://github.com/rtrlib/rtrlib/wiki/Usage-of-the-RTRlib>`__ can be found. For BIRD v2, an example of how to configure the RTR protocol can be found in the ``examples/bird2_rpki_rtr`` directory (`also on GitHub <https://github.com/pierky/arouteserver/tree/master/examples/bird2_rpki_rtr>`_).

The configuration of ROAs source can be done within the ``rpki_roas`` section of the ``general.yml`` file.

Origin validation
~~~~~~~~~~~~~~~~~

RPKI-based validation of routes can be configured using the general ``filtering.rpki_bgp_origin_validation`` section.
RFC8097 BGP extended communities are used to mark routes on the basis of their validity state.
Depending on the ``reject_invalid`` configuration, INVALID routes can be rejected before entering the route server or accepted for further processing by external tools or functions provided within :ref:`.local files <site-specific-custom-config>`.
INVALID routes are not propagated to clients.

BGP Communities
***************

BGP communities can be used for many features in the configurations built using ARouteServer: blackhole filtering, AS_PATH prepending, announcement control, various informative purposes (valid origin ASN, valid prefix, ...) and more. All these communities are referenced by *name* (or *tag*) in the configuration files and their real values are reported only once, in the ``communities`` section of the ``general.yml`` file.
For each community, values can be set for any of the three *formats*: standard (`RFC1997 <https://tools.ietf.org/html/rfc1997>`_), extended (`RFC4360 <https://tools.ietf.org/html/rfc4360>`_/`RFC5668 <https://tools.ietf.org/html/rfc5668>`_) and large (`RFC8092 <https://tools.ietf.org/html/rfc8092>`_).

Custom BGP Communities
~~~~~~~~~~~~~~~~~~~~~~

Custom, locally significant BGP communities can also be used for informational purposes, for example to keep track of the geographical origin of a route or the nature of the relation with the announcing route server client.

Custom communities are declared once in the ``general.yml`` configuration file and then are referenced by clients definitions in the ``clients.yml`` file.

Example:

**general.yml**

.. code:: yaml

   cfg:
     rs_as: 6777
     router_id: "80.249.208.255"
   custom_communities:
     colo_digitalrealty_ams01:
       std: "65501:1"
       lrg: "6777:65501:1"
     colo_equinix_am3:
       std: "65501:2"
       lrg: "6777:65501:2"
     colo_evoswitch:
       std: "65501:3"
       lrg: "6777:65501:3"
     member_type_peering:
       std: "65502:1"
       lrg: "6777:65502:1"
     member_type_probono:
       std: "65502:2"
       lrg: "6777:65502:2"

**clients.yml**

.. code:: yaml

   clients:
     - asn: 112
       ip: "192.0.2.112"
       cfg:
         attach_custom_communities:
         - "colo_digitalrealty_ams01"
         - "member_type_probono"
     - asn: 22
       ip: "192.0.2.22"
       passive: False
       cfg:
         attach_custom_communities:
         - "colo_equinix_am3"
         - "member_type_peering"
     - asn: 33
       ip: "192.0.2.33"
       cfg:
         attach_custom_communities:
         - "colo_evoswitch"
         - "member_type_peering"

.. _site-specific-custom-config:

Site-specific custom configuration files
****************************************

Local configuration files can be used to load static site-specific snippets of configuration into the BGP daemon, bypassing the dynamic ARouteServer configuration building mechanisms. These files can be used to configure, for example, neighborship with peers which are not route server members or that require custom settings.

Local files inclusion can be enabled by a command line argument, ``--use-local-files``: there are some fixed points in the configuration files generated by ARouteServer where local files can be included:

- BIRD:

  .. autoattribute:: pierky.arouteserver.builder.BIRDConfigBuilder.LOCAL_FILES_IDS

- OpenBGPD:

  .. autoattribute:: pierky.arouteserver.builder.OpenBGPDConfigBuilder.LOCAL_FILES_IDS

One or more of these labels must be used as the argument's value in order to enable the relative inclusion points.
For each enabled label, an *include* statement is added to the generated configuration in the point identified by the label itself. To modify the base directory, the ``--local-files-dir`` command line option can be used.

These files must be present on the host running the route server.

- Example, BIRD, file name "footer4.local" in "/etc/bird" directory:

  .. code::

      protocol bgp RouteCollector {
      	local as 999;
      	neighbor 192.0.2.99 as 65535;
      	rs client;
        secondary;

      	import none;
      	export all;
      }

- Example, OpenBGPD, ``header`` and ``post-clients``:

  .. code-block:: console
     :emphasize-lines: 2, 16

     $ arouteserver openbgpd --use-local-files header post-clients
     include "/etc/bgpd/header.local"

     AS 999
     router-id 192.0.2.2

     [...]

     group "clients" {

             neighbor 192.0.2.11 {
                     [...]
             }
     }

     include "/etc/bgpd/post-clients.local"

     [...]

  In the example above, the ``header`` and ``post-clients`` inclusion points are enabled and allow to insert two ``include`` statements into the generated configuration: one at the start of the file and one between clients declaration and filters.

- Example, OpenBGPD, ``client`` and ``footer``:

  .. code-block:: console
     :emphasize-lines: 10, 15, 22

     $ arouteserver openbgpd --use-local-files client footer --local-files-dir /etc/
     AS 999
     router-id 192.0.2.2

     [...]

     group "clients" {

             neighbor 192.0.2.11 {
                     include "/etc/client.local"
                     [...]
             }

             neighbor 192.0.2.22 {
                     include "/etc/client.local"
                     [...]
             }
     }

     [...]

     include "/etc/footer.local"

  The example above uses the ``client`` label, that is used to add an ``include`` statement into every neighbor configuration. Also, the base directory is set to ``/etc/``.

.. _bird-hooks:

BIRD hooks
~~~~~~~~~~

In BIRD, hook functions can also be used to tweak the configuration generated by ARouteServer.
Hooks are enabled by the ``--use-hooks`` command line argument, that accepts one or more of the following hook IDs:

  .. autoattribute:: pierky.arouteserver.builder.BIRDConfigBuilder.HOOKS

Functions with name ``hook_<HOOK_ID>`` must then be implemented within *.local* configuration files, in turn included using the ``--use-local-files`` command line argument.

Example:

  .. code-block:: console
     :emphasize-lines: 13, 21, 22

     $ arouteserver bird --ip-ver 4 --use-local-files header --use-hooks pre_receive_from_client
     router id 192.0.2.2;
     define rs_as = 999;

     log "/var/log/bird.log" all;
     log syslog all;
     debug protocols all;

     protocol device {};

     table master sorted;

     include "/etc/bird/header.local";

     [...]

     filter receive_from_AS3333_1 {
             if !(source = RTS_BGP ) then
                     reject "source != RTS_BGP - REJECTING ", net;

             if !hook_pre_receive_from_client(3333, 192.0.2.11, "AS3333_1") then
                     reject "hook_pre_receive_from_client returned false - REJECTING ", net;

             scrub_communities_in();

     [...]

Details about hook functions can be found in the :doc:`BIRD_HOOKS` page.

An example (including functions' prototypes) is provided within the "examples/bird_hooks" directory (`also on GitHub <https://github.com/pierky/arouteserver/tree/master/examples/bird_hooks>`_).

.. _reject-policy:

Reject policy and invalid routes tracking
*****************************************

Invalid routes, that is those routes that failed the validation process, can be simply discarded as they enter the route server (default behaviour) or, optionally, they can be kept for troubleshooting purposes, analysis or statistic reporting.

The ``reject_policy`` configuration option can be set to ``tag`` in order to have invalid routes tagged with a user-configurable BGP Community (``reject_reason``) whose purpose is to keep track of the reason for which they are considered to be invalid. These routes are also set with a low local-pref value (``1``) and tagged with a control BGP Community that prevents them from being exported to clients. If configured, the ``rejected_route_announced_by`` community is used to track the ASN of the client that announced the invalid route to the route server.

The goal of this feature is to allow the deployment of route collectors that can be used to further process invalid routes announced by clients. These route collectors can be configured using :ref:`site-specific .local files <site-specific-custom-config>`. The `InvalidRoutesReporter <https://github.com/pierky/invalidroutesreporter>`_ is an example of this kind of route collector.

The reason that brought the server to reject the route is identified using a numeric value in the last part of the BGP Community; the list of reject reasons follow:

.. include:: REJECT_REASON_COMMUNITIES.txt

\* This is not really a reject reason code, it only means that the route must be treated as rejected and must not be propagated to clients.

On BIRD, it's also possible to configure the ``reject_policy`` using the ``tag_and_reject`` value: doing this, the ``reject_reason`` and optionally the ``rejected_route_announced_by`` BGP communities are still attached to the invalid routes, but then they are rejected by BIRD. Since the BIRD-specific ``import keep filtered on`` configuration statement is used, those routes remain available within the BIRD daemon and can be seen using BIRD-specific commands like ``show route filtered all``.

Caveats and limitations
***********************

Not all features offered by ARouteServer are supported by both BIRD and OpenBGPD.
The following list of limitations is based on the currently supported versions of BIRD and OpenBGPD.

- IRR filtering of routes whose AS_PATH ends with an AS_SET

  - BIRD: routes are rejected by the IRR filters.
  - OpenBGPD: if the last non-aggregated AS in the AS_PATH is included in the list of ASNs generated from the IRR records, the routes pass the IRR filters.

    More details on `GitHub PR56 <https://github.com/pierky/arouteserver/pull/56>`_ (commit `a65934a <https://github.com/pierky/arouteserver/commit/a65934ad0ca636d7d381f705508f128b0ac17e5e>`_).

- BIRD

  - Multihop sessions are only supported on configurations for which **path hiding** mitigation is turned off.

    More details on `GitHub PR61 <https://github.com/pierky/arouteserver/pull/61>`_.

- OpenBGPD

  - Currently, **path hiding** mitigation is not implemented for OpenBGPD configurations. Only single-RIB configurations are generated.

  - **ADD-PATH** is not supported by OpenBGPD.

  - For max-prefix filtering, only the ``shutdown`` and the ``restart`` actions are supported by OpenBGPD. Restart is configured with a 15 minutes timer.

  - OpenBGPD does not offer a way to delete **extended communities** using wildcard (``rt xxx:*``): peer-ASN-specific extended communities (such as ``prepend_once_to_peer``, ``do_not_announce_to_peer``) are not scrubbed from routes that leave OpenBGPD route servers and so they are propagated to the route server clients.

  - The Site of Origin Extended BGP communities in the range 65535:* are reserved for internal reasons.

A list of all the features and their support level among the BGP speakers is maintained on the :ref:`Supported BGP speakers and features` section of this documentation.

Depending on the features that are enabled in the ``general.yml`` and ``clients.yml`` files, compatibility issues may arise; in this case, ARouteServer logs one or more errors, which can be then acknowledged and ignored using the ``--ignore-issues`` command line option:

.. code-block:: console

   $ arouteserver openbgpd
   ARouteServer 2017-03-23 21:39:45,955 ERROR Compatibility issue ID 'path_hiding'. The 'path_hiding'
   general configuration parameter is set to True, but the configuration generated by ARouteServer for
   OpenBGPD does not support path-hiding mitigation techniques.
   ARouteServer 2017-03-23 21:39:45,955 ERROR One or more compatibility issues have been found.

   Please check the errors reported above for more details.
   To ignore those errors, use the '--ignore-issues' command line argument and list the IDs of the
   issues you want to ignore.
   $ arouteserver openbgpd --ignore-issues path_hiding
   AS 999
   router-id 192.0.2.2

   fib-update no
   log updates
   ...

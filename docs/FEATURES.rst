How it works
------------

#. Two YAML files provide *general policies* and *clients configurations* options:

   .. code:: yaml

      cfg:
        rs_as: 64496
        router_id: "192.0.2.2"
        filtering:
          irrdb:
            enforce_origin_in_as_set: True
            enforce_prefix_in_as_set: True
          rpki_bgp_origin_validation:
            enabled: True
            reject_invalid: True
            ...

   .. code:: yaml

      clients:
        - asn: 64511
          ip:
          - "192.0.2.11"
          - "2001:db8:1:1::11"
          irrdb:
            as_sets:
              - "RIPE::AS-FOO"
        ...

#. ARouteServer acquires external information to enrich them: i.e. `bgpq4`_/`bgpq3`_ for IRR data, `PeeringDB`_ for max-prefix limit and AS-SETs, RPKI ROAs, ...

#. `Jinja2`_ built-in templates are used to render the final route server's configuration file.

   Currently, **BIRD** (>= 1.6.3 up to 1.6.8), **BIRD v2** (starting from 2.0.7) and **OpenBGPD** (OpenBSD 6.1 up to 7.6 and also OpenBGPD Portable 6.5p1 up to 7.6) are supported, with almost `feature parity <https://arouteserver.readthedocs.io/en/latest/SUPPORTED_SPEAKERS.html#supported-features>`__ between them.

**Validation** and testing of the configurations generated with this tool are performed using the built-in **live tests** framework: `Docker`_ instances are used to simulate several scenarios and to validate the behaviour of the route server after configuring it with ARouteServer. More details on the `Live tests <https://arouteserver.readthedocs.io/en/latest/LIVETESTS.html>`__ section.

A Docker-based `playground <https://github.com/pierky/arouteserver/tree/master/tools/playground>`__ is available to experiment with the tool in a virtual IXP environment.

Also, a `Docker image <https://hub.docker.com/r/pierky/arouteserver>`__ is provided to start building rich and secure configurations in a couple of minutes.

.. _bgpq3: https://github.com/snar/bgpq3
.. _bgpq4: https://github.com/bgp/bgpq4
.. _PeeringDB: https://www.peeringdb.com/
.. _Jinja2: http://jinja.pocoo.org/
.. _Docker: https://www.docker.com/

Features
--------

- **Path hiding** mitigation techniques (`RFC7947`_ `section 2.3.1 <https://tools.ietf.org/html/rfc7947#section-2.3.1>`__).

- Basic filters (mostly enabled by default):

  - **NEXT_HOP** enforcement (strict / same AS - `RFC7948`_ `section 4.8 <https://tools.ietf.org/html/rfc7948#section-4.8>`__);
  - minimum and maximum IPv4/IPv6 **prefix length**;
  - maximum **AS_PATH length**;
  - reject **invalid AS_PATHs** (containing `private/invalid ASNs <http://mailman.nanog.org/pipermail/nanog/2016-June/086078.html>`_);
  - reject AS_PATHs containing **transit-free** or **never via route-servers** ASNs (using `PeeringDB info_never_via_route_servers attribute <https://github.com/peeringdb/peeringdb/issues/394>`__);
  - reject **bogons**;
  - **max-prefix limit** based on global or client-specific values or on **PeeringDB** data.

- Prefixes and origin ASNs validation (also in *tag-only* mode):

  - **IRR-based filters** (`RFC7948`_ `section 4.6.2 <https://tools.ietf.org/html/rfc7948#section-4.6.2>`__);
  - AS-SETs configured manually or fetched from PeeringDB;
  - support for **IRR sources** (RIPE::AS-FOO, RADB::AS-BAR);
  - **white lists** support;
  - extended dataset for filters generation:

    - RPKI **ROAs used as route objects**;
    - `Origin AS <https://mailman.nanog.org/pipermail/nanog/2017-December/093525.html>`__ from **ARIN Whois** database dump;
    - `NIC.BR Whois data <https://ripe76.ripe.net/presentations/43-RIPE76_IRR101_Job_Snijders.pdf>`_ (slide n. 26) from Registro.br;

  - **RPKI**-based filtering (BGP Prefix Origin Validation);

    - ROAs can be retrieved from publicly available JSON files or from a local validating cache.

- **Blackhole filtering** support:

  - optional **NEXT_HOP rewriting**;
  - signalling via BGP Communities (`BLACKHOLE <https://tools.ietf.org/html/rfc7999#section-5>`__ and custom communities);
  - client-by-client control over propagation.

- **Graceful shutdown** support:

  - honor the **GRACEFUL_SHUTDOWN** BGP community received from clients (`draft-ietf-grow-bgp-gshut-11 <https://tools.ietf.org/html/draft-ietf-grow-bgp-gshut-11>`_);
  - allow to perform a graceful shutdown of the route server itself.

- Control and informative communities:

  - prefix/origin ASN present/not present in **IRRDBs data**;
  - do (not) announce to any / **peer** / on **RTT basis**;
  - **prepend** to any / **peer** / on **RTT basis**;
  - add **NO_EXPORT** / **NO_ADVERTISE** to any / **peer**;
  - `Euro-IX large BGP communities <https://www.euro-ix.net/en/forixps/large-bgp-communities/>`__ to track reject reasons;
  - custom informational BGP communities.

- Optional session features on a client-by-client basis:

  - prepend route server ASN (`RFC7947`_ `section 2.2.2.1 <https://tools.ietf.org/html/rfc7947#section-2.2.2.1>`__);
  - active sessions;
  - **GTSM** (Generalized TTL Security Mechanism - `RFC5082`_);
  - **ADD-PATH** capability (`RFC7911`_).

- Automatic building of clients list:

  - `integration <https://arouteserver.readthedocs.io/en/latest/USAGE.html#ixp-manager-integration>`__ with **IXP-Manager**;
  - `fetch lists <https://arouteserver.readthedocs.io/en/latest/USAGE.html#automatic-clients>`__ from **PeeringDB** records and **Euro-IX member list JSON** files.

- **IX-F Member Export** JSON files `creation <https://arouteserver.readthedocs.io/en/latest/USAGE.html#ixf-member-export-command>`__.

- Related tools:

  - The `Playground <https://github.com/pierky/arouteserver/tree/master/tools/playground>`__, to experiment with the tool in a virtual IXP environment.

  - `Invalid routes reporter <https://arouteserver.readthedocs.io/en/latest/TOOLS.html#invalid-routes-reporter>`__, to log or report invalid routes and their reject reason.

A comprehensive list of features can be found within the comments of the distributed configuration file on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/general.yml>`__ or on the `documentation web page <https://arouteserver.readthedocs.io/en/latest/GENERAL.html>`__.

More feature are already planned: see the `Future work <https://arouteserver.readthedocs.io/en/latest/FUTUREWORK.html>`__ section for more details.

.. _RFC7947: https://tools.ietf.org/html/rfc7947
.. _RFC7948: https://tools.ietf.org/html/rfc7948
.. _RFC5082: https://tools.ietf.org/html/rfc5082
.. _RFC7911: https://tools.ietf.org/html/rfc7911

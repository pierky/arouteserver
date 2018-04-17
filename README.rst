.. DO NOT EDIT: this file is automatically created by /utils/build_doc

ARouteServer
============

|Documentation| |Build Status| |Unique test cases| |PYPI Version| |Python Versions| |Requirements|


A Python tool to automatically build (and test) feature-rich configurations for BGP route servers.

How it works
------------

#. Two YAML files provide *general policies* and *clients configurations* options:

   .. code:: yaml

      cfg:
        rs_as: 64496
        router_id: "192.0.2.2"
        add_path: True
        filtering:
          next_hop:
            policy: "same-as"
        blackhole_filtering:
          policy_ipv4: "rewrite-next-hop"
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

#. ARouteServer acquires external information to enrich them: i.e. `bgpq3`_ for IRR data, `PeeringDB`_ for max-prefix limit and AS-SETs, ...

#. `Jinja2`_ built-in templates are used to render the final route server's configuration file.

   Currently, **BIRD** (1.6.3 and 1.6.4), **GoBGP (TBD)** and **OpenBGPD** (OpenBSD 6.0, 6.1 and 6.2) are supported, with almost feature parity between them.

**Validation** and testing are performed using the built-in **live tests** framework: `Docker`_ instances are used to simulate several scenarios, and more custom scenarios can be built on the basis of the user's needs. More details on the `Live tests <https://arouteserver.readthedocs.io/en/latest/LIVETESTS.html>`_ section.

.. _bgpq3: https://github.com/snar/bgpq3
.. _PeeringDB: https://www.peeringdb.com/
.. _Jinja2: http://jinja.pocoo.org/
.. _Docker: https://www.docker.com/

Features
--------

- **Path hiding** mitigation techniques (`RFC7947`_ `section 2.3.1 <https://tools.ietf.org/html/rfc7947#section-2.3.1>`_).

- Basic filters (mostly enabled by default):

  - **NEXT_HOP** enforcement (strict / same AS - `RFC7948`_ `section 4.8 <https://tools.ietf.org/html/rfc7948#section-4.8>`_);
  - minimum and maximum IPv4/IPv6 **prefix length**;
  - maximum **AS_PATH length**;
  - reject **invalid AS_PATHs** (containing `private/invalid ASNs <http://mailman.nanog.org/pipermail/nanog/2016-June/086078.html>`_);
  - reject AS_PATHs containing **transit-free** ASNs;
  - reject **bogons**;
  - **max-prefix limit** based on global or client-specific values or on **PeeringDB** data.

- Prefixes and origin ASNs validation (also in *tag-only* mode):

  - **IRR-based filters** (`RFC7948`_ `section 4.6.2 <https://tools.ietf.org/html/rfc7948#section-4.6.2>`_);
  - AS-SETs configured manually or fetched from PeeringDB;
  - support for **IRR sources** (RIPE::AS-FOO, RADB::AS-BAR);
  - **white lists** support;
  - extended dataset for filters generation:

    - RPKI **ROAs used as route objects**;
    - `Origin AS <https://mailman.nanog.org/pipermail/nanog/2017-December/093525.html>`_ from **ARIN Whois** database dump;

  - **RPKI**-based filtering (BGP Prefix Origin Validation).

- **Blackhole filtering** support:

  - optional **NEXT_HOP rewriting**;
  - signalling via BGP Communities (`BLACKHOLE <https://tools.ietf.org/html/rfc7999#section-5>`_ and custom communities);
  - client-by-client control over propagation.

- **Graceful shutdown** support:

  - honor the **GRACEFUL_SHUTDOWN** BGP community received from clients (`draft-ietf-grow-bgp-gshut-11 <https://tools.ietf.org/html/draft-ietf-grow-bgp-gshut-11>`_);
  - allow to perform a graceful shutdown of the route server itself.

- Control and informative communities:

  - prefix/origin ASN present/not present in **IRRDBs data**;
  - do (not) announce to any / **peer** / on **RTT basis**;
  - **prepend** to any / **peer** / on **RTT basis**;
  - add **NO_EXPORT** / **NO_ADVERTISE** to any / **peer**;
  - custom informational BGP communities.

- Optional session features on a client-by-client basis:

  - prepend route server ASN (`RFC7947`_ `section 2.2.2.1 <https://tools.ietf.org/html/rfc7947#section-2.2.2.1>`_);
  - active sessions;
  - **GTSM** (Generalized TTL Security Mechanism - `RFC5082`_);
  - **ADD-PATH** capability (`RFC7911`_).

- Automatic building of clients list:

  - `integration <https://arouteserver.readthedocs.io/en/latest/USAGE.html#ixp-manager-integration>`__ with **IXP-Manager**;
  - `fetch lists <https://arouteserver.readthedocs.io/en/latest/USAGE.html#automatic-clients>`__ from **PeeringDB** records and **Euro-IX member list JSON** files.

- **IX-F Member Export** JSON files `creation <https://arouteserver.readthedocs.io/en/latest/USAGE.html#ixf-member-export-command>`__.

- Related tools:

  - `Invalid routes reporter <https://arouteserver.readthedocs.io/en/latest/TOOLS.html#invalid-routes-reporter>`__, to log or report invalid routes and their reject reason.

A comprehensive list of features can be found within the comments of the distributed configuration file on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/general.yml>`__ or on the `documentation web page <https://arouteserver.readthedocs.io/en/latest/GENERAL.html>`__.

More feature are already planned: see the `Future work <https://arouteserver.readthedocs.io/en/latest/FUTUREWORK.html>`__ section for more details.

.. _RFC7947: https://tools.ietf.org/html/rfc7947
.. _RFC7948: https://tools.ietf.org/html/rfc7948
.. _RFC5082: https://tools.ietf.org/html/rfc5082
.. _RFC7911: https://tools.ietf.org/html/rfc7911

Full documentation
------------------

Full documentation can be found on ReadTheDocs: https://arouteserver.readthedocs.org/

Presentations
-------------

- RIPE74, 10 May 2017, Connect Working Group: `video <https://ripe74.ripe.net/archives/video/87/>`__ (9:53), `slides <https://ripe74.ripe.net/presentations/22-RIPE74-ARouteServer.pdf>`__ (PDF)
- Salottino MIX, 30 May 2017: `slides <https://www.slideshare.net/PierCarloChiodi/salottino-mix-2017-arouteserver-ixp-automation-made-easy>`__

Mentions / endorsements:

- Job Snijders, LINX99, 20 November 2017: `slides <http://instituut.net/~job/LINX99_route_servers.pdf>`__

Who is using ARouteServer?
--------------------------

- `IX-Denver <http://ix-denver.org/>`__, BIRD.

- `PIT-IX <https://pit-ix.net/>`__, BIRD.

- `YYCIX <https://yycix.ca>`__, OpenBGPD.

Are you using it? Do you want to be listed here? `Drop me a message <https://pierky.com/#contactme>`__!

Status
------

**Beta testing**, looking for testers and reviewers.

Anyone who wants to share his/her point of view, to review the output configurations or to test them is **more than welcome**!

Bug? Issues? Support requests?
------------------------------

But also suggestions? New ideas?

Please create an `issue on GitHub <https://github.com/pierky/arouteserver/issues>`_ or `drop me a message <https://pierky.com/#contactme>`_.

A Slack channel is also available on the `network.toCode() <https://networktocode.herokuapp.com/>`__ community: **arouteserver**.

Author
------

Pier Carlo Chiodi - https://pierky.com

Blog: https://blog.pierky.com Twitter: `@pierky <https://twitter.com/pierky>`_

.. |Documentation| image:: https://readthedocs.org/projects/arouteserver/badge/?version=latest
    :target: https://arouteserver.readthedocs.org/en/latest/?badge=latest
.. |Build Status| image:: https://travis-ci.org/pierky/arouteserver.svg?branch=master
    :target: https://travis-ci.org/pierky/arouteserver
.. |Unique test cases| image:: https://img.shields.io/badge/dynamic/json.svg?uri=https://raw.githubusercontent.com/pierky/arouteserver/master/tests/last.json&label=unique%20test%20cases&query=$.unique_test_cases&colorB=47C327
    :target: https://github.com/pierky/arouteserver/blob/master/tests/last
.. |PYPI Version| image:: https://img.shields.io/pypi/v/arouteserver.svg
    :target: https://pypi.python.org/pypi/arouteserver/
.. |Requirements| image:: https://requires.io/github/pierky/arouteserver/requirements.svg?branch=master
    :target: https://requires.io/github/pierky/arouteserver/requirements/?branch=master
    :alt: Requirements Status
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/arouteserver.svg

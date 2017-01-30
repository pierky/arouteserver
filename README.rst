ARouteServer
============

A Python tool to automatically build (and test) configurations for BGP route servers.

How it works
------------

#. Two YAML files provide *general policies* and *clients configurations* options:

   .. code:: yaml

      cfg:
        rs_as: 999
        router_id: "192.0.2.2"
        add_path: True
        filtering:
          next_hop_policy: "same-as"
        blackhole_filtering:
          policy_ipv4: "rewrite-next-hop"
          ...

   .. code:: yaml

      clients:
        - as: 111
          ip:
          - "192.0.2.11"
          - "2001:db8:1:1::11"
          rpsl:
            as_sets:
              - "AS-AS111MAIN"
        ...

#. ARouteServer acquires external information to enrich them: `bgpq3`_ for IRRDb data, `PeeringDB`_ for max-prefix limit, ...

#. `Jinja2`_ built-in templates are used to render the final route server's configuration file.

   Currently, only **BIRD** is supported.

**Validation** and testing is performed using the built-in **live tests** framework: `Docker`_ instances are used to simulate several scenarios, and more custom scenarios can be built on the basis of the user's needs. More details on the `Live tests <https://arouteserver.readthedocs.io/en/latest/LIVETESTS.html>`_ section.

.. _bgpq3: https://github.com/snar/bgpq3
.. _PeeringDB: https://www.peeringdb.com/
.. _Jinja2: http://jinja.pocoo.org/
.. _Docker: https://www.docker.com/

Features
--------

- **Path hiding** mitigation techniques (`RFC7947`_ `section 2.3.1 <https://tools.ietf.org/html/rfc7947#section-2.3.1>`_).

- Filtering features on by default:

  - **NEXT_HOP** enforcement (strict / same AS - `RFC7948`_ `section 4.8 <https://tools.ietf.org/html/rfc7948#section-4.8>`_);
  - minimum and maximum IPv4/IPv6 **prefix length**;
  - maximum **AS_PATH length**;
  - reject **invalid AS_PATHs** (containing private/invalid ASNs);
  - reject **bogons**;
  - prefixes and origin ASNs enforcing via **RPSL/IRRdb AS-SETs** (`RFC7948`_ `section 4.6.2 <https://tools.ietf.org/html/rfc7948#section-4.6.2>`_);
  - **max-prefix limit** based on global or client-specific values or on **PeeringDB** data.

- **Blackhole filtering** support:

  - optional **NEXT_HOP rewriting**;
  - signalling via BGP Communities (`BLACKHOLE <https://tools.ietf.org/html/rfc7999#section-5>`_ and custom communities);
  - client-by-client control over propagation.

- Control and informative communities:

  - prefix/origin ASN present/not present in **IRRDB data**;
  - do (not) announce to any / **peer**;
  - **prepend** to any.

- Optional session features on a client-by-client basis:

  - prepend route server ASN;
  - active sessions;
  - **GTSM** (Generalized TTL Security Mechanism - `RFC5082`_);
  - **ADD-PATH** capability (`RFC7911`_).

A comprehensive list of features can be found within the comments of the distributed configuration file on GitHub.

More feature are already planned: see the `Future work <https://arouteserver.readthedocs.io/en/latest/FUTUREWORK.html>`_ section for more details.

.. _Path hiding: https://tools.ietf.org/html/rfc7947#section-2.3.1
.. _RFC7947: https://tools.ietf.org/html/rfc7947
.. _RFC7948: https://tools.ietf.org/html/rfc7948
.. _RFC5082: https://tools.ietf.org/html/rfc5082
.. _RFC7911: https://tools.ietf.org/html/rfc7911

Full documentation
------------------

Full documentation can be found on ReadTheDocs: https://arouteserver.readthedocs.org/

Status
------

**Highly experimental**!

Bug? Issues?
------------

But also suggestions? New ideas?

Please create an issue on GitHub at https://github.com/pierky/arouteserver/issues

Author
------

Pier Carlo Chiodi - https://pierky.com

Blog: https://blog.pierky.com Twitter: `@pierky <https://twitter.com/pierky>`_

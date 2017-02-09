.. DO NOT EDIT: this file is automatically created by /utils/build_doc

ARouteServer
============
|Documentation| |Build Status|

A Python tool to automatically build (and test) feature-rich configurations for BGP route servers.

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
        - asn: 111
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

**Validation** and testing are performed using the built-in **live tests** framework: `Docker`_ instances are used to simulate several scenarios, and more custom scenarios can be built on the basis of the user's needs. More details on the `Live tests <https://arouteserver.readthedocs.io/en/latest/LIVETESTS.html>`_ section.

.. _bgpq3: https://github.com/snar/bgpq3
.. _PeeringDB: https://www.peeringdb.com/
.. _Jinja2: http://jinja.pocoo.org/
.. _Docker: https://www.docker.com/

Features
--------

- **Path hiding** mitigation techniques (`RFC7947`_ `section 2.3.1 <https://tools.ietf.org/html/rfc7947#section-2.3.1>`_).

- Filtering features (most enabled by default):

  - **NEXT_HOP** enforcement (strict / same AS - `RFC7948`_ `section 4.8 <https://tools.ietf.org/html/rfc7948#section-4.8>`_);
  - minimum and maximum IPv4/IPv6 **prefix length**;
  - maximum **AS_PATH length**;
  - reject **invalid AS_PATHs** (containing `private/invalid ASNs <http://mailman.nanog.org/pipermail/nanog/2016-June/086078.html>`_);
  - reject AS_PATHs containing **transit-free** ASNs;
  - **RPKI**-based filtering/tagging `RFC6811`_;
  - reject **bogons**;
  - prefixes and origin ASNs enforcing via **RPSL/IRRdb AS-SETs** (`RFC7948`_ `section 4.6.2 <https://tools.ietf.org/html/rfc7948#section-4.6.2>`_);
  - **max-prefix limit** based on global or client-specific values or on **PeeringDB** data.

- **Blackhole filtering** support:

  - optional **NEXT_HOP rewriting**;
  - signalling via BGP Communities (`BLACKHOLE <https://tools.ietf.org/html/rfc7999#section-5>`_ and custom communities);
  - client-by-client control over propagation.

- Control and informative communities:

  - prefix/origin ASN present/not present in **IRRDB data**;
  - prefix **RPKI** status;
  - do (not) announce to any / **peer**;
  - **prepend** to any / **peer**.

- Optional session features on a client-by-client basis:

  - prepend route server ASN (`RFC7947`_ `section 2.2.2.1 <https://tools.ietf.org/html/rfc7947#section-2.2.2.1>`_);
  - active sessions;
  - **GTSM** (Generalized TTL Security Mechanism - `RFC5082`_);
  - **ADD-PATH** capability (`RFC7911`_).

A comprehensive list of features can be found within the comments of the distributed configuration file on `GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/general.yml>`_.

More feature are already planned: see the `Future work <https://arouteserver.readthedocs.io/en/latest/FUTUREWORK.html>`_ section for more details.

.. _RFC7947: https://tools.ietf.org/html/rfc7947
.. _RFC7948: https://tools.ietf.org/html/rfc7948
.. _RFC5082: https://tools.ietf.org/html/rfc5082
.. _RFC7911: https://tools.ietf.org/html/rfc7911
.. _RFC6811: https://tools.ietf.org/html/rfc6811

Full documentation
------------------

Full documentation can be found on ReadTheDocs: https://arouteserver.readthedocs.org/

Status
------

**Highly experimental**! Please consider it as a toy, far from being production ready. Looking for advices and testers.

Bug? Issues?
------------

But also suggestions? New ideas?

Please create an issue on GitHub at https://github.com/pierky/arouteserver/issues

Author
------

Pier Carlo Chiodi - https://pierky.com

Blog: https://blog.pierky.com Twitter: `@pierky <https://twitter.com/pierky>`_

.. |Documentation| image:: https://readthedocs.org/projects/arouteserver/badge/?version=latest
    :target: https://arouteserver.readthedocs.org/en/latest/?badge=latest
.. |Build Status| image:: https://travis-ci.org/pierky/arouteserver.svg?branch=master
    :target: https://travis-ci.org/pierky/arouteserver

.. DO NOT EDIT: this file is automatically created by /utils/build_doc

Examples of configurations
==========================

Default
-------

Configurations built using the default ``general.yml`` and ``clients.yml`` files distributed with the project.

https://github.com/pierky/arouteserver/blob/master/examples/default

See the `textual representation of this configuration <_static/examples_default.html>`_.

Feature-rich example
--------------------

Configurations built using the files provided in the ``examples/rich`` directory.

- GTSM and ADD-PATH are enabled by default on the route server.
- Next-hop filtering allows clients to set NEXT_HOP of any client in the same AS.
- Local networks are filtered, and also transit-free ASNs, invalid paths and prefixes/origin ASNs which are not authorized by clients' AS-SETs.
- RPKI-based route validation is enabled; INVALID routes are rejected, VALID and UNKNOWN are tagged with BGP communities.
- A max-prefix limit is enforced on the basis of PeeringDB information.
- Blackhole filtering is implemented with a rewrite-next-hop policy and can be triggered with BGP communities BLACKHOLE, 65534:0 and 999:666:0.
- Control communities allow selective announcement control and prepending.

https://github.com/pierky/arouteserver/blob/master/examples/rich

See the `textual representation of this configuration <_static/examples_rich.html>`_.

Clients from Euro-IX member list JSON file
------------------------------------------

Some clients files automatically built from `Euro-IX member list JSON files <https://github.com/euro-ix/json-schemas>`_ are reported here.

https://github.com/pierky/arouteserver/blob/master/examples/clients-from-euroix

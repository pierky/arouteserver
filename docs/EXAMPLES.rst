Examples of configurations
==========================

Default
-------

BIRD configurations built using the default ``general.yml`` and ``clients.yml`` files distributed with the project.

https://github.com/pierky/arouteserver/blob/master/examples/default

Feature-rich example
--------------------

Configurations built using the files provided in the ``examples/rich`` directory.

- GTSM and ADD-PATH are enabled by default on the route server.
- Next-hop filtering allows clients to set NEXT_HOP of any client in the same AS.
- Local networks are filtered, and also transit-free ASNs, invalid paths and prefixes/origin ASNs which are not authorized by clients' AS-SETs.
- RPKI-based prefix validation is enabled; INVALID prefixes are rejected, VALID and UNKNOWN are tagged with BGP communities.
- A max-prefix limit is enforced on the basis of PeeringDB information.
- Blackhole filtering is implemented with a rewrite-next-hop policy and can be triggered with BGP communities BLACKHOLE, 65534:0 and 999:666:0.
- Control communities allow selective announcement control and prepending.

https://github.com/pierky/arouteserver/blob/master/examples/rich


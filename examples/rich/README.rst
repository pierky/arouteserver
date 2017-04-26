Feature-rich example
--------------------

Configurations built using the files provided in the ``examples/rich`` directory.

- GTSM and ADD-PATH are enabled by default on the route server.
- Next-hop filtering allows clients to set NEXT_HOP of any client in the same AS.
- Local networks are filtered, and also transit-free ASNs, invalid paths and prefixes/origin ASNs which are not authorized by clients' AS-SETs.
- RPKI-based route validation is enabled; INVALID routes are rejected.
- A max-prefix limit is enforced on the basis of PeeringDB information.
- Blackhole filtering is implemented with a rewrite-next-hop policy and can be triggered with BGP communities BLACKHOLE, 65534:0 and 999:666:0.
- Control communities allow selective announcement control and prepending.
- Client timers are configured using the custom, site-specific .local file.
- Informational custom BGP communities are used to tag routes from European or American clients.

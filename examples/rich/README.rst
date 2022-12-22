Feature-rich example
--------------------

Configurations built using the files provided in the ``examples/rich`` directory.

- GTSM and ADD-PATH are enabled by default on the route server.
- Next-hop filtering allows clients to set NEXT_HOP of any client in the same AS.
- Local networks are filtered, and also transit-free ASNs, "never via route-servers" networks, invalid paths and prefixes/origin ASNs which are not authorized by clients' AS-SETs (which are fetched from PeeringDB).
- Dataset used for prefix validation extended using NIC.BR Whois DB dump and RPKI ROAs.
- RPKI-based Origin Validation is enabled; INVALID routes are rejected.
- A max-prefix limit is enforced on the basis of PeeringDB information.
- Blackhole filtering is implemented with a rewrite-next-hop policy and can be triggered with BGP communities BLACKHOLE, 65534:0 and 999:666:0.
- Control communities allow selective announcement control and prepending, also on the basis of peers RTT.
- Graceful BGP session shutdown is enabled.
- Client timers are configured using the custom, site-specific .local file.
- Informational custom BGP communities are used to tag routes from European or American clients.

Please note: for the sake of readability of the configuration files built in this example the set of RPKI ROAs is artificially limited to just a bunch of them.

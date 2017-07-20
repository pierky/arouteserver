RTT getter program for RTT-based actions
****************************************

The program referenced by the ``rtt_getter_path`` option in the ARouteServer's configuration file is used when RTT-based actions are configured (*do not announce to peers with RTT higher than x*, *prepend to peers with RTT higher than y*, ...).

The path referenced by this option must point to a file that is executed during the configuration building process in order to obtain the RTT measured toward route server's clients.

Since the configuration building process might be executed on a machine that is not on the peering LAN, or that is not expected to be able to perform RTT measurements toward the peers, the path to a custom script can be configured here in order to gather the RTT from external data sources.

The program is executed with the following arguments:

- client IP address
- client ASN
- internal client ID.

ARouteServer reads the result from the stdout; if the result contains multiple line, only the first one is parsed. The format must be the following:

- ``none`` means that, for the given client, no information are available;
- any number that matches the ``^\d+[.]?\d*$`` regex pattern is used to set the client's RTT.

A proof of concept script is provided within the ``config.d/rtt_getter.sh`` file (`here on GitHub <https://github.com/pierky/arouteserver/blob/master/config.d/rtt_getter.sh>`_).

Within the route server's configuration, RTTs lower than 1 ms will be treated as 1 ms and values higher than 60000 ms will be adjusted to that limit.

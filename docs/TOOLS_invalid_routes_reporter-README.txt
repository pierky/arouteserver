Invalid routes reporter
-----------------------

This script is intended to be used as an `ExaBGP <https://github.com/Exa-Networks/exabgp>`_ process to elaborate and report/log invalid routes received by route servers that have been previously configured using the `"tag" reject policy option <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#reject-policy>`_ of `ARouteServer <https://github.com/pierky/arouteserver>`_.

Invalid routes are those routes that, for some reason, didn't pass the route server's validation process (invalid/private ASNs in the AS_PATH, bogon prefixes, invalid NEXT_HOP, IRRDBs data mismatch, ...). The "tag" reject policy allows route servers to keep these routes instead of discarding them and to attach a BGP community that describes the reason for which they have been considered as invalid.

A session with an ExaBGP-based route collector can be used to announce invalid routes to this script, that finally processes them, extracts the reject reason and uses this information to log a record or to send an email alert to the involved networks.

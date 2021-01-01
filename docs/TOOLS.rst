Tools
=====

Playground
----------

This is a Docker-based playground that can be use to experiment with ARouteServer.

It offers and environment with several actors, configured to represent specific scenarios that can often be found on a real IX platform: a route server, some clients that announce some good and some bad routes, a looking glass.

The idea is to let the users play with the whole environment and see how easy it is to deploy a secure, feature-rich route server.

For more information: https://github.com/pierky/arouteserver/tree/master/tools/playground

Invalid routes reporter
-----------------------

This script is intended to be used as an `ExaBGP <https://github.com/Exa-Networks/exabgp>`_ process to elaborate and report/log invalid routes received by route servers that have been previously configured using the `"tag" reject policy option <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#reject-policy>`_ of ARouteServer.

For more information: https://invalidroutesreporter.readthedocs.io

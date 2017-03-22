Future work
===========

OpenBGPD support
----------------
- New feature: path-hiding mitigation technique
- New feature: max-prefix 'restart' action timer
- New feature: group clients by AFI/ASN
- Fix: blackhole filtering requests, next-hop rewriting for IPv6

Short term
----------

- New feature: custom informative BGP communities
- Doc: contributing section
- Packaging: a command to upgrade the program

Mid term
--------

- Split configuration in multiple files
- Doc: better documentation
- Doc: schema of data that can be used within J2 templates

Long term
---------

- New feature: routing policies based on RPSL import-via/export-via
- New feature: other BGP speakers support (GoBGP, ...)
- New feature: balance clients among *n* different configurations (for multiple processes - see `Scaling BIRD Routeservers <https://ripe73.ripe.net/presentations/115-e-bru-20161026-RIPE73-scaling-bird-routeservers-final.pdf>`_)

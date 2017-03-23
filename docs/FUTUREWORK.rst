Future work
===========

Short term
----------

- New feature: max-prefix 'restart' action timer (OpenBGPD only)
- New feature: custom informative BGP communities
- New feature: timers customization
- Improvement: BIRD .local files
- Packaging: a command to upgrade the program

Mid term
--------

- New feature: group clients by AFI/ASN (OpenBGPD only)
- Split configuration in multiple files
- Doc: better documentation
- Doc: contributing section
- Doc: schema of data that can be used within J2 templates
- Fix: blackhole filtering requests, next-hop rewriting for IPv6 (OpenBGPD only)

Long term
---------

- New feature: path-hiding mitigation technique on OpenBGPD
- New feature: routing policies based on RPSL import-via/export-via
- New feature: other BGP speakers support (GoBGP, ...)
- New feature: balance clients among *n* different configurations (for multiple processes - see `Scaling BIRD Routeservers <https://ripe73.ripe.net/presentations/115-e-bru-20161026-RIPE73-scaling-bird-routeservers-final.pdf>`_)

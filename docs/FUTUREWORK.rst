Future work
===========

Short term
----------

- RTT-based communities: extend support to add NO_EXPORT / NO_ADVERTISE
- Informative community with the measured RTT of the announcing peer
- New feature: CLI option to build configs based on templates/groups only and avoid client specific settings

Mid term
--------

- New feature: group clients by AFI/ASN (OpenBGPD only)
- Split configuration in multiple files
- Doc: better documentation
- Doc: contributing section
- Doc: schema of data that can be used within J2 templates

Long term
---------

- New feature: path-hiding mitigation technique on OpenBGPD
- New feature: routing policies based on RPSL import-via/export-via
- New feature: other BGP speakers support (GoBGP, ...)
- New feature: balance clients among *n* different configurations (for multiple processes - see `Scaling BIRD Routeservers <https://ripe73.ripe.net/presentations/115-e-bru-20161026-RIPE73-scaling-bird-routeservers-final.pdf>`_)

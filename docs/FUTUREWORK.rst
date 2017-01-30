Future work
===========

Short term
----------

- New feature: RPKI filtering/tagging (based on `rtrsub`_ and/or `rtrlib`_)
- New feature: selective prepending via BGP communities
- New feature: Custom informative BGP communities
- Live tests: path hiding mitigation live test
- Live tests: provide a skeleton to ease building of new live test scenarios.
- Add options for bgpq3 (sources)
- Examples: provide examples of route server configurations
- Doc: Contributing section
- Templates: textual representation of configurations

Mid term
--------

- Doc: better documentation
- Doc: schema of data that can be used within J2 templates
- New feature: tier-1 list

Long term
---------

- New feature: routing policies based on RPSL import-via/export-via
- New feature: other BGP speakers support (OpenBGPD, ...)

.. _rtrsub: https://github.com/job/rtrsub
.. _rtrlib: https://github.com/rtrlib/bird-rtrlib-cli


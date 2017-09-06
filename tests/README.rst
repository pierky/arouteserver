Tests
=====

The following directories contain code that is used to test ARouteServer:

- **static**: Python unittest modules used to test single piece of code;

- **live_tests**: the `Live tests framework <https://arouteserver.readthedocs.io/en/latest/LIVETESTS.html>`_ used to simulate route servers configured using this tool and to verify how they interact with their clients;

- **real**: some `realistic scenarios <https://arouteserver.readthedocs.io/en/latest/REALTESTS.html>`_ built on the basis of lists of clients pulled from actual IXPs' members lists.

The latest results of *static* tests and *live* tests can be found within the **last** file (and also on `Travis CI log file <https://travis-ci.org/pierky/arouteserver/>`_, except for OpenBGPD focused tests).

Results for the *real* tests are reported within the **tests/real/last** file.

Tests
=====

The following directories contain code that is used to test ARouteServer:

- **static**: Python unittest modules used to test single pieces of code;

- **live_tests**: the `Live tests framework <https://arouteserver.readthedocs.io/en/latest/LIVETESTS.html>`_ used to simulate route servers configured using this tool and to verify how they interact with their clients;

- **external_resources**: to verify that interactions between ARouteServer and the external tools it uses are fine: PeeringDB, RIPE RPKI Validator cache, bgpq3... Also scheduled to run via a cron job on GitHub Actions.

- **real**: some `realistic scenarios <https://arouteserver.readthedocs.io/en/latest/REALTESTS.html>`_ built on the basis of lists of clients pulled from actual IXPs' members lists.

The latest results of *static*, *live* and *external_resources* tests can be found within the **last** file (and also on `GitHub Actions log file <https://github.com/pierky/arouteserver/actions/workflows/tests.yml>`_, except for OpenBGPD focused tests).

Results for the *real* tests are reported within the **tests/real/last** file.

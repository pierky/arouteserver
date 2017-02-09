Usage
=====

The script can be executed via command-line:

  .. code:: bash

    # if cloned from GitHub, from the repository's root directory:
    export PYTHONPATH="`pwd`"
    ./scripts/arouteserver build --ip-ver 4 -o /etc/bird/bird4.conf

    # if installed using pip:
    arouteserver build --ipver-4 -o /etc/bird/bird4.conf

It produces the route server configuration and saves it on ``/etc/bird/bird4.conf``.

Other commands
--------------

Initialize a custom live test scenario
**************************************

To setup a new live test scenario:

.. code:: bash

      arouteserver init-scenario ~/ars_scenarios/myscenario

More details on :doc:`LIVETESTS_CUSTOMSCENARIO`.


Create clients.yml file from PeeringDB records
**********************************************

The ``clients-from-peeringdb`` command can be used for testing purposes to automatically create a ``clients.yml`` file on the basis of PeeringDB records.
Given an IX LAN ID, it collects all the networks which are registered as route server clients on that LAN, then it builds the clients file accordingly.

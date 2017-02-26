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

It exits with ``0`` if everything is fine or with an exit code different than zero if something wrong occurs.

It can be scheduled at regular interval to re-build the configuration (for example to add new clients or to update IRRDB information), test it and finally to deploy it in production:

  .. code:: bash

    arouteserver build --ipver-4 -o /etc/bird/bird4.new && \
        bird -p -c /etc/bird/bird4.new && \
        cp /etc/bird/bird4.new /etc/bird/bird4.conf && \
        birdcl configure

Other commands
--------------

Textual representation
**********************

To build an HTML textual representation of route server's options and policies, the ``html`` command can be used:

  .. code:: bash

    arouteserver html -o /var/www/html/rs_description.html

This command writes an HTML page that contains a brief textual representation of route server's policies. An example can be found `here <_static/examples_rich.html>`_.

Template context data
*********************

To dump the list of variables and data that can be used inside a template, the ``template-context`` command can be used:

  .. code:: bash

    arouteserver template-context

It produces a YAML document that contains the context variables and their values as they are passed to the template engine used to build configurations.

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

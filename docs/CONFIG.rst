Configuration
=============

The following files, by default located in ``/etc/arouteserver``, contain configuration options for the program and for the route server's configuration:

- ``arouteserver.yml``: program's options and paths to other files are configured here. See the default content on GitHub.

- ``general.yml``: the route server's configuration options and policies. See the default content on GitHub.

- ``clients.yml``: the list of route server's clients and their options and policies. See the default content on GitHub.

- ``bogons.yml``: the list of bogon prefixes automatically discarded by the route server. See the default content on GitHub.

Route server's configuration
----------------------------

Route server's general configuration and policies are outlined in the ``general.yml`` file. Clients, which are configured in the ``clients.yml`` file, inherit most of these options, unless their configuration sets specific values. For example:

.. code:: yaml

   cfg:
     rs_as: 999
     router_id: "192.0.2.2"
     passive: True
     gtsm: True

.. code:: yaml

   clients:
     - as: 11
       ip: "192.0.2.11"
     - as: 22
       ip: "192.0.2.22"
       passive: False
     - as: 33
       ip: "192.0.2.33"
       passive: False
       gtsm: False

In this scenario, the route server's configuration will look like this:

- a passive session with GTSM enabled toward AS11 client;
- an active session with GTSM enabled toward AS22 client;
- an active session with GTSM disabled toward AS33 client.

Configuration details and options can be found within the distributed general and clients configuration files on GitHub.

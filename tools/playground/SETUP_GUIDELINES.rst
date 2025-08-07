ARouteServer playground: setup guidelines
=========================================

Four main steps are needed to go from zero to a secure and feature-rich configuration for our route server:

- ARouteServer setup
- ARouteServer configuration
- Clients definition
- Configuration generation

ARouteServer setup
++++++++++++++++++

First, we need to connect to the docker instance where the route server and ARouteServer run:

.. code:: console

    $ docker-compose exec rs bash

All the dependencies needed by ARouteServer (basically just Python and `bgpq4 <https://github.com/bgp/bgpq4>`__) are already installed inside the Docker image (see `rs/Dockerfile <rs/Dockerfile>`__).

We just need to setup the program and configure it.

Let's start with the setup of the program.

I'd suggest using */etc/arouteserver* as the directory where configuration files will be stored:

.. code:: console
    root@3b94400c5de0:~# arouteserver setup
    ARouteServer setup

    Where do you want configuration files and templates to be stored? (default: ~/arouteserver) /etc/arouteserver

    [... omitted...]

    Configuration complete!

    - edit the /etc/arouteserver/arouteserver.yml file to configure program's options
    - edit the /etc/arouteserver/log.ini file to set your logging preferences
    - set your route server's options and policies in /etc/arouteserver/general.yml
      (edit it manually or use the 'arouteserver configure' command)
    - configure route server clients in the /etc/arouteserver/clients.yml file


ARouteServer configuration
++++++++++++++++++++++++++

Now, we need to configure the route server policies: IRR filtering, RPKI Origin Validation, max-prefix handling, ...

We can either manually edit the *general.yml* file (``vim /etc/arouteserver/general.yml``) or we can run the ``arouteserver configure`` command, that will take care of setting options based on best-practices and industry standards.

**Please note**: in order to configure the BIRD instance in a way that will work smoothly with the other actors of this playground, please use the following values to answer the ``configure`` command questions:

- Daemon: BIRD
- Version: 2.17.1
- ASN of the route server: 64500
- Router-ID of the route server: 10.0.0.2
- Local networks: 10.0.0.0/24

.. code:: console

    root@3b94400c5de0:~# arouteserver configure

    BGP daemon
    ==========

    Depending on the BGP daemon used for the route server some features may not be
    available.

    Details here:
    https://arouteserver.readthedocs.io/en/latest/CONFIG.html#caveats-and-
    limitations

    Which BGP daemon will be used? [bird/openbgpd] bird
    Which version? [1.6.3/1.6.4/1.6.6/1.6.7/1.6.8/2.0.7/2.0.7+b962967e] 1.6.8

    Router server's ASN
    ===================

    What's the ASN of the route server? 64500

    Route server's BGP router-id
    ============================

    Please enter the route server BGP router-id: 10.0.0.2

    List of local networks
    ======================

    A list of local IPv4/IPv6 networks must be provided here: routes announced by
    route server clients for these prefixes will be filtered out.

    Please enter a comma-separated list of local networks: 10.0.0.0/24

At this point, the command will print a summary of the settings that it produced:

.. code::

    Route server policy definition file generated successfully!
    ===========================================================

    The content of the general configuration file will now be written to
    /etc/arouteserver/general.yml

    Some notes:

     - Accepted prefix lengths are 8-24 for IPv4 and 12-48 for IPv6.
     - Routes with 'transit-free networks' or 'never via route-server' (PeeringDB)
    ASNs in the middle of AS_PATH are rejected.
     - IRR-based filters are enabled; prefixes that are more specific of those
    registered are accepted.
     - PeeringDB is used to fetch AS-SETs for those clients that are not explicitly
    configured.
     - RPKI ROAs are used as if they were route objects to further enrich IRR data.
     - ARIN Whois database dump is fetched from NLNOG to further enrich IRR data.
     - NIC.BR Whois database dump is fetched from Registro.br to further enrich IRR
    data.
     - RPKI BGP Origin Validation is enabled. INVALID routes are rejected.
     - PeeringDB is used to fetch networks prefix count.
     - Routes tagged with the GRACEFUL_SHUTDOWN well-known community (65535:0) are
    processed accordingly to draft-ietf-grow-bgp-gshut.

Clients definition
++++++++++++++++++

Now that we have the general policy that will drive the route server's configuration building process, we can define our clients.

Clients are defined using a YML file, *clients.yml*: in this playground, an example file can be found in the root directory of the *rs* instance (``cat /root/clients.yml``):

.. code:: yaml

    clients:
      - asn: 3333
        ip:
        - "10.0.0.11"
        description: Test client 1
      - asn: 10745
        ip:
        - "10.0.0.12"
        description: Test client 2

Again, ASNs and IP addresses are set according to the way Docker containers for clients are configured.

We can copy this file directly into the path of the official file used by ARouteServer:

.. code:: console

    root@3b94400c5de0:~# cp /root/clients.yml /etc/arouteserver/clients.yml

Configuration generation
++++++++++++++++++++++++

Now we have everything we need to configure BIRD.
ARouteServer can be executed and the final configuration loaded into the daemon:

.. code:: console

    root@3b94400c5de0:~# arouteserver bird --ip-ver 4 -o /etc/bird/bird.conf
    ARouteServer 2020-12-29 17:19:34,618 INFO Started processing configuration for /etc/arouteserver/templates/bird/main.j2
    [... omitted...]
    ARouteServer 2020-12-29 17:19:41,543 INFO Template rendering completed after 1 seconds.

.. code:: console

    root@3b94400c5de0:~# birdc configure
    BIRD 1.6.8 ready.
    Reading configuration from /etc/bird/bird.conf
    Reconfigured

At this point, BIRD should show a couple of established BGP sessions:

.. code:: console

    root@3b94400c5de0:~# birdc show protocols
    BIRD 1.6.8 ready.
    name     proto    table    state  since       info
    device1  Device   master   up     2020-12-30 10:45:29
    AS10745_1 BGP      master   up     2020-12-30 10:45:29  Established
    AS3333_1 BGP      master   up     2020-12-30 10:45:29  Established

References
++++++++++

- `ARouteServer docs: Installation <https://arouteserver.readthedocs.io/en/latest/INSTALLATION.html#>`__

- `ARouteServer docs: Setup and initialization <https://arouteserver.readthedocs.io/en/latest/INSTALLATION.html#setup-and-initialization>`__

- `ARouteServer docs: Route server’s configuration <https://arouteserver.readthedocs.io/en/latest/CONFIG.html#route-server-s-configuration>`__

- `ARouteServer repository: general.yml <https://github.com/pierky/arouteserver/blob/master/config.d/general.yml>`__

- `ARouteServer repository: clients.yml <https://github.com/pierky/arouteserver/blob/master/config.d/clients.yml>`__

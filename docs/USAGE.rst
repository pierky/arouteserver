Usage
=====

The script can be executed via command-line:

  .. code:: bash

    # if cloned from GitHub, from the repository's root directory:
    export PYTHONPATH="`pwd`"
    ./scripts/arouteserver bird --ip-ver 4 -o /etc/bird/bird4.conf

    # if installed using pip:
    arouteserver bird --ip-ver 4 -o /etc/bird/bird4.conf

It produces the route server configuration for BIRD and saves it on ``/etc/bird/bird4.conf``.
To build the configuration for OpenBGPD, the ``bird`` sub-command must be replaced with ``openbgpd``.

The ``--target-version`` argument can be used to set the version of the target BGP daemon for which the configuration is generated: this allows to enable features that are supported only by more recent versions of BGP speakers and that, otherwise, would produce an error.

The script exits with ``0`` if everything is fine or with an exit code different than zero if something wrong occurs.

It can be scheduled at regular intervals to re-build the configuration (for example to add new clients or to update IRRDB information), test it and finally to deploy it in production:

  .. code:: bash

    # The following assumes that ARouteServer runs on the
    # route server itself, that is a thing that you may want
    # to avoid.
    arouteserver bird --ip-ver 4 -o /etc/bird/bird4.new && \
        bird -p -c /etc/bird/bird4.new && \
        cp /etc/bird/bird4.new /etc/bird/bird4.conf && \
        birdcl configure

Textual representation
----------------------

To build an HTML textual representation of route server's options and policies, the ``html`` command can be used:

  .. code:: bash

    arouteserver html -o /var/www/html/rs_description.html

This command writes an HTML page that contains a brief textual representation of route server's policies. An example can be found `here <_static/examples_rich.html>`_.

.. _automatic-clients:

Automatic ``clients.yml`` creation
----------------------------------

Create clients.yml file from PeeringDB records
**********************************************

The ``clients-from-peeringdb`` command can be used to automatically create a ``clients.yml`` file on the basis of PeeringDB records.
Given an IX LAN ID, it collects all the networks which are registered as route server clients on that LAN, then it builds the clients file accordingly.

If the IX LAN ID argument is not given, the script uses the `IX-F database <http://www.ix-f.net/ixp-database.html>`_ to show a list of IXPs and their PeeringDB ID; this can be used to easily search for the IXP PeeringDB ID.

.. code-block:: console

   $ arouteserver clients-from-peeringdb
   Loading IX-F database... OK
   
   Select the IXP for which the clients list must be built
   Enter the text to search for (IXP name, country, city): LINX
        ID  IXP description
        18  GB, London, London Internet Exchange LON1 (LINX LON1)
       777  US, Ashburn, LINX NoVA (LINX NoVA)
       321  GB, London, London Internet Exchange LON2 (LINX LON2)
   
   Enter the ID of the IXP you want to use to build the clients list: 18

Create clients.yml file from Euro-IX member list JSON file
**********************************************************

The `Euro-IX member list JSON schema <https://github.com/euro-ix/json-schemas>`_ defines a portable output format to export the list of members connected to an Internet Exchange. These files can be used to fetch the list of clients and their attributes (AS-SETs, max-prefix limits) and to use them to automatically build the ``clients.yml`` file used by ARouteServer to generate route server's configuration.

The ``clients-from-euroix`` command can be used for this purpose.

.. code:: bash

        arouteserver clients-from-euroix --url <URL> <ixp_id> -o <output_file>

The JSON file may contain information about more than one IXP for every IX. For example, AMS-IX has 'AMS-IX', 'AMS-IX Caribbean', 'AMS-IX Hong Kong' and more. To filter only those clients which are connected to the IXP of interest an identifier (``ixp_id``) is needed. When executed without the ``ixp_id`` argument, the command prints the list of IXPs and VLANs reported in the JSON file; the ID can be found on this list:

.. code-block:: console

	$ arouteserver clients-from-euroix --url https://my.ams-ix.net/api/v1/members.json
	IXP ID 1, short name 'AMS-IX'
	 - VLAN ID 502, name 'GRX', IPv4 prefix 193.105.101.0/25, IPv6 prefix 2001:7f8:86:1::/64
	 - VLAN ID 504, name 'MDX', IPv4 prefix 195.60.82.128/26
	 - VLAN ID 600, name 'PI'
	 - VLAN ID 501, name 'ISP', IPv4 prefix 103.247.139.0/25, IPv6 prefix 2001:13c7:6004::/64
	IXP ID 3, short name 'AMS-IX Caribbean'
	 - VLAN ID 600, name 'PI'
	 - VLAN ID 501, name 'ISP', IPv4 prefix 103.247.139.0/25, IPv6 prefix 2001:13c7:6004::/64
	IXP ID 2, short name 'AMS-IX Hong Kong'
	 - VLAN ID 501, name 'ISP', IPv4 prefix 103.247.139.0/25, IPv6 prefix 2001:13c7:6004::/64
	...

Finally, the list of clients and their attributes can be fetched:

.. code-block:: console

        $ arouteserver clients-from-euroix --url https://my.ams-ix.net/api/v1/members.json 1 --vlan 502
        clients:
        - asn: 58453
          description: China Mobile International Limited
          ip: 193.105.101.100
        - asn: 33849
          description: Comfone AG
          ip: 193.105.101.30
        - asn: 8959
          description: Emirates Telecommunications Corporation (Etisalat) (GRX)
          ip: 193.105.101.22
        - asn: 8959
          description: Emirates Telecommunications Corporation (Etisalat) (GRX)
          ip: 193.105.101.62
        - asn: 12322
          description: Free SAS
          ip: 193.105.101.28
        ...

An example from the LONAP:

.. code-block:: console

        $ arouteserver clients-from-euroix --url https://portal.lonap.net/apiv1/member-list/list 1
        clients:
        - asn: 42
          cfg:
            filtering:
              irrdb:
                as_sets:
                - AS-PCH
              max_prefix:
                limit_ipv4: 100
          description: Packet Clearing House AS42
          ip: 5.57.80.238
        - asn: 42
          cfg:
            filtering:
              irrdb:
                as_sets:
                - AS-PCH
              max_prefix:
                limit_ipv6: 100
          description: Packet Clearing House AS42
          ip: 2001:7f8:17::2a:1
        - asn: 714
          cfg:
            filtering:
              irrdb:
                as_sets:
                - AS-APPLE
              max_prefix:
                limit_ipv4: 1000
          description: Apple Europe Ltd
          ip: 5.57.81.57
        ...

To get a list of all the available options, run the ``arouteserver clients-from-euroix --help`` command.

.. _ixp-manager-integration:

Integration with IXP-Manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since the popular `IXP-Manager <https://github.com/inex/IXP-Manager>`_ allows to `export the list of members in Euro-IX JSON format <https://github.com/inex/IXP-Manager/wiki/Euro-IX-Member-Data-Export>`_, this ARouteServer's command can also be used to integrate the two tools:

.. code:: bash

        #!/bin/bash

        set -e

        # Setup an API key on IXP-Manager and write it below.
        # https://github.com/inex/IXP-Manager/wiki/Euro-IX-Member-Data-Export#setting-up-an-api-key
        api_key="YOURAPIKEY"

        # Adjust the URL and point it to your IXP-Manager application.
        url="https://www.example.com/ixp/apiv1/member-list/list/key/$api_key"

        # This is the IXP ID you want to export members from.
        ixp_id=1

        # Path to the clients file.
        clients_file=~/ars/clients-from-ixpmanager.yml

        # Build the clients file using info from IXP-Manager.
        arouteserver clients-from-euroix \
                -o $clients_file \
                --url "$url" $ixp_id

        # Build the route server configuration.
        arouteserver bird \
                --clients $clients_file \
                --ip-ver 4 \
                -o /etc/bird/bird4.new

        # Now test the new configuration and, finally,
        # push it to the route server.
        ...

Live tests, development and customization
-----------------------------------------

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

More details on :ref:`How to build custom scenarios`.

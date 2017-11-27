``configure`` command output
----------------------------

The ``configure`` command can be used to quickly generate policy definition files (*general.yml*) which are based on suggested settings and best practices.

A list of BGP communities is also automatically built.

.. code-block:: console

   $ arouteserver configure --output general.yml
   
   BGP daemon
   ==========
   
   Depending on the BGP daemon used for the route server some features may not be
   available.
   
   Details here:
   https://arouteserver.readthedocs.io/en/latest/CONFIG.html#caveats-and-
   limitations
   
   Which BGP daemon will be used? [bird/openbgpd] bird
   
   Router server's ASN
   ===================
   
   What's the ASN of the route server? 64496
   
   Route server's BGP router-id
   ============================
   
   Please enter the route server BGP router-id: 192.0.2.1
   
   List of local networks
   ======================
   
   A list of local IPv4/IPv6 networks must be provided here: routes announced by
   route server clients for these prefixes will be filtered out.
   
   Please enter a comma-separated list of local networks: 192.0.2.0/24,2001:db8::/32
   
   
   Route server policy definition file generated successfully!
   
   The content of the general configuration file will now be written to general.yml
   
   Some notes:
   
    - Accepted prefix lengths are 8-24 for IPv6 and 12-48 for IPv6.
    - Routes with 'transit-free networks' ASNs in the middle of AS_PATH are
   rejected.
    - IRR-based filters are enabled; prefixes that are more specific of those
   registered are accepted.
    - PeeringDB is used to fetch AS-SETs for those clients that are not explicitly
   configured.
    - RPKI ROAs are used as if they were route objects to further enrich IRR data.
    - Routes tagged with the GRACEFUL_SHUTDOWN well-known community (65535:0) are
   processed accordingly to draft-ietf-grow-bgp-gshut.

The textual description (HTML) generated on the basis of the *general.yml* files produced by this command is also reported here.

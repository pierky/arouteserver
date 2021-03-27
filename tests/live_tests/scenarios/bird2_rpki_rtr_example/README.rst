BIRD v2 RTR protocol
********************

A simple BIRD v2 scenario to verify the ``rpki_roas.source`` setting when an external resource must be used to pull ROAs (like an external validator).

The files used here are links to those provided within the ``examples/bird2_rpki_rtr`` directory.

AS1 announces 193.0.0.0/24 with origin AS 1.

Initially, no RTR sessions are active on the route-server, and the route is accepted.

In a second stage, a validator instance is spun up and connected to the route-server. The local file routinator_local_exceptions.json is used to instruct the RPKI validator to advertise a ROA for 193.0.0.0/21 with origin AS 3333.

Once the RTR session is up, the route-server is checked again to verify that the route from AS1 is no longer accepted and tagged with the RPKI INVALID ext community.

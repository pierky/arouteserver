RTR protocol
************

A simple scenario to verify the ``rpki_roas.source`` and ``rpki_aspas.source`` settings when an external resource must be used to pull RPKI ROAs and ASPAs (like an external validator).

The files used here are links to those provided within the ``examples/rpki_rtr`` directory.

AS1 announces the following prefixes:

- 193.0.0.0/24, with origin AS 1;
- 193.0.9.0/24, with AS_PATH "1 103";
- 193.0.8.0/24, with AS_PATH "1 104";
- 193.0.10.0/24, with AS_PATH "1 105".

Initially, no RTR sessions are active on the route-server, and all the routes are accepted.

In a second stage, a validator instance is spun up and connected to the route-server. RTRTR is used here, configured to serve a static JSON file (*rpki.json*) in the RIPE RPKI Validator format, so that the data received over RTR is completely predictable and no access to the real RPKI repositories is needed. It advertises:

- a ROA for 193.0.0.0/21 with origin AS 3333;
- an ASPA for AS 103, whose only provider is AS 1;
- an ASPA for AS 104, whose only provider is AS 200.

Since ASPA payloads are carried only by version 2 of the RTR protocol, the RTR sessions configured in the *rpki_rtr_config.local* files negotiate that version explicitly.

Once the RTR session is up, the route-server is checked again to verify that:

- ASPAs are actually received over the RTR session;
- the route for 193.0.0.0/24 from AS1 is no longer accepted, because it's RPKI INVALID (and it's tagged with the RPKI INVALID ext community, BIRD only);
- the route for 193.0.8.0/24 is no longer accepted, because the 104 -> 1 hop of its AS_PATH is not authorized by the ASPA of AS 104;
- the routes for 193.0.9.0/24 (ASPA VALID) and 193.0.10.0/24 (ASPA UNKNOWN, no ASPA exists for AS 105) are still accepted.

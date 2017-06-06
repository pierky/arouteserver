Reject policy: `tag`
********************

This scenario uses the same base layout of the *global* one, with the addition of an *Invalid routes collector* that receives only the routes that have been classified as *invalid* by the route server.

All the test cases used here inherit from the ``LiveScenario_TagRejectPolicy`` class, that dynamically changes the ``general.yml`` content to reflect the use of the ``tag`` ``reject_policy``: the BGP community used to mark the rejected routes and the reject reasons is ``65520:x``.

BIRD and OpenBGPD are configured using *.local* files to setup the sessions with the route collector and to properly announce only the invalid routes that have been previously marked with the ``reject_reason`` BGP community.

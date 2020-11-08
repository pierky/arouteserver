Max-prefix limits
*****************

General policy:

- limit: 4
- peering DB: True (increment: 1 / 20%)
- action: block

AS1:

- no peering DB
- no specific limits
- expected limit: 4

- n. of announced routes: 5 (all valid)
- expectations:

  - BIRD 1.6.x: only 4 routes received
  - BIRD 2.0.7: 4 valid imported, 5 received
  - OpenBGPD: session down

AS2 (client with peering_db.increment set to 0/0):

- peering DB (3)
- no specific limits
- expected limit: 3

- n. of announced routes: 5 (all valid)
- expectations:

  - BIRD 1.6.x: only 3 routes received
  - BIRD 2.0.7: 3 imported, 5 received
  - OpenBGPD: session down

AS3:

- specific limit: 2
- expected limit: 2

- n. of announced routes: 5 (all valid)
- expectations:

  - BIRD 1.6.x: only 2 routes received
  - BIRD 2.0.7: 2 imported, 5 received
  - OpenBGPD: session down

AS4:

- peering DB (4)
- no specific limits
- expected limit: 6 (given by (4 + 1) * 1.20)

- n. of announced routes: 7 (all valid)
- expectations:

  - BIRD 1.6.x: only 6 routes received
  - BIRD 2.0.7: 6 imported, 7 received
  - OpenBGPD: session down

AS5 (only for BIRD):
- specific limit: 3
- expected limit: 3
- configured with ``count_rejected_routes: True`` (default value) and ``action: shutdown``

- n. of announced routes: 4 (2 valid, 2 bogons)
- expectations:

  - BIRD 1.6.x: session down
  - BIRD 2.0.7: session up, all routes received

AS6 (only for BIRD):
- specific limit: 3
- expected limit: 3
- configured with ``count_rejected_routes: False`` (client specific value) and ``action: shutdown``

- n. of announced routes: 4 (2 valid, 2 bogons)
- expectations:

  - BIRD 1.6.x: all 4 routes received
  - BIRD 2.0.7: all 4 routes received

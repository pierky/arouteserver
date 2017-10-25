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

AS2 (client with peering_db.increment set to 0/0):

- peering DB (3)
- no specific limits
- expected limit: 3

AS3:

- specific limit: 2
- expected limit: 2

AS4:

- peering DB (4)
- no specific limits
- expected limit: 6 (given by (4 + 1) * 1.20)

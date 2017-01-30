Max-prefix limits
*****************

General policy:

- limit: 4
- peering DB: True
- action: block

AS1:

- no peering DB
- no specific limits
- expected limit: 4

AS2:

- peering DB (3)
- no specific limits
- expected limit: 3

AS3:

- specific limit: 2
- expected limit: 2

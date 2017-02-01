Path hiding mitigation technique
********************************

AS1, AS2, AS3 and AS4 are clients of the route server. AS4 has ADD-PATH rx on.

Only one prefix is used, *AS101_pref_ok1*, announced by AS101 to AS1 and AS2:

- AS101 -> AS1, AS_PATH = [101]
- AS101 -> AS2, AS_PATH = [101 101 101 101]

The route server has the path toward AS1 as the preferred one.

AS1 announces this prefix to the rs after having added the *do not announce to AS3* and *do not announce to AS4* BGP communities.

- When mitigation is on, AS3 and AS4 receive the prefix via the sub-optimal path toward AS2.
- When mitigation is off, AS3 does not receive the prefix at all, AS4 receives it because of ADD-PATH capability.

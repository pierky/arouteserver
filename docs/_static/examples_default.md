Configuration of route server 192.0.2.2 at AS999
======================================================================

BGP sessions default configuration
----------------------------------

* **Passive** sessions are configured toward neighbors.
* GTSM (Generalized TTL Security Mechanism - [RFC5082](//tools.ietf.org/html/rfc5082)) is **disabled** on sessions toward the neighbors.
* **ADD-PATH** capability ([RFC7911](//tools.ietf.org/html/rfc7911)) is **not** negotiated by default.

Route server general behaviours
-------------------------------

* Route server ASN is **not prepended** to the AS_PATH of routes announced to clients ([RFC7947 section 2.2.2.1](https://tools.ietf.org/html/rfc7947#section-2.2.2.1)).
* Route server **does  implement** path-hiding mitigation techniques ([RFC7947 section 2.3.1](https://tools.ietf.org/html/rfc7947#section-2.3.1)).


Default filtering policy
------------------------

### NEXT_HOP attribute

* The route server verifies that the NEXT_HOP attribute of routes received from a client matches the **IP address of the client itself**.

### AS_PATH attribute

* Routes whose **AS_PATH is longer than 32** ASNs are rejected.
* The **left-most ASN** in the AS_PATH of any route announced to the route server must be the ASN of the announcing client.
* Routes whose AS_PATH contains [**private or invalid ASNs**](http://mailman.nanog.org/pipermail/nanog/2016-June/086078.html) are rejected.

* Routes with an AS_PATH containing one or more **"never via route-servers" networks**' ASNs are **rejected**.

  List of "never via route-servers" networks' ASNs is generated from PeeringDB.

### IRRDBs prefix/origin ASN enforcement

* Origin ASN validity is **enforced**. Routes whose origin ASN is not authorized by the client's AS-SET are rejected.
* Announced prefixes validity is **enforced**. Routes whose prefix is not part of the client's AS-SET are rejected.

### RPKI BGP Prefix Origin Validation


* [RPKI BGP Origin Validation](https://tools.ietf.org/html/rfc6483) of routes received by the route server is **disabled**.



### Min/max prefix length


* Only prefixes whose length is in the following range are accepted by the route server:
	+ IPv4: 8-24
	+ IPv6: 12-48







Announcement control via BGP communities
----------------------------------------


* Routes tagged with the **NO_EXPORT** or **NO_ADVERTISE** communities received by the route server are propagated to other clients with those communities unaltered.



| Function | Standard | Extended | Large |
| --- | --- | --- | --- |



* The following 16bit ASNs can be used in standard BGP communities to implement announcement control for clients having a 32bit ASN. They can be used in place of the 32bit ASN to set the value of `peer_as` in the standard BGP communities listed above.

| 32bit ASN | Client | 16bit mapped ASN |
| --- | --- | --- |
| 65551 | AS65551 192.0.2.33 | 64512 |



Reject reasons
--------------

* The following values are used to identify the reason for which routes are rejected. This is mostly used for troubleshooting, internal reporting purposes, looking glasses or in the route server log files.


| ID | Reason |
| --- | --- |
| 0 |Generic code: the route must be treated as rejected |
| 1 | Invalid AS_PATH length |
| 2 | Prefix is bogon |
| 3 | Prefix is in global blacklist |
| 4 | Invalid AFI |
| 5 | Invalid NEXT_HOP |
| 6 | Invalid left-most ASN |
| 7 | Invalid ASN in AS_PATH |
| 8 | Transit-free ASN in AS_PATH |
| 9 | Origin ASN not in IRRDB AS-SETs |
| 10 | IPv6 prefix not in global unicast space |
| 11 | Prefix is in client blacklist |
| 12 | Prefix not in IRRDB AS-SETs |
| 13 | Invalid prefix length |
| 14 | RPKI INVALID route |
| 15 | Never via route-servers ASN in AS_PATH |
| 65535 | Unknown |



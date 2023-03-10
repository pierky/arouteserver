Configuration of route server 192.0.2.1 at AS64496
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
* Routes with an AS_PATH containing one or more of the following **"transit-free" networks**' ASNs
are **rejected**.

  List of "transit-free" networks' ASNs:
[174](https://stat.ripe.net/AS174), [701](https://stat.ripe.net/AS701), [1299](https://stat.ripe.net/AS1299), [2914](https://stat.ripe.net/AS2914), [3257](https://stat.ripe.net/AS3257), [3320](https://stat.ripe.net/AS3320), [3356](https://stat.ripe.net/AS3356), [5511](https://stat.ripe.net/AS5511), [6453](https://stat.ripe.net/AS6453), [6461](https://stat.ripe.net/AS6461), [6762](https://stat.ripe.net/AS6762), [6830](https://stat.ripe.net/AS6830), [7018](https://stat.ripe.net/AS7018), [12956](https://stat.ripe.net/AS12956)
* Routes with an AS_PATH containing one or more **"never via route-servers" networks**' ASNs are **rejected**.

  List of "never via route-servers" networks' ASNs is generated from PeeringDB.

### IRRDBs prefix/origin ASN enforcement

* Origin ASN validity is **enforced**. Routes whose origin ASN is not authorized by the client's AS-SET are rejected.
* Announced prefixes validity is **enforced**. Routes whose prefix is not part of the client's AS-SET are rejected.
  Longer prefixes that are covered by one entry of the resulting route set are accepted.
* Use **RPKI ROAs** to validate routes whose origin ASN is authorized by the client's AS-SET but whose prefix is not.
* Use **NIC.BR Whois DB dump** to validate routes whose origin ASN is authorized by the client's AS-SET but whose prefix is not.
* Database is fetched from ftp://ftp.registro.br/pub/numeracao/origin/nicbr-asn-blk-latest.txt.
* Route **validity state** is signalled to route server clients using the following **BGP communities**:


| Validity state | Standard | Extended | Large |
| --- | --- | --- | --- |
| Prefix is included in client's AS-SET | 64512:11 | None | 64496:64512:11 |
| Prefix is NOT included in client's AS-SET | 64512:10 | None | 64496:64512:10 |
| Origin ASN is included in client's AS-SET | 64512:21 | None | 64496:64512:21 |
| Origin ASN is NOT included in client's AS-SET | 64512:20 | None | 64496:64512:20 |
| Prefix matched by a RPKI ROA for the authorized origin ASN | 64512:31 | None | 64496:64512:31 |
| Route authorized soley because of a client white list entry | 64512:41 | None | 64496:64512:41 |

### RPKI BGP Prefix Origin Validation


* [RPKI BGP Origin Validation](https://tools.ietf.org/html/rfc6483) of routes received by the route server is **enabled**.
* When an INVALID route is received by the route server, **it is rejected**.
* The following communities are used to keep track of the validity state of the routes (only internally to the route server, they are not propagated to the clients):


| State | Standard | Extended | Large |
| --- | --- | --- | --- |
| Valid | 64512:51 | None | 64496:1000:1 |
| Unknown | 64512:52 | None | 64496:1000:2 |
| Invalid | 64512:53 | None | 64496:1000:4 |
* In circumstances (if any) where BGP Origin Validation is not performed, the following BGP communities are attached to the route:

| Description | Standard | Extended | Large |
| --- | --- | --- | --- |
| RPKI BGP Origin Validation not performed | 64512:50 | None | 64496:1000:3 |




### RPKI ROAs


* RPKI ROAs are fetched from the RIPE RPKI Validator format cache files at <a href="https://console.rpki-client.org/vrps.json" rel="noopener">https://console.rpki-client.org/vrps.json</a>, <a href="https://rpki.gin.ntt.net/api/export.json" rel="noopener">https://rpki.gin.ntt.net/api/export.json</a>, <a href="https://rpki-validator.ripe.net/api/export.json" rel="noopener">https://rpki-validator.ripe.net/api/export.json</a>. The following Trust Anchors are used: APNIC RPKI Root, AfriNIC RPKI Root, LACNIC RPKI Root, RIPE NCC RPKI Root, apnic, afrinic, lacnic, ripe

### Max-pref limit


* A **max-prefix limit** is enforced; when it triggers, the session with the announcing client is **shutdown**.
* The limit, if not provided on a client-by-client basis, is learnt from the client's **PeeringDB record**.
* If no more specific limits exist for the client, the **general limit** of 170000 IPv4 routes and 12000 IPv6 routes is enforced.


### Min/max prefix length


* Only prefixes whose length is in the following range are accepted by the route server:
	+ IPv4: 8-24
	+ IPv6: 12-48






### Rejected prefixes


* The following prefixes are **unconditionally rejected**:

| Prefix | More specific | Comment |
| --- | --- | --- |
| 192.0.2.0/24 | any more specific prefix | None |
| 2001:db8::/32 | any more specific prefix | None |

* **Bogon prefixes** are rejected too.

| Prefix | More specific | Comment |
| --- | --- | --- |
| 0.0.0.0/0 | only the exact prefix | Default route |
| 0.0.0.0/8 | any more specific prefix | IANA - Local Identification |
| 10.0.0.0/8 | any more specific prefix | RFC 1918 - Private Use |
| 127.0.0.0/8 | any more specific prefix | IANA - Loopback |
| 169.254.0.0/16 | any more specific prefix | RFC 3927 - Link Local |
| 172.16.0.0/12 | any more specific prefix | RFC 1918 - Private Use |
| 192.0.2.0/24 | any more specific prefix | RFC 5737 - TEST-NET-1 |
| 192.88.99.0/24 | any more specific prefix | RFC 3068 - 6to4 prefix |
| 192.168.0.0/16 | any more specific prefix | RFC 1918 - Private Use |
| 198.18.0.0/15 | any more specific prefix | RFC 2544 - Network Interconnect Device Benchmark Testing |
| 198.51.100.0/24 | any more specific prefix | RFC 5737 - TEST-NET-2 |
| 203.0.113.0/24 | any more specific prefix | RFC 5737 - TEST-NET-3 |
| 224.0.0.0/3 | any more specific prefix | RFC 5771 - Multcast (formerly Class D) |
| 100.64.0.0/10 | any more specific prefix | RFC 6598 - Shared Address Space |
| ::/0 | only the exact prefix | Default route |
| ::/8 | any more specific prefix | loopback, unspecified, v4-mapped |
| 64:ff9b::/96 | any more specific prefix | RFC 6052 - IPv4-IPv6 Translation |
| 100::/8 | any more specific prefix | RFC 6666 - reserved for Discard-Only Address Block |
| 200::/7 | any more specific prefix | RFC 4048 - Reserved by IETF |
| 400::/6 | any more specific prefix | RFC 4291 - Reserved by IETF |
| 800::/5 | any more specific prefix | RFC 4291 - Reserved by IETF |
| 1000::/4 | any more specific prefix | RFC 4291 - Reserved by IETF |
| 2001::/33 | any more specific prefix | RFC 4380 - Teredo prefix |
| 2001:0:8000::/33 | any more specific prefix | RFC 4380 - Teredo prefix |
| 2001:2::/48 | any more specific prefix | RFC 5180 - Benchmarking |
| 2001:3::/32 | any more specific prefix | RFC 7450 - Automatic Multicast Tunneling |
| 2001:10::/28 | any more specific prefix | RFC 4843 - Deprecated ORCHID |
| 2001:20::/28 | any more specific prefix | RFC 7343 - ORCHIDv2 |
| 2001:db8::/32 | any more specific prefix | RFC 3849 - NON-ROUTABLE range to be used for documentation purpose |
| 2002::/16 | any more specific prefix | RFC 3068 - 6to4 prefix |
| 3ffe::/16 | any more specific prefix | RFC 5156 - used for the 6bone but was returned |
| 4000::/3 | any more specific prefix | RFC 4291 - Reserved by IETF |
| 5f00::/8 | any more specific prefix | RFC 5156 - used for the 6bone but was returned |
| 6000::/3 | any more specific prefix | RFC 4291 - Reserved by IETF |
| 8000::/3 | any more specific prefix | RFC 4291 - Reserved by IETF |
| a000::/3 | any more specific prefix | RFC 4291 - Reserved by IETF |
| c000::/3 | any more specific prefix | RFC 4291 - Reserved by IETF |
| e000::/4 | any more specific prefix | RFC 4291 - Reserved by IETF |
| f000::/5 | any more specific prefix | RFC 4291 - Reserved by IETF |
| f800::/6 | any more specific prefix | RFC 4291 - Reserved by IETF |
| fc00::/7 | any more specific prefix | RFC 4193 - Unique Local Unicast |
| fe80::/10 | any more specific prefix | RFC 4291 - Link Local Unicast |
| fec0::/10 | any more specific prefix | RFC 4291 - Reserved by IETF |
| ff00::/8 | any more specific prefix | RFC 4291 - Multicast |


* IPv6 prefixes are accepted only if part of the IPv6 Global Unicast space 2000::/3.



Graceful BGP session shutdown
-----------------------------


* Routes tagged with the **GRACEFUL_SHUTDOWN** BGP community (65535:0) have their LOCAL_PREF attribute lowered to 0.


Announcement control via BGP communities
----------------------------------------


* Routes tagged with the **NO_EXPORT** or **NO_ADVERTISE** communities received by the route server are propagated to other clients with those communities unaltered.



| Function | Standard | Extended | Large |
| --- | --- | --- | --- |
| Do not announce to any client | 0:64496 | None | 64496:0:0 |
| Announce to peer, even if tagged with the previous community | 64496:peer_as | None | 64496:1:peer_as |
| Do not announce to peer | 0:peer_as | None | 64496:0:peer_as |
| Prepend the announcing ASN once to peer | 65511:peer_as | None | 64496:101:peer_as |
| Prepend the announcing ASN twice to peer | 65512:peer_as | None | 64496:102:peer_as |
| Prepend the announcing ASN thrice to peer | 65513:peer_as | None | 64496:103:peer_as |
| Prepend the announcing ASN once to any | 65501:64496 | None | 64496:101:0 |
| Prepend the announcing ASN twice to any | 65502:64496 | None | 64496:102:0 |
| Prepend the announcing ASN thrice to any | 65503:64496 | None | 64496:103:0 |
| Add NO_EXPORT to peer | 65281:peer_as | None | 64496:65281:peer_as |
| Add NO_ADVERTISE to peer | 65282:peer_as | None | 64496:65282:peer_as |



* The following 16bit ASNs can be used in standard BGP communities to implement announcement control for clients having a 32bit ASN. They can be used in place of the 32bit ASN to set the value of `peer_as` in the standard BGP communities listed above.

| 32bit ASN | Client | 16bit mapped ASN |
| --- | --- | --- |
| 65551 | AS65551 192.0.2.33 | 64512 |



Reject reasons
--------------

* The following values are used to identify the reason for which routes are rejected. This is mostly used for troubleshooting, internal reporting purposes, looking glasses or in the route server log files.

* Routes which are rejected are tagged with the BGP community that represents the reason for which they were discarded.

| ID | Reason | Standard | Extended | Large |
| --- | --- | --- | --- | --- |
| 0 | Generic code: the route must be treated as rejected | 65520:0 | None | 64496:65520:0 |
| 1 | Invalid AS_PATH length | 65520:1 | None | 64496:65520:1 |
| 2 | Prefix is bogon | 65520:2 | None | 64496:65520:2 |
| 3 | Prefix is in global blacklist | 65520:3 | None | 64496:65520:3 |
| 4 | Invalid AFI | 65520:4 | None | 64496:65520:4 |
| 5 | Invalid NEXT_HOP | 65520:5 | None | 64496:65520:5 |
| 6 | Invalid left-most ASN | 65520:6 | None | 64496:65520:6 |
| 7 | Invalid ASN in AS_PATH | 65520:7 | None | 64496:65520:7 |
| 8 | Transit-free ASN in AS_PATH | 65520:8 | None | 64496:65520:8 |
| 9 | Origin ASN not in IRRDB AS-SETs | 65520:9 | None | 64496:65520:9 |
| 10 | IPv6 prefix not in global unicast space | 65520:10 | None | 64496:65520:10 |
| 11 | Prefix is in client blacklist | 65520:11 | None | 64496:65520:11 |
| 12 | Prefix not in IRRDB AS-SETs | 65520:12 | None | 64496:65520:12 |
| 13 | Invalid prefix length | 65520:13 | None | 64496:65520:13 |
| 14 | RPKI INVALID route | 65520:14 | None | 64496:65520:14 |
| 15 | Never via route-servers ASN in AS_PATH | 65520:15 | None | 64496:65520:15 |
| 65535 | Unknown | 65520:65535 | None | 64496:65520:65535 |



* In addition to the BGP communities reported above, the following *custom* ones are also used for the reject reasons listed below.

| ID | Reason | Standard | Extended | Large |
| --- | --- |  --- | --- | --- |
| 1 | Invalid AS_PATH length | None | None | 64496:1101:5 |
| 2 | Prefix is bogon | None | None | 64496:1101:3 |
| 5 | Invalid NEXT_HOP | None | None | 64496:1101:8 |
| 6 | Invalid left-most ASN | None | None | 64496:1101:7 |
| 7 | Invalid ASN in AS_PATH | None | None | 64496:1101:4 |
| 8 | Transit-free ASN in AS_PATH | None | None | 64496:1101:14 |
| 9 | Origin ASN not in IRRDB AS-SETs | None | None | 64496:1101:10 |
| 10 | IPv6 prefix not in global unicast space | None | None | 64496:1101:3 |
| 12 | Prefix not in IRRDB AS-SETs | None | None | 64496:1101:9 |
| 14 | RPKI INVALID route | None | None | 64496:1101:13 |

Configuration of route server 192.0.2.2 at AS999
======================================================================

BGP sessions default configuration
----------------------------------

* **Passive** sessions are configured toward neighbors.
* GTSM (Generalized TTL Security Mechanism - [RFC5082](//tools.ietf.org/html/rfc5082)) is **enabled** on sessions toward the neighbors.
* **ADD-PATH** capability ([RFC7911](//tools.ietf.org/html/rfc7911)) is negotiaded by default; the route server is configured as "able to send multiple paths to its peer".

Route server general behaviours
-------------------------------

* Route server ASN is **not prepended** to the AS_PATH of routes announced to clients ([RFC7947 section 2.2.2.1](https://tools.ietf.org/html/rfc7947#section-2.2.2.1)).
* Route server **does  implement** path-hiding mitigation techniques ([RFC7947 section 2.3.1](https://tools.ietf.org/html/rfc7947#section-2.3.1)).


Default filtering policy
------------------------

### NEXT_HOP attribute

* The route server verifies that the NEXT_HOP attribute of routes received from a client matches the **IP address of the client itself** or one of the **IP addresses of other clients from the same AS**. This "allows an organization with multiple connections into an IXP configured with different IP addresses to direct traffic off the IXP infrastructure through any of their connections for traffic engineering or other purposes." [RFC7948, section 4.8](https://tools.ietf.org/html/rfc7948#section-4.8)

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
Also, the following ASNs are always included:
[2914](https://stat.ripe.net/AS2914), [3491](https://stat.ripe.net/AS3491)
### IRRDBs prefix/origin ASN enforcement

* Origin ASN validity is **enforced**. Routes whose origin ASN is not authorized by the client's AS-SET are rejected.
* Announced prefixes validity is **enforced**. Routes whose prefix is not part of the client's AS-SET are rejected.
  Longer prefixes that are covered by one entry of the resulting route set are accepted.
* Use **RPKI ROAs** to validate routes whose origin ASN is authorized by the client's AS-SET but whose prefix is not.
* Route **validity state** is signalled to route server clients using the following **BGP communities**:


| Validity state | Standard | Extended | Large |
| --- | --- | --- | --- |
| Origin ASN is included in client's AS-SET | 65530:1 | None | 999:65530:1 |
| Origin ASN is NOT included in client's AS-SET | 65530:0 | None | 999:65530:0 |
| Prefix matched by a RPKI ROA for the authorized origin ASN | 65530:2 | None | 999:65530:2 |
| Prefix matched by an entry of the ARIN Whois DB dump | 65530:4 | None | 999:65530:4 |
| Route authorized soley because of a client white list entry | 65530:3 | None | 999:65530:3 |

### RPKI BGP Prefix Origin Validation


* [RPKI BGP Origin Validation](https://tools.ietf.org/html/rfc6483) of routes received by the route server is **enabled**.
* When an INVALID route is received by the route server, **it is rejected**.



### RPKI ROAs


* RPKI ROAs are fetched from the RIPE RPKI Validator format cache files at examples/rich/ripe-rpki-cache.json. The following Trust Anchors are used: APNIC RPKI Root, AfriNIC RPKI Root, LACNIC RPKI Root, RIPE NCC RPKI Root, apnic, afrinic, lacnic, ripe

### Max-pref limit


* A **max-prefix limit** is enforced; when it triggers, the session with the announcing client is **restarted** after 30 minutes.
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
| 192.0.2.0/24 | any more specific prefix | Local network |
| 2001:db8:1:1::/64 | any more specific prefix | Local network |

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


Blackhole filtering
-------------------


* Blackhole filtering of more specific IP prefixes can be requested by tagging them with the following **BGP communities**: 65534:0, 999:666:0,  65535:666 ([BLACKHOLE](https://tools.ietf.org/html/rfc7999#section-5) well-known community)

* By default, routes are **propagated** to all the clients unless they have been explicitly configured to not receive them.
* IPv4 routes are propagated to clients after their **NEXT_HOP attribute has been rewritten** to 192.0.2.66.
* IPv6 routes are propagated to clients after their **NEXT_HOP attribute has been rewritten** to 2001:db8:1:1::66.
* Before being announced to clients, all the routes are tagged with the BLACKHOLE well-known community.
  The NO_EXPORT well-known community is also added.
* Blackhole filtering requests bypass any RPKI validation check and min/max length check.

Graceful BGP session shutdown
-----------------------------


* Routes tagged with the **GRACEFUL_SHUTDOWN** BGP community (65535:0) have their LOCAL_PREF attribute lowered to 0.


Announcement control via BGP communities
----------------------------------------


* Routes tagged with the **NO_EXPORT** or **NO_ADVERTISE** communities received by the route server are propagated to other clients with those communities unaltered.



| Function | Standard | Extended | Large |
| --- | --- | --- | --- |
| Do not announce to any client | 0:999 | rt:0:999 | 999:0:999 |
| Announce to peer, even if tagged with the previous community | 999:peer_as | rt:999:peer_as | 999:999:peer_as |
| Do not announce_to peers with RTT <= than *X* ms (*) | 64511:X | rt:64511:X | 999:64511:X |
| Do not announce_to peers with RTT > than *X* ms (*) | 64512:X | rt:64512:X | 999:64512:X |
| Announce_to peers with RTT <= than *X* ms (*) | 64513:X | rt:64513:X | 999:64513:X |
| Announce_to peers with RTT > than *X* ms (*) | 64514:X | rt:64514:X | 999:64514:X |
| Do not announce to peer | 0:peer_as | rt:0:peer_as | 999:0:peer_as |
| Prepend the announcing ASN once to peer | 65504:peer_as | rt:65504:peer_as | 999:65504:peer_as |
| Prepend the announcing ASN twice to peer | 65505:peer_as | rt:65505:peer_as | 999:65505:peer_as |
| Prepend the announcing ASN thrice to peer | 65506:peer_as | rt:65506:peer_as | 999:65506:peer_as |
| Prepend once to peers with RTT > than *X* ms (*) | 64518:X | rt:64518:X | 999:64518:X |
| Prepend twice to peers with RTT > than *X* ms (*) | 64519:X | rt:64519:X | 999:64519:X |
| Prepend thrice to peers with RTT > than *X* ms (*) | 64520:X | rt:64520:X | 999:64520:X |
| Prepend once to peers with RTT <= than *X* ms (*) | 64515:X | rt:64515:X | 999:64515:X |
| Prepend twice to peers with RTT <= than *X* ms (*) | 64516:X | rt:64516:X | 999:64516:X |
| Prepend thrice to peers with RTT <= than *X* ms (*) | 64517:X | rt:64517:X | 999:64517:X |
| Prepend the announcing ASN once to any | 65501:999 | rt:65501:999 | 999:65501:999 |
| Prepend the announcing ASN twice to any | 65502:999 | rt:65502:999 | 999:65502:999 |
| Prepend the announcing ASN thrice to any | 65503:999 | rt:65503:999 | 999:65503:999 |
| Add NO_EXPORT to any | 65507:999 | rt:65507:999 | 999:65507:999 |
| Add NO_ADVERTISE to any | 65508:999 | rt:65508:999 | 999:65508:999 |
| Add NO_EXPORT to peer | 65509:peer_as | rt:65509:peer_as | 999:65509:peer_as |
| Add NO_ADVERTISE to peer | 65510:peer_as | rt:65510:peer_as | 999:65510:peer_as |


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


* For RTT-based communities, the following values can be used for *X*:
5, 10, 15, 20, 30, 50, 100, 200, 500
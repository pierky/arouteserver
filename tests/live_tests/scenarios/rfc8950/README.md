# RFC8950 scenario

A scenario to test announcements of IPv4 routes with an IPv6 NEXT_HOP, over an IPv6 session.

## AS1_1

- `AS1_v4_route1`: accepted.
- `AS1_v4_route2`: rejected, not in IRR data.
- `AS1_v4_route3`, announced by AS1_1 with AS1_2 NEXT_HOP: rejected.
- `AS1_v4_route4`: accepted (white list - pref).
- `AS1_v4_route5`: accepted (white list - route).
- `AS1_v4_route7`: accepted (ARIN Whois).
- `AS1_v4_route8`: accepted (RegistroBR).
- `AS1_v4_route9`: rejected (RPKI BOV AS0).
- `AS1_v4_route10`: accepted (RPKI BOV VALID).
- `AS1_v4_route11`: rejected (RPKI BOC INVALID).

## AS1_2

- `AS1_v4_route6`: announced with AS1_1 NEXT_HOP: accepted (same-as).

## AS2_1

- `AS2_v4_route12`: accepted (NEXT_HOP authorized-next-hop)

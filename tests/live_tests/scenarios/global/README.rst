Global scenario
***************

Built to group as many tests as possible in a single scenario.

- **AS1**:

  AS-SETs:

  - AS-AS1 (1.0.0.0/8, 128.0.0.0/7)
  - AS-AS1_CUSTOMERS (101.0.0.0/16)

  clients:

  - AS1_1 (192.0.2.11, RTT 0.1 ms)

    - next-hop-self configured in AS1_1.conf
    - next_hop.policy: strict (inherited from general config)

    Originated prefixes:

    ============   ============  ============  ====================================
    Prefix ID      Prefix        AS_PATH       Expected result
    ============   ============  ============  ====================================
    AS1_good1      1.0.1.0/24		       pass
    AS1_good2      1.0.2.0/24                  pass

    bogon1         10.0.0.0/24                 fail prefix_is_bogon
    local1         192.0.2.0/24                fail prefix_is_in_global_blacklist
    pref_len1      128.0.0.0/7                 fail prefix_len_is_valid
    peer_as1       128.0.0.0/8   [2, 1]        fail bgp_path.first != peer_as
    invalid_asn1   128.0.0.0/9   [1, 65536 1]  fail as_path_contains_invalid_asn
    aspath_len1    128.0.0.0/10  [1, 2x6]      fail bgp_path.len > 6
    ============   ============  ============  ====================================

  - AS1_2 (192.0.2.12, RTT 5 ms)

    - NO next-hop-self in AS1_2.conf (next-hop of AS101 used for AS101_good == 101.0.1.0/24)
    - next_hop.policy: same-as (from clients config)
    - not enabled to receive blackhole requests

    Originated prefixes:

    ===========    ===========     ==============  ===========================================
    Prefix ID      Prefix          Feature         Expected result    
    ===========    ===========     ==============  ===========================================
    AS1_good1      1.0.1.0/24
    AS1_good2      1.0.2.0/24
    AS1_good3      1.0.3.0/24      next_hop=AS1_1  win next_hop_is_valid_for_AS1_2 (same-as)
    ===========    ===========     ==============  ===========================================

- **AS2**:

  AS-SETs:

  - AS-AS2 (2.0.0.0/16)
  - AS-AS2_CUSTOMERS (101.0.0.0/16)

  clients:

  - AS2 (192.0.2.21, RTT 17.3 ms)

    - next-hop-self configured in AS2.conf
    - next_hop.policy: authorized_addresses (from clients config)
    - next_hop.authorized_addresses_list:
      - 192.0.2.21 and 2001:db8:1:1::21, its own IP addresses
      - 192.0.2.22 and 2001:db8:1:1::22, IP addresses not configured as route server client

    Originated prefixes:

    =======================  ================   =======================================   =================================================
    Prefix ID                Prefix             Feature                                   Expected result
    =======================  ================   =======================================   =================================================
    AS2_good1                2.0.1.0/24
    AS2_good2                2.0.2.0/24

    AS2_blackhole1           2.0.3.1/32         announced with BLACKHOLE 65535:666 comm   propagated with only 65535:666 to AS1_1 and AS3
                                                                                          (AS1_2 has "announce_to_client" = False) and
                                                                                          next-hop 192.0.2.66; NO_EXPORT also added
    AS2_blackhole2           2.0.3.2/32         announced with local 65534:0 comm         as above
    AS2_blackhole3           2.0.3.3/32         announced with local 65534:0:0 comm       as above

    AS2_nonclient_nexthop1   2.0.4.0/24         announce with an authorized next-hop      received by other clients
    AS2_nonclient_nexthop2   2.0.5.0/24         announce with an unknown next-hop         not received by other clients
    =======================  ================   =======================================   =================================================

- **AS3**:

  AS-SETs: none

  clients:

  - AS3 (192.0.2.31, RTT 123.8)

    - no enforcing of origin in AS-SET
    - no enforcing of prefix in AS-SET
    - ADD-PATH enabled
    - passive client-side (no passive on the route server)

    Originated prefixes:

    =================  ============ ================= ============================================
    Prefix ID          Prefix       Communities       Expected result
    =================  ============ ================= ============================================
    AS3_blacklist1     3.0.1.0/24                     fail prefix_is_in_AS3_1_blacklist

    AS3_cc_AS1only     3.0.2.0/24   0:999, 65501:1    seen on AS1_1/_2 only
    AS3_cc_not_AS1     3.0.3.0/24   0:1               seen on AS2 only
    AS3_cc_none        3.0.4.0/24   0:999             not seen
    AS3_prepend1any    3.0.5.0/24   999:65501         AS_PATH 3, 3
    AS3_prepend2any    3.0.6.0/24   999:65502         AS_PATH 3, 3, 3
    AS3_prepend3any    3.0.7.0/24   999:65503         AS_PATH 3, 3, 3, 3
    AS3_prepend1_AS1   3.0.8.0/24   65504:1           AS_PATH 3, 3 on AS1 clients
    AS3_prepend2_AS2   3.0.9.0/24   65505:2           AS_PATH 3, 3, 3 on AS2 clients
    AS3_prep3AS1_1any  3.0.10.0/24  65506:1 999:65501 AS_PATH 3, 3, 3, 3
                                                      on AS1 clients, 3, 3 on AS2 clients
    AS3_noexport_any   3.0.11.0/24  65507:999         received by all with NO_EXPORT
    AS3_noexport_AS1   3.0.12.0/24  65509:1 65506:2   (prepend x3 to AS2) received by AS1 with
                                                      NO_EXPORT
    Default_route      0.0.0.0/0                      rejected by rs
    =================  ============ ================= ============================================

- **AS4**:

  AS-SETs: none

  clients:

  - AS4 (192.0.2.41, RTT 600)

    - no enforcing of origin in AS-SET
    - no enforcing of prefix in AS-SET
    - RTT thresholds configured on rs: 5, 10, 15, 20, 30, 50, 100, 200, 500
    - other peers RTTs:
      - AS1_1: 0.1
      - AS1_2: 5
      - AS2: 17.3
      - AS3: 123.8

    Originated prefixes:

    =================  ============ ================= ============================================ ===============
    Prefix ID          Prefix       Communities       Expected result                              Who receives it
    =================  ============ ================= ============================================ ===============
    AS4_rtt_1          4.0.1.0/24   0:999 64532:3     Do not announce to any + announce to peers   AS1_1, AS1_2
                                                      with RTT <= 15 ms
    AS4_rtt_2          4.0.2.0/24   0:999 64532:1     Do not announce to any + announce to peers   AS1_1, AS1_2
                                                      with RTT <= 5 ms
    AS4_rtt_3          4.0.3.0/24   64531:3           Do not announce to peers with RTT > 15 ms    AS1_1, AS1_2
    AS4_rtt_4          4.0.4.0/24   64531:1           Do not announce to peers with RTT > 5 ms     AS1_1, AS1_2
    AS4_rtt_5          4.0.5.0/24   64531:1 65501:3   Do not announce to peers with RTT > 5 ms but AS1_1, AS1_2,
                                                      announce to AS3                              AS3
    AS4_rtt_6          4.0.6.0/24   64530:1 64531:7   Do not announce to peers with RTT <= 5 and   AS2
                                                      Do not announce to peers with RTT > 100
    AS4_rtt_7          4.0.7.1/32   65535:666 64531:4 BLACKHOLE request, do not announce to peers  AS1_1, AS2
                                                      with RTT > 20 (AS1_2 not enabled to receive
                                                      blackhole requests)
    =================  ============ ================= ============================================ ===============

- **AS101**:

  clients:

  - Not a route server client, it only peers with AS1_1, AS1_2 and AS2 on 192.0.2.101.

  - RPKI ROAs:

    == ==============  ====  ======
    ID Prefix          Max   ASN
    == ==============  ====  ======
    1  101.0.8.0/24          101
    2  101.0.9.0/24          102
    3  101.0.128.0/20  23    101
    == ==============  ====  ======

  Originated prefixes:

  ====================  ==============   ========== ==================================================================================
  Prefix ID             Prefix           AS_PATH    Expected result
  ====================  ==============   ========== ==================================================================================
  AS101_good1           101.0.1.0/24                fail next_hop_is_valid_for_AS1_2 (for the prefix announced by AS101 to AS1_2)
  AS101_no_rset         101.1.0.0/24                fail prefix_is_in_AS1_1_r_set and prefix_is_in_AS2_1_r_set
  AS102_no_asset        102.0.1.0/24     [101 102]  fail origin_as_in_AS1_1_as_set and origin_as_in_AS2_1_as_set

  AS101_bad_std_comm    101.0.2.0/24                add 65530:0, scrubbed by rs
  AS101_bad_lrg_comm    101.0.3.0/24                add 999:65530:0, scrubbed by rs
  AS101_other_s_comm    101.0.4.0/24                add 888:0, NOT scrubbed by rs
  AS101_other_l_comm    101.0.5.0/24                add 888:0:0, NOT scrubbed by rs
  AS101_bad_good_comms  101.0.6.0/24                add 65530:1,999:65530:1,777:0,777:0:0, 65530 are scrubbed by rs, 777:** are kept
  AS101_transitfree_1   101.0.7.0/24     [101 174]  fail as_path_contains_transit_free_asn
  AS101_roa_valid1      101.0.8.0/24                roa check ok (roa n. 1), tagged with 64512:1 / 999:64512:1
  AS101_roa_invalid1    101.0.9.0/24                roa check fail (roa n. 2, bad origin ASN), rejected
  AS101_roa_badlen      101.0.128.0/24              roa check fail (roa n. 3, bad length), rejected
  AS101_roa_blackhole   101.0.128.1/32              65535:666, pass because blackhole filtering request
  AS101_no_ipv6_gl_uni  8000:1::/32                 fail IPv6 global unicast space check
  ====================  ==============   ========== ==================================================================================

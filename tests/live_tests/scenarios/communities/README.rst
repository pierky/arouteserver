BGP communities
***************

Communities:

=== ======================= ================ ======================
fmt do_not_announce_to_peer announce_to_peer do_not_announce_to_any
=== ======================= ================ ======================
std 0:peer_as               999:peer_as      0:999
ext rt:0:peer_as            rt:999:peer_as   rt:0:999
lrg 999:0:peer_as           999:999:peer_as  999:0:999
=== ======================= ================ ======================

AS2

- announced prefixes:

  =========================== ========================= =============  =====================================================
  Prefix ID                   Comms                     Prefix         Expected result
  =========================== ========================= =============  =====================================================
  AS2_only_to_AS1_s           0:999, 999:1              2.0.1.0/24     only AS1 receives the prefix
  AS2_only_to_AS1_e           rt:0:999, rt:999:1        2.0.2.0/24     only AS1 receives the prefix
  AS2_only_to_AS1_l           999:0:999, 999:999:1      2.0.3.0/24     only AS1 receives the prefix
  AS2_only_to_AS131073_e      0:999, rt:999:131073      2.0.4.0/24     only AS131073 receives the prefix
  AS2_only_to_AS131073_l      999:0:999, 999:999:131073 2.0.5.0/24     only AS131073 receives the prefix
  AS2_bad_cust_comm1          65501:65501               2.0.6.0/24     AS1 and AS131073 receive the prefix without the cust
                                                                       community (scrubbed by the rs)
  =========================== ========================= =============  =====================================================

AS1

- configured to have its routes tagged with cust_comm1 (65501:65501, 999:65501:65501, rt:65501:65501)

- announced prefixes:

  =========================== ========================= =============  =====================================================
  Prefix ID                   Comms                     Prefix         Expected result
  =========================== ========================= =============  =====================================================
  AS1_good1                                             1.0.1.0/24     AS2 and AS131073 receive the prefix, tagged with the
                                                                       custom community
  =========================== ========================= =============  =====================================================

AS131073

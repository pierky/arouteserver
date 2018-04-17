Tag prefixes/origin ASNs present/not-present in IRRDb
*****************************************************

Built to test the ``irrdb.tag_as_set`` option.

Two sub-scenarios exist for this test:

1. AS-SETs are populated with origin ASNs and prefixes reported below.

2. AS-SETs are empty.

Communities:

    ==============  =====
    OK / Not OK     Comm
    ==============  =====
    prefix OK       64512
    prefix NOT OK   64513

    origin OK       64514
    origin NOT OK   64515

    RPKI ROA OK     64516
    ARIN Whois OK   64518

    route wht list  64517
    ==============  =====

RPKI ROAs:

    ==============  =====
    prefix          ASN
    ==============  =====
    2.4.0.0/16      AS2
    2.5.0.0/16      AS2
    2.7.0.0/16      AS2
    2.0.4.0/24      AS2
    3.1.0.0/16      AS3
    3.3.0.0/16      AS3
    6.0.1.0/24      AS6
    ==============  =====

ARIN Whois DB entries:

    ==============  =====
    prefix          ASN
    ==============  =====
    2.6.0.0/16      AS2
    2.7.0.0/16      AS2
    3.2.0.0/16      AS3
    3.3.0.0/16      AS3
    2.0.5.0/24      AS3
    6.0.1.0/24      AS6
    ==============  =====

AS2
---

- allowed objects:

  - prefix: 2.0.0.0/16
  - origin: [2]

- configuration:

  - enforcing: no
  - tagging: yes

- white lists:

  - prefixes: 2.2.0.0/16
  - asns: 21

AS2 announces:

    ====================== ============    ===========     ==========      ==========      =================  =================
    id                     prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected result 2
    ====================== ============    ===========     ==========      ==========      =================  =================
    AS2_pref_ok_origin_ok1 2.0.1.0/24      2               yes             yes             64512 64514        64513 64515
    AS2_pref_ko_origin_ok1 2.1.0.0/24      2               no              yes             64513 64514        64513 64515
    AS3_pref_ok_origin_ko1 2.0.2.0/24      2 3             yes             no              64512 64515        64513 64515
    AS3_pref_ko_origin_ko1 3.0.1.0/24      2 3             no              no              64513 64515        64513 64515
    AS2_pref_wl_origin_ok  2.2.1.0/24      2               yes (WL)        yes             64512 64514        64512 64515
    AS2_pref_wl_origin_ko  2.2.2.0/24      2 3             yes (WL)        no              64512 64515        the same
    AS2_pref_wl_origin_wl  2.2.3.0/24      2 21            yes (WL)        yes (WL)        64512 64514        the same
    AS2_pref_ko_origin_wl  2.3.1.0/24      2 21            no              yes (WL)        64513 64514        the same
    AS2_pref_ok_origin_wl  2.0.3.0/24      2 21            yes             yes (WL)        64512 64514        64513 64514
    AS2_roa2               2.5.0.0/16      2               no              yes             64513 64514 64516  64513 64515
    AS2_arin1              2.6.0.0/16      2               no              yes             64513 64514 64518  64513 64515
    AS2_roa3_arin2         2.7.0.0/16      2               no              yes             64513 64514 64516  64513 64515
                                                                                           64518
    AS2_ok_ok_roa3         2.0.4.0/24      2               yes             yes             64512 64514 64516  64513 64515
    AS2_ok_ok_arin3        2.0.5.0/24      2               yes             yes             64512 64514 64518  64513 64515
    ====================== ============    ===========     ==========      ==========      =================  =================

AS3
---

Not a route server client here, used just to track RPKI ROAs and ARIN Whois DB entries:

AS4
---

- allowed objects:

  - prefix: 4.0.0.0/16
  - origin: 4

- configuration:

  - enforcing: origin only
  - tagging: yes

- white lists:

  - prefixes: 4.2.0.0/16
  - asns: 41

  - routes:

    - exact 4.4.0.0/16, AS 44
    - 4.5.0.0/16, AS 43
    - 4.6.0.0/16, no origin AS

AS4 announces:

    ====================== ============    ===========     ==========      ==========      =================  =================
    id                     prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected result 2
    ====================== ============    ===========     ==========      ==========      =================  =================
    AS4_pref_ok_origin_ok1 4.0.1.0/24      4               yes             yes             64512 64514        rejected
    AS4_pref_ko_origin_ok1 4.1.0.0/24      4               no              yes             64513 64514        rejected
    AS3_pref_ok_origin_ko2 4.0.2.0/24      4 3             yes             no              rejected           rejected
    AS3_pref_ko_origin_ko1 3.0.1.0/24      4 3             no              no              rejected           rejected
    AS4_pref_wl_origin_ok  4.2.1.0/24      4               yes (WL)        yes             64512 64514        rejected
    AS4_pref_wl_origin_ko  4.2.2.0/24      4 3             yes (WL)        no              rejected           rejected
    AS4_pref_wl_origin_wl  4.2.3.0/24      4 41            yes (WL)        yes (WL)        64512 64514        the same
    AS4_pref_ko_origin_wl  4.3.1.0/24      4 41            no              yes (WL)        64513 64514        the same
    AS4_pref_ok_origin_wl  4.0.3.0/24      4 41            yes             yes (WL)        64512 64514        64513 64514
    AS4_routewl_1          4.4.0.0/16      4 44            r WL            r WL            64513 64515 64517  the same
    AS4_routewl_2          4.4.1.0/24      4 44            r WL KO         r WL            rejected           rejected
    AS4_routewl_3          4.5.1.0/24      4 43            r WL            r WL            64513 64515 64517  the same
    AS4_routewl_4          4.5.2.0/24      4 45            r WL            r WL KO         rejected           rejected
    AS4_routewl_5          4.6.1.0/24      4 45            r WL            r WL            64513 64515 64517  the same
    ====================== ============    ===========     ==========      ==========      =================  =================

AS5
---

- allowed objects (AS-SET from PeeringDB):

  - prefix: 5.0.0.0/16
  - origin: 5

configuration:

  - enforcing: prefix only
  - tagging: yes

- white lists:

  - prefixes: 5.2.0.0/16
  - asns: 51

AS5 announces:

    ====================== ============    ===========     ==========      ==========      =================  =================
    id                     prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected results 2
    ====================== ============    ===========     ==========      ==========      =================  =================
    AS5_pref_ok_origin_ok1 5.0.1.0/24      5               yes             yes             64512 64514        rejected
    AS5_pref_ko_origin_ok1 5.1.0.0/24      5               no              yes             rejected           rejected
    AS3_pref_ok_origin_ko3 5.0.2.0/24      5 3             yes             no              64512 64515        rejected
    AS3_pref_ko_origin_ko1 3.0.1.0/24      5 3             no              no              rejected           rejected
    AS5_pref_wl_origin_ok  5.2.1.0/24      5               yes (WL)        yes             64512 64514        64512 64515
    AS5_pref_wl_origin_ko  5.2.2.0/24      5 3             yes (WL)        no              64512 64515        the same
    AS5_pref_wl_origin_wl  5.2.3.0/24      5 51            yes (WL)        yes (WL)        64512 64514        the same
    AS5_pref_ko_origin_wl  5.3.1.0/24      5 51            no              yes (WL)        rejected           rejected
    AS5_pref_ok_origin_wl  5.0.3.0/24      5 51            yes             yes (WL)        64512 64514        rejected
    ====================== ============    ===========     ==========      ==========      =================  =================

AS6
---

- allowed objects:

  - prefix: 6.0.0.0/16
  - origin: 6, 3

configuration:

  - enforcing: both origin ASN and prefix
  - tagging: yes

- white lists:

  - routes:

    - 3.2.0.0/16+, AS3 (1)

AS6 announces:

    ====================== ============    ===========     ==========      ==========      =================  =================
    id                     prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected results 2
    ====================== ============    ===========     ==========      ==========      =================  =================
    AS2_roa1               2.4.0.0/16      6 2             no              no              rejected           rejected
    AS3_roa2               3.1.0.0/16      6 3             ROA             yes             64513 64514 64516  rejected
    AS3_arin1              3.2.1.0/24      6 3             ARIN (1)        yes             64513 64514 64518  64513 64515 64517
    AS3_roa3_arin2         3.3.0.0/16      6 3             no              yes             64513 64514 64516  rejected
                                                                                           64518
    AS6_ok_ok_roa6_arin6   6.0.1.0/24      6               yes             yes             64512 64514 64516  rejected
                                                                                           64518
    ====================== ============    ===========     ==========      ==========      =================  =================

1) The route white list is used to verify that:
- in scenario 1, 3.2.1.0/24 AS3 is accepted and tagged with the ARIN db community, and not because of the white list entry;
- in scenario 2, 3.2.1.0/24 AS3 is accepted anyway, but solely because of the route white list

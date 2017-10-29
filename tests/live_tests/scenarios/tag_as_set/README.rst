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

        route wht list  64517
        ==============  =====

AS2:

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

        ============    ===========     ==========      ==========      =================  =================
        prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected result 2
        ============    ===========     ==========      ==========      =================  =================
        2.0.1.0/24      2               yes             yes             64512 64514        64513 64515
        2.1.0.0/24      2               no              yes             64513 64514        64513 64515
        2.0.2.0/24      2 3             yes             no              64512 64515        64513 64515
        3.0.1.0/24      2 3             no              no              64513 64515        64513 64515
        2.2.1.0/24      2               yes (WL)        yes             64512 64514        64512 64515
        2.2.2.0/24      2 3             yes (WL)        no              64512 64515        the same
        2.2.3.0/24      2 21            yes (WL)        yes (WL)        64512 64514        the same
        2.3.1.0/24      2 21            no              yes (WL)        64513 64514        the same
        2.0.3.0/24      2 21            yes             yes (WL)        64512 64514        64513 64514
        ============    ===========     ==========      ==========      =================  =================

AS4:

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

        ============    ===========     ==========      ==========      =================  =================
        prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected result 2
        ============    ===========     ==========      ==========      =================  =================
        4.0.1.0/24      4               yes             yes             64512 64514        rejected
        4.1.0.0/24      4               no              yes             64513 64514        rejected
        4.0.2.0/24      4 3             yes             no              rejected           rejected
        3.0.1.0/24      4 3             no              no              rejected           rejected
        4.2.1.0/24      4               yes (WL)        yes             64512 64514        rejected
        4.2.2.0/24      4 3             yes (WL)        no              rejected           rejected
        4.2.3.0/24      4 41            yes (WL)        yes (WL)        64512 64514        the same
        4.3.1.0/24      4 41            no              yes (WL)        64513 64514        the same
        4.0.3.0/24      4 41            yes             yes (WL)        64512 64514        64513 64514
        4.4.0.0/16      4 44            r WL            r WL            64513 64515 64517  the same
        4.4.1.0/24      4 44            r WL KO         r WL            rejected           rejected
        4.5.1.0/24      4 43            r WL            r WL            64513 64515 64517  the same
        4.5.2.0/24      4 45            r WL            r WL KO         rejected           rejected
        4.6.1.0/24      4 45            r WL            r WL            64513 64515 64517  the same
        ============    ===========     ==========      ==========      =================  =================

AS5:

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

        ============    ===========     ==========      ==========      =================  =================
        prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected results 2
        ============    ===========     ==========      ==========      =================  =================
        5.0.1.0/24      5               yes             yes             64512 64514        rejected
        5.1.0.0/24      5               no              yes             rejected           rejected
        5.0.2.0/24      5 3             yes             no              64512 64515        rejected
        3.0.1.0/24      5 3             no              no              rejected           rejected
        5.2.1.0/24      5               yes (WL)        yes             64512 64514        64512 64515
        5.2.2.0/24      5 3             yes (WL)        no              64512 64515        the same
        5.2.3.0/24      5 51            yes (WL)        yes (WL)        64512 64514        the same
        5.3.1.0/24      5 51            no              yes (WL)        rejected           rejected
        5.0.3.0/24      5 51            yes             yes (WL)        64512 64514        rejected
        ============    ===========     ==========      ==========      =================  =================


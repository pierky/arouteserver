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
        ==============  =====

AS2:

- allowed objects:

  - prefix: 2.0.0.0/16
  - origin: [2]

- configuration:

  - enforcing: no
  - tagging: yes

AS2 announces:

        ============    ===========     ==========      ==========      =================  =================
        prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected result 2
        ============    ===========     ==========      ==========      =================  =================
        2.0.1.0/24      2               yes             yes             64512 64514        64513 64515
        2.1.0.0/24      2               no              yes             64513 64514        64513 64515
        2.0.2.0/24      2 3             yes             no              64512 64515        64513 64515
        3.0.1.0/24      2 3             no              no              64513 64515        64513 64515
        ============    ===========     ==========      ==========      =================  =================

AS4:

- allowed objects:

  - prefix: 4.0.0.0/16
  - origin: 4

- configuration:

  - enforcing: origin only
  - tagging: yes

AS4 announces:

        ============    ===========     ==========      ==========      =================  =================
        prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected result 2
        ============    ===========     ==========      ==========      =================  =================
        4.0.1.0/24      4               yes             yes             64512 64514        rejected
        4.1.0.0/24      4               no              yes             64513 64514        rejected
        4.0.2.0/24      4 3             yes             no              rejected           rejected
        3.0.1.0/24      4 3             no              no              rejected           rejected
        ============    ===========     ==========      ==========      =================  =================

AS5:

- allowed objects (AS-SET from PeeringDB):

  - prefix: 5.0.0.0/16
  - origin: 5

configuration:

  - enforcing: prefix only
  - tagging: yes

AS5 announces:

        ============    ===========     ==========      ==========      =================  =================
        prefix          AS_PATH         prefix ok?      origin ok?      expected result 1  expected results 2
        ============    ===========     ==========      ==========      =================  =================
        5.0.1.0/24      5               yes             yes             64512 64514        rejected
        5.1.0.0/24      5               no              yes             rejected           rejected
        5.0.2.0/24      5 3             yes             no              64512 64515        rejected
        3.0.1.0/24      5 3             no              no              rejected           rejected
        ============    ===========     ==========      ==========      =================  =================


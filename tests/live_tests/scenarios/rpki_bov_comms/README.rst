RPKI BGP Origin Validation and ASPA verification custom communities
*******************************************************************

This scenario uses the same BGP announcements of the ``rpki`` one. It's used to test the behaviour of the route servers when custom BGP communities are configured to keep track of the validation state of the routes when BOV and ASPA verification are performed.

Contrary to what is configured in the ``rpki`` scenario, no hooks are used here, and ``reject_invalid`` is alwasy False.

- Custom BOV state communities:

  ==============  =============
  Validity state  BGP community
  ==============  =============
  VALID           64512:1
  INVALID         64512:2
  UNKNOWN         64512:3
  ==============  =============

- Custom ASPA verification state communities:

  ======================  =============
  Verification state      BGP community
  ======================  =============
  VALID                   64512:4
  INVALID                 64512:5
  UNKNOWN                 64512:6
  ======================  =============

Please note: an AS_PATH that is one hop long has no hop to be verified, so its ASPA verification state is VALID; the "2 101" AS_PATHs are UNKNOWN, because no ASPA exists for AS101.

ASPA INVALID routes are never announced to the clients, even though ``reject_invalid`` is False.

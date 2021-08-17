RPKI BGP Origin Validation custom communities
*********************************************

This scenario uses the same BGP announcements of the ``rpki`` one. It's used to test the behaviour of the route servers when custom BGP communities are configured to keep track of the validation state of the routes when BOV is performed.

Contrary to what is configured in the ``rpki`` scenario, no hooks are used here, and ``reject_invalid`` is alwasy False.

- Custom BOV state communities:

  ==============  =============
  Validity state  BGP community
  ==============  =============
  VALID           64512:1
  INVALID         64512:2
  UNKNOWN         64512:3
  ==============  =============

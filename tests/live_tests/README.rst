Live tests
==========

Live tests are used to validate configurations built by ARouteServer and to test compliance between expected and real results.

A mix of Python unittest and Docker allows to create scenarios where some instances of BGP speakers (the clients) connect to a route server whose configuration has been generated using this tool.

Example: in a configuration where blackhole filtering is enabled, an instance of a route server client (AS1) is used to announce some tagged prefixes (203.0.113.1/32) and the instances representing other clients (AS2, AS3) are queried to ensure they receive those prefixes with the expected blackhole NEXT_HOP (192.0.2.66).

.. code:: python

  def test_071_blackholed_prefixes_as_seen_by_enabled_clients(self):
    for inst in (self.AS2, self.AS3):
      self.receive_route(inst, "203.0.113.1/32", self.rs,
                         next_hop="192.0.2.66",
                         std_comms=["65535:666"], lrg_comms=[])

`GitHub Actions log file <https://github.com/pierky/arouteserver/actions/workflows/tests.yml>`_ contains the latest built-in live tests results.
Since (AFAIK) OpenBGPD can't be run on GitHub Actions platform, the full live tests results including those run on OpenBGPD can be found on `this file <https://github.com/pierky/arouteserver/blob/master/tests/last>`_.

More details on the `Live tests <https://arouteserver.readthedocs.io/en/latest/LIVETESTS.html>`_ page on the official documentation.

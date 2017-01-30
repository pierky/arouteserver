Live tests
==========

Live tests are used to validate configurations built by ARouteServer.

A mix of Python's unittest and Docker allows to create scenarios where some instances of BGP speakers connect to a route server that has been configured using this program in order to test compliance between expected and real results.

Example: in a configuration where blackhole filtering is enabled, an instance of a route server client (AS1) is used to announce some tagged prefixes (203.0.113.1/32) and the instances representing other clients (AS2, AS3) are queried to ensure they receive those prefixes with the expected blackhole NEXT_HOP (192.0.2.66).

.. code:: python

  def test_071_blackholed_prefixes_as_seen_by_enabled_clients(self):
    for inst in (self.AS2, self.AS3):
      self.receive_route_from(inst, "203.0.113.1/32", self.rs,
                              next_hop="192.0.2.66",
                              std_comms=["65535:666"], lrg_comms=[])

Travis CI log file contains the latest live tests results: https://travis-ci.org/pierky/arouteserver/

How to run live tests
---------------------

#. Build the Docker image (or pull it from `Dockerhub <https://hub.docker.com/r/pierky/bird/>`_):

   .. code:: bash

      cd tests/live_tests/

      # build the image from the Dockerfile
      docker build -t pierky/bird:1.6.3 -f dockerfiles/Dockerfile.bird .

      # pull the image from Dockerhub
      docker pull pierky/bird:1.6.3

#. Run the Python testunit using ``nose``

   .. code:: bash

      nosetests -vs 

How it works
------------

Each directory in ``tests/live_tests/scenarios`` represents a scenario: the route server configuration is stored in the usual ``general.yml`` and ``clients.yml`` files, while other BGP speaker instances (route server clients and their peers) are configured through the ``ASxxx.j2`` files.
These files are Jinja2 templates and are expanded by the Python code at runtime. Containers' configuration files are saved in the local ``var`` directory and are used to mount the BGP speaker configuration file (currenly, ``/etc/bird/bird.conf``).
The unittest code sets up a Docker network (with name ``arouteserver``) used to attach instances and finally brings instances up. Regular unittest tests are now performed and can be used to match expectations to real results.

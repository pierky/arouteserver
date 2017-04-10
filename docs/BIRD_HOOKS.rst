BIRD hooks specifications
=========================

``pre_receive_from_client`` and ``post_receive_from_client``
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

- function name: ``hook_pre_receive_from_client`` / ``hook_post_receive_from_client``

- arguments:

  - ``int client_asn``: ASN of the client that announces the route to the route server.
  - ``ip client_ip``: IP address of the client that announces the route to the route server.
  - ``string client_id``: the client ID internally used by ARouteServer and BIRD.

- return value: ``true`` or ``false``

These functions are called within the filter that handles routes entering the route server from clients.
The *pre_* version is called as soon as the processing is started; the *post_* version is called just before the route is being accepted and after ARouteServer features and filters have been applied.
The return value determines whether the route is accepted (``true``) or rejected (``false``) by the route server.

``pre_announce_to_client`` and ``post_announce_to_client``
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

- function name: ``hook_pre_announce_to_client`` / ``hook_post_announce_to_client``

- arguments:

  - ``int client_asn``: ASN of the client that the route is announced to by the route server.
  - ``ip client_ip``: IP address of the client that the route is announced to by the route server.
  - ``string client_id``: the client ID internally used by ARouteServer and BIRD.

- return value: ``true`` or ``false``

These functions are called within the filter that handles routes leaving the route server toward its clients.
The *pre_* version is called as soon as the processing is started; the *post_* version is called just before the route is being announced and after ARouteServer features and filters have been applied.
The return value determines whether the route is announced (``true``) or not (``false``) by the route server to the client identified by the arguments.

``route_can_be_announced_to``
+++++++++++++++++++++++++++++

- function name: ``hook_route_can_be_announced_to``

- arguments:

  - ``int client_asn``: ASN of the client that the route is announced to by the route server.
  - ``ip client_ip``: IP address of the client that the route is announced to by the route server.
  - ``string client_id``: the client ID internally used by ARouteServer and BIRD.

- return value: ``true`` or ``false``

This function is called within the filter that handles routes leaving the route server toward its clients, more precisely when BGP control communities are processed to determine whether the route can be announced to a specific client.
The return value determines whether the route is announced (``true``) or not (``false``) by the route server to the client identified by the arguments.

``announce_rpki_invalid_to_client``
+++++++++++++++++++++++++++++++++++

- function name: ``hook_announce_rpki_invalid_to_client``

- arguments:

  - ``int client_asn``: ASN of the client that the route is announced to by the route server.
  - ``ip client_ip``: IP address of the client that the route is announced to by the route server.
  - ``string client_id``: the client ID internally used by ARouteServer and BIRD.

- return value: ``true`` or ``false``

This function is called when RPKI validation is enabled and an INVALID route is processed before being announced to a client.
The return value determines whether the RPKI INVALID route is announced (``true``) or not (``false``) by the route server to the client identified by the arguments.

``scrub_communities_in`` and ``scrub_communities_out``
++++++++++++++++++++++++++++++++++++++++++++++++++++++

- function name: ``hook_scrub_communities_in`` / ``hook_scrub_communities_out``

- arguments: none

- return value: none

These functions are called for route entering / leaving the route server; their purpose is only to remove/adjust any custom BGP community used by the route server.

``apply_blackhole_filtering_policy``
++++++++++++++++++++++++++++++++++++

- function name: ``hook_apply_blackhole_filtering_policy``

- arguments:

  - ``int ip_ver``: IP version (``4`` or ``6``)

- return value: none

This function is called when a blackhole filtering request is processed. It can be used to perform custom manipulation of the route before it is announced to clients.

#!/bin/bash

# A sort of deterministic number based on the IP address of the peer.
# To avoid that example configuration files change every time that
# documentation is built.
echo "$1" | md5sum | grep -Eo "[[:digit:]]{3}" | head -n1

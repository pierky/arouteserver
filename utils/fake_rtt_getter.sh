#!/bin/bash

# Determine the md5 program to use.
echo "test" | md5sum &>/dev/null
if [ $? -eq 0 ]; then
    MD5_PROGR="md5sum"
else
    MD5_PROGR="md5"
fi

# A sort of deterministic number based on the IP address of the peer.
# To avoid that example configuration files change every time that
# documentation is built.
echo "$1" | ${MD5_PROGR} | grep -Eo "[[:digit:]]" | tr -d '\n' | head --bytes 3

#!/bin/bash

# This script is the entry point of the Docker
# container used for the route server instance.

# Run the script that verifies when BIRD is
# configured and executes Alice-LG birdwatcher.
nohup /root/run_birdwatcher_when_ready.sh &

# Run BIRD - the route server daemon.
bird -c /etc/bird/bird.conf

# ARouteServer setup and configuration
# ------------------------------------

SETUP_AND_CONFIGURE_AROUTESERVER=${SETUP_AND_CONFIGURE_AROUTESERVER:-0}

# This part of the script can be skipped if the
# user desires to setup and configure ARouteServer
# manually.
#
# By setting SETUP_AND_CONFIGURE_AROUTESERVER=0
# in the docker-compose.yml file, ARouteServer
# will not be setup and configured, otherwise
# the options that are most suitable to this
# playground will be set by this script.
#
# If the content of this file is modified, for
# example to change the answers that are provided
# to the 'configure' command, please remember to
# rebuild the image via 'docker-compose build'.
#
# The setup and configure process can be monitored
# by attaching to the route server instance ('rs')
# and looking at the log file:
#
# $ docker-compose exec rs bash
# root@9ff51597be1b:~# tail -f /var/log/arouteserver_setup.log

if [ ${SETUP_AND_CONFIGURE_AROUTESERVER} -eq 1 ]; then
    LOG_FILE=/var/log/arouteserver_setup.log

    exec >${LOG_FILE} 2>&1

    echo "Running 'arouteserver setup'..."

    arouteserver \
        setup --dest-dir /etc/arouteserver

    echo "Running 'arouteserver configure'..."

    rm /etc/arouteserver/general.yml &>/dev/null

    arouteserver \
        configure --preset-answer \
            daemon=bird \
            version=1.6.8 \
            asn=64500 \
            router_id=10.0.0.2 \
            black_list=10.0.0.0/24

    rm /etc/arouteserver/clients.yml &>/dev/null

    cp /root/clients.yml /etc/arouteserver/clients.yml

    echo "Building BIRD configuration..."

    arouteserver \
        bird --ip-ver 4 -o /etc/bird/bird.conf

    echo "Reloading BIRD config... "
    birdc "configure"

    echo "ARouteServer setup and configure completed."
fi

sleep 365d

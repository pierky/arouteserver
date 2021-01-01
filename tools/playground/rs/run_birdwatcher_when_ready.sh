#!/bin/bash

# Wait until BIRD is up and some BGP sessions are
# configured, then run birdwatcher (needed by Alice-LG).

LOG_FILE=/var/log/birdwatcher.log

is_bird_ready=0

while [ $is_bird_ready -eq 0 ]
do
    echo "Waiting for BIRD to be ready... " >>${LOG_FILE}
    sleep 10

    birdc show protocols | grep BGP &>/dev/null

    if [ $? -eq 0 ]; then
        is_bird_ready=1
    fi
done

/root/go/bin/birdwatcher &>>/var/log/birdwatcher.log

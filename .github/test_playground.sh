#!/bin/bash

set -e

error=0

function pr_bold() {
    echo -e "\033[1m$@\033[0m"
}

function run_on() {
    set +e
    docker compose exec -T $1 bash -c "$2"

    if [ $? -eq 0 ]; then
        res="OK"
    else
        res="Failed"
        error=1
    fi

    set -e

    pr_bold "$1: $2 $res"
}

docker compose version

cd tools/playground

if [ "$CI" == "true" ]; then
    export INSTALL_FROM_SRC=1
fi

docker compose build

docker compose up -d

# Let run.sh configure ARouteServer...
echo -n "Waiting a bit till run.sh configures everything... "
sleep 60
echo "OK, let's move now!"

run_on rs 'birdc show protocols | grep BGP | grep Established | wc -l | grep 2'

run_on alice_lg 'curl -L http://10.0.0.2:29184/protocols/bgp'

run_on client_2 'birdc show route count | grep "2 of 2 routes for 2 networks"'
run_on client_2 'birdc show route | grep 193.0.0.0/21 | grep "via 10.0.0.11"'

# Valid routes on the RS.
run_on rs 'birdc show route count | grep "3 of 3 routes for 3 networks"'

for prefix in \
    192.136.136.0/24 \
    193.0.0.0/21 \
    193.0.22.0/23
do
    run_on rs "birdc show route $prefix | grep $prefix"
done

# Filtered routes on the RS.
run_on rs 'birdc show route filtered count | grep "4 of 4 routes for 4 networks"'

for prefix in \
    10.0.0.0/24 \
    192.168.0.0/24 \
    193.0.0.1/32 \
    202.12.29.0/24
do
    run_on rs "birdc show route filtered $prefix | grep $prefix"
done

run_on rs "birdc show route filtered 10.0.0.0/24 all | grep '(64500, 65520, 3)'"
run_on rs "birdc show route filtered 202.12.29.0/24 all | grep '(64500, 65520, 9)'"

pr_bold "Testing localhost, Alice at port 8080..."
curl -L http://127.0.0.1:8080 | grep 'Alice - The friendly BGP looking glass'
pr_bold "Testing localhost, Alice at port 8080... OK"

echo ""
echo ""

if [ $error -eq 0 ]; then
    pr_bold "Tests completed successfully!"
    exit 0
else:
    pr_bold "Tests failed :-("
    exit 1
fi

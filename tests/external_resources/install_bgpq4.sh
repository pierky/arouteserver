#!/bin/sh
set -ex
wget https://github.com/bgp/bgpq4/archive/refs/heads/main.zip -O bgpq4.zip
unzip bgpq4.zip
cd bgpq4-main
./bootstrap
./configure
make
sudo make install

#!/bin/sh
set -ex
wget https://github.com/bgp/bgpq4/archive/refs/tags/1.2.zip -O bgpq4.zip
unzip bgpq4.zip
cd bgpq4-1.2
./bootstrap
./configure
make
sudo make install

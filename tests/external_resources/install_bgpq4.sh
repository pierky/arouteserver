#!/bin/sh
set -ex
wget https://github.com/bgp/bgpq4/archive/master.zip -O bgpq4.zip
unzip bgpq4.zip
cd bgpq4-master
./bootstrap
./configure
make
sudo make install

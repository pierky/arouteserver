#!/bin/sh
set -ex
wget https://github.com/bgp/bgpq4/archive/master.zip
unzip master.zip
cd bgpq4-master
./bootstrap
./configure
make
sudo make install

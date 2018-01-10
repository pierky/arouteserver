#!/bin/sh
set -ex
wget https://github.com/snar/bgpq3/archive/master.zip
unzip master.zip
cd bgpq3-master
./configure
make
sudo make install

#!/bin/sh
set -ex
wget https://github.com/snar/bgpq3/archive/refs/heads/master.zip -O bgpq3.zip
unzip bgpq3.zip
cd bgpq3-master
./configure
make
sudo make install

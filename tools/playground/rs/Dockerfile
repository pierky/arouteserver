FROM pierky/bird:1.6.8

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get install \
        -y \
        --no-install-recommends \
            vim \
            git \
            build-essential \
            python3-pip \
            python3-dev && \
    rm -rf /var/lib/apt/lists/*

# ARouteServer dependencies: bgpq3
# --------------------------------

RUN mkdir /bgpq3 && \
    cd /bgpq3 && \
    git clone https://github.com/snar/bgpq3.git ./ && \
    ./configure && \
    make && \
    make install

# Installing ARouteServer
# -----------------------

RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install arouteserver

# Installing AliceLG birdwatcher
# ------------------------------

RUN curl \
    -OL https://golang.org/dl/go1.15.6.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.15.6.linux-amd64.tar.gz

ENV PATH=$PATH:/usr/local/go/bin

RUN go get github.com/alice-lg/birdwatcher

RUN mkdir -p /etc/birdwatcher

COPY birdwatcher.conf /etc/birdwatcher/birdwatcher.conf

# Environment setup
# -----------------

# This file is used to spin up BIRD when the
# container comes up. It's a very basic configuration,
# with no neighbors, only used to get the program up.
COPY bird.conf /etc/bird/bird.conf

# This file contains the ARouteServer clients definition
# used in this playground.
COPY clients.yml /root/clients.yml

# Startup script
# --------------

COPY run.sh /root/
COPY run_birdwatcher_when_ready.sh /root/

RUN chmod +x /root/*.sh

CMD /root/run.sh

FROM pierky/bird:2.17.1

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && \
    apt-get install \
        -y \
        --no-install-recommends \
            vim \
            git \
            build-essential \
            python3-pip \
            python3-dev \
            python3-venv \
            libtool && \
    rm -rf /var/lib/apt/lists/*

# Installing AliceLG birdwatcher
# ------------------------------

RUN curl \
    -OL https://golang.org/dl/go1.18.3.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.18.3.linux-amd64.tar.gz

ENV PATH=$PATH:/usr/local/go/bin

RUN go install github.com/alice-lg/birdwatcher@2.2.3

RUN mkdir -p /etc/birdwatcher

COPY birdwatcher.conf /etc/birdwatcher/birdwatcher.conf

# ARouteServer dependencies: bgpq3
# --------------------------------

RUN mkdir /bgpq4 && \
    cd /bgpq4 && \
    git clone https://github.com/bgp/bgpq4.git ./ && \
    ./bootstrap && \
    ./configure && \
    make && \
    make install

# Installing ARouteServer
# -----------------------

ARG INSTALL_FROM_GITHUB_SHA

RUN python3 -m venv .venv && \
    .venv/bin/pip install --upgrade pip setuptools wheel

# INSTALL_FROM_GITHUB_SHA is used by the
# test suite to perform the installation of
# ARouteServer from source. It can be ignored
# for the regular use of this playground.
RUN if [ -z "$INSTALL_FROM_GITHUB_SHA" ]; \
    then \
        .venv/bin/pip install arouteserver; \
    else \
        .venv/bin/pip install git+https://github.com/pierky/arouteserver.git@$INSTALL_FROM_GITHUB_SHA; \
    fi;

# Make the 'arouteserver' command from the virtualenv
# globally available.
RUN ln -s /root/.venv/bin/arouteserver /usr/local/bin/arouteserver

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

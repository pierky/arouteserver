ARG base_image="python:3.14"

# uv is only used at build time, to export the exact (hash-pinned) runtime
# dependencies from uv.lock: it's mounted when needed and it doesn't end
# up in the final image.
FROM ghcr.io/astral-sh/uv:0.12.19 AS uv

FROM ${base_image}

RUN mkdir /arouteserver
WORKDIR /arouteserver

RUN mkdir /bgpq4 && \
    cd /bgpq4 && \
    git clone https://github.com/bgp/bgpq4.git ./ && \
    git checkout tags/1.12 && \
    ./bootstrap && \
    ./configure && \
    make && \
    make install

RUN pip install --upgrade pip

# Dependencies are installed in their own layer, which is rebuilt only
# when the lock file changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=bind,from=uv,source=/uv,target=/usr/local/bin/uv \
    uv export --frozen --no-dev --no-emit-project -o /tmp/requirements.txt && \
    pip install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

COPY . ./
COPY docker/run.sh /root/run.sh
RUN pip install --no-deps .

RUN arouteserver \
    setup --dest-dir /etc/arouteserver

RUN rm /etc/arouteserver/clients.yml

CMD /root/run.sh

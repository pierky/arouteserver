FROM debian:oldstable

include(`base.m4')

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y \
	python3-pip

ENV python=python3
ENV pip=pip3

include(`install.m4')

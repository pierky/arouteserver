FROM debian:oldstable

include(`base.m4')

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y \
	python-pip \
	python-dev

include(`install.m4')

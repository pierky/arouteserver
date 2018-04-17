FROM debian:stable

include(`base.m4')

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y \
	python-pip

include(`install.m4')

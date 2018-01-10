FROM ubuntu:trusty

include(`base.m4')

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y \
	python3-pip \
	python3-dev

ENV python=python3
ENV pip=pip3

RUN pip3 install --upgrade setuptools

include(`install.m4')

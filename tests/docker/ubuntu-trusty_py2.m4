FROM ubuntu:trusty

include(`base.m4')

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y \
	python-pip \
	python-dev

RUN pip install --upgrade setuptools

include(`install.m4')

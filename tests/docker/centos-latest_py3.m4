FROM centos:latest

include(`base.m4')

RUN yum -y update && yum -y install epel-release
RUN yum -y update && yum -y install \
	python3-pip \
	python3-devel \
	gcc

ENV python=python3
ENV pip=pip3

include(`install.m4')

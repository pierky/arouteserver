FROM centos:latest

include(`base.m4')

RUN yum -y update && yum -y install epel-release
RUN yum -y update && yum -y install \
	python-pip \
	python-devel \
	gcc

include(`install.m4')

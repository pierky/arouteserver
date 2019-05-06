FROM ubuntu:latest

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y \
    ruby-full \
    libffi-dev \
    make \
    build-essential \
    git

RUN gem install travis

RUN echo 'Usage: docker run -v $(pwd):/repo -it pierky/travis_ci bash'
RUN echo '       cd repo'
RUN echo '       travis login'
RUN echo '       travis encrypt-file ars_cicd_travis'

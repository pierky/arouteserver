COPY arouteserver.tar.gz /root/arouteserver.tar.gz

RUN $pip -V
RUN $python -V

RUN $pip install virtualenv

SHELL ["/bin/bash", "-c"]

RUN mkdir -p ~/.virtualenvs/arouteserver && \
	virtualenv ~/.virtualenvs/arouteserver && \
	source ~/.virtualenvs/arouteserver/bin/activate && \
	$pip install /root/arouteserver.tar.gz

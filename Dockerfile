
FROM python:3.8

WORKDIR /migration

COPY utils /migration/utils
COPY parser /migration/obtainer
COPY modifier /migration/modifier

COPY migrate.py /migration/
COPY setup.py /migration/

ENV PYTHONPATH=/usr/local/bin/python:/migrate/:.

RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y vim

RUN python setup.py install

ENTRYPOINT [ "/bin/bash" ]

FROM python:3.8

WORKDIR /migration

COPY utils /migration/
COPY migrate.py /migration/

RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install build-essential libcap-dev

ENTRYPOINT [ "/bin/bash" ]
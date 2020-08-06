FROM python:3.8-alpine
ENV PYTHONUNBUFFERED 1
ENV MIGRATE_DIR /migrate
RUN apk --update --no-cache add git bash
RUN mkdir /code ; mkdir /code/journeys ; mkdir /migrate
COPY requirements.txt /code/
RUN apk --update --no-cache --virtual .build add gcc make musl-dev libffi-dev openssl-dev && \
  pip install -U pip ; pip install -r /code/requirements.txt && \
  apk del .build
COPY ./journeys /code/journeys/
COPY ./journey.py ./entrypoint.sh /code/
RUN ln -s /code/journey.py /usr/local/bin/
ENTRYPOINT ["/code/entrypoint.sh"]

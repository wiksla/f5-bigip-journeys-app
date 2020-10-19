FROM python:3.8-alpine
ENV PYTHONUNBUFFERED 1
ENV MIGRATE_DIR /migrate
RUN apk --update --no-cache add git bash gnupg
RUN mkdir /code ; mkdir /code/journeys ; mkdir /migrate
COPY requirements.txt /code/
RUN apk --update --no-cache --virtual .build add gcc make musl-dev libffi-dev openssl-dev && \
  pip install -U pip ; pip install -r /code/requirements.txt && \
  apk del .build

COPY ./journeys /code/journeys/
COPY ./journey ./entrypoint.sh ./manage.py /code/

RUN ln -s /code/journey /usr/local/bin/
RUN ln -s /code/manage.py /usr/local/bin/
RUN echo 'eval "$(_JOURNEY_COMPLETE=source_bash journey)"' >> /root/.bashrc

ENV DJANGO_SETTINGS_MODULE journeys.backend.settings
ENV PYTHON_PATH /code
EXPOSE 8000/tcp
ENTRYPOINT ["/code/entrypoint.sh"]

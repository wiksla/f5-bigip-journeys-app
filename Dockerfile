FROM python:3.8-alpine
ENV PYTHONUNBUFFERED 1
ENV MIGRATE_DIR /migrate
RUN apk --update --no-cache add git bash gnupg openssl
RUN apk --update --no-cache add git bash gnupg openssl wkhtmltopdf xvfb ttf-dejavu
RUN mkdir /code ; mkdir /code/journeys ; mkdir /migrate
COPY requirements.txt /code/
RUN apk --update --no-cache --virtual .build add gcc make musl-dev libffi-dev openssl-dev && \
  pip install -U pip ; pip install -r /code/requirements.txt && \
  apk del .build

COPY ./journeys /code/journeys/
COPY ./journey ./entrypoint.sh ./manage.py /code/
RUN ln -s /code/journey /usr/local/bin/ && \
    echo 'eval "$(_JOURNEY_COMPLETE=source_bash journey)"' >> /root/.bashrc && \
    /code/manage.py makemigrations backend && \
    /code/manage.py migrate
ENV PYTHONPATH /code
ENTRYPOINT ["/code/entrypoint.sh"]

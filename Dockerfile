FROM python:3.8-alpine
ENV PYTHONUNBUFFERED 1
RUN apk --update --no-cache add git
RUN mkdir /code ; mkdir /code/journeys ; mkdir /migrate
COPY requirements.txt /code/
WORKDIR /code
RUN apk --update --no-cache --virtual .build add gcc make musl-dev libffi-dev openssl-dev && \
  pip install -U pip ; pip install -r requirements.txt && \
  apk del .build
COPY ./journeys /code/journeys/
COPY ./migrate.py /code/
ENV PATH /code:$PATH
WORKDIR /migrate
ENTRYPOINT ["migrate.py"]

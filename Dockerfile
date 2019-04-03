FROM python:alpine3.7
WORKDIR /app
COPY . /app
RUN apk add --no-cache --virtual .build-deps mariadb-dev gcc musl-dev \
    && apk add --virtual .runtime-deps mariadb-client-libs \
    && pip install --upgrade pip \
    && pip install -r requirements.txt \
    && apk del .build-deps

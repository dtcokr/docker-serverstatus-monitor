FROM alpine:3.15.0

RUN apk add --update --no-cache py3-pip libc-dev gcc python3-dev
RUN mkdir -p /ServerStatus/json /ServerStatus/log
RUN python3 -m pip install --no-cache-dir python-telegram-bot
RUN apk del libc-dev gcc

COPY ./server-monitor.py /ServerStatus/server-monitor.py

WORKDIR /ServerStatus

ENTRYPOINT python3 -u /ServerStatus/server-monitor.py

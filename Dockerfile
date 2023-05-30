FROM alpine:3.15.0

RUN apk add --update --no-cache python3 py3-requests && \
    mkdir -p /ServerStatus/json /ServerStatus/log

COPY ./server-monitor.py /ServerStatus/server-monitor.py

WORKDIR /ServerStatus

ENTRYPOINT python3 -u /ServerStatus/server-monitor.py

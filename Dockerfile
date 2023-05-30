FROM python:3.9-slim-buster

RUN pip install requests && \
    mkdir -p /ServerStatus/json /ServerStatus/log

COPY server-monitor.py /ServerStatus/

WORKDIR /ServerStatus

ENTRYPOINT ["python3", "-u", "server-monitor.py"]

# docker-serverstatus-monitor

![Docker Image Size (tag)](https://img.shields.io/docker/image-size/dtcokr/serverstatus-monitor/latest)
![Docker Pulls](https://img.shields.io/docker/pulls/dtcokr/serverstatus-monitor)
![GitHub last commit](https://img.shields.io/github/last-commit/dtcokr/docker-serverstatus-monitor)

A monitor works with [ServerStatus](https://github.com/cppla/ServerStatus), using Telegram as notifier.

[中文](https://github.com/dtcokr/docker-serverstatus-monitor/blob/main/README_EN.md) | EN

## Usage

`docker run -v /path/to/json:/ServerStatus/json -v /path/to/log:/ServerStatus/log dtcokr/serverstatus-monitor`

## Volumes

`/path/to/json:/ServerStatus/json` --- directory where `stats.json` sits, for reading data
`/path/to/log:/ServerStatus/log` --- directory where `server-monitor.log` sits, for logging and debugging

## Docker Envs

`BOT_TOKEN` --- Telegram bot token, go to **Bot Father**
`ACC_ID` --- a Telegram user account, where notifications are pushed
`MON_INTRVL` --- how often the monitor reads data, **10 seconds by default**
`PL_THRES` --- packet loss notification threshold, **90% by default**
`PL_CM` --- weight of CM packet loss

To be continued..

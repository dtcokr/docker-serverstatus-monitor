# docker-serverstatus-monitor

![Docker Image Size (tag)](https://img.shields.io/docker/image-size/dtcokr/serverstatus-monitor/latest)
![Docker Pulls](https://img.shields.io/docker/pulls/dtcokr/serverstatus-monitor)
![GitHub last commit](https://img.shields.io/github/last-commit/dtcokr/docker-serverstatus-monitor)

- 与 [ServerStatus](https://github.com/cppla/ServerStatus) 一同工作的服务器监视器，部署在 Server 端，并将告警推送至 Telegram。
- 可监控的指标：
  - 在线状态
  - 系统负载
  - 磁盘使用率
  - 三网（CU、CT、CM）各自丢包率
  - 是否被屏蔽
  - TCP 连接数

中文 | [EN](https://github.com/dtcokr/docker-serverstatus-monitor/blob/main/README_EN.md)

## 使用

文件夹结构

```
/path/to/ServerStatus
.
├── json
│   └── stats.json
├── log
│   └── server-monitor.log
└── server
    └── config.json
```

### CLI

```bash
$ docker run \
    -v /path/to/json:/ServerStatus/json \
    -v /path/to/log:/ServerStatus/log \
    -v /path/to/server:/ServerStatus/server \
    -v /etc/localtime:/etc/localtime:ro \
    dtcokr/serverstatus-monitor
```

### docker-compose

```yaml
services:
    serstatmon:
        image: dtcokr/serverstatus-monitor
        container_name: serstatmon
        restart: always
        volumes:
            - /path/to/json:/ServerStatus/json
            - /path/to/log:/ServerStatus/log
            - /path/to/server:/ServerStatus/server
            - /etc/localtime:/etc/localtime:ro
        environment:
            - BOT_TOKEN=
            - ACC_ID=
            - SL_THRES=
            - DU_THRES

```

## 挂载卷

- `/path/to/json:/ServerStatus/json` --- `stats.json` 所在的目录，数据的来源
- `/path/to/log:/ServerStatus/log` --- `server-monitor.log` 所在的目录，日志的归宿
- `/path/to/server:/ServerStatus/server` --- `config.json` 所在的目录，独立控制（*详见下方）的设置位置
- `/etc/localtime:/etc/localtime:ro` --- 将日志的时区设定为系统的时区

## Docker 环境变量

### 基本信息

- `BOT_TOKEN` --- **必填** - Telegram Bot 令牌，去找 _Bot Father_ 要
- `ACC_ID` --- **必填** - 你用于接收告警的 Telegram 用户 ID，很多 Bot 可以获取
- `SERVER_ID` --- 可选 - 该服务器的名字，可用于区分多台监控服务器
- `MON_INTRVL` --- 可选 - 每次读取数据的时间间隔，**默认 60 秒**

### 丢包率

- `PL_CM` --- 可选 - CM 网络丢包率，**默认 30**（指30%）
- `PL_CT` --- 可选 - CT 网络丢包率，**默认 30**（指30%）
- `PL_CU` --- 可选 - CU 网络丢包率，**默认 30**（指30%）

### 系统资源

- `SL_THRES` --- **必填** - 系统负载阈值，以 **15 分钟均值（load_15）** 为准
- `DU_THRES` --- 可选 - 磁盘使用率阈值，百分比，_如：_ `DU_THRES=85` 指 `85%`，**默认 90**
- `TCP_THRES` --- 可选 - TCP 连接数阈值，**默认 300**

### 告警阈值

- `BN_THRES` --- 可选 - 发出被屏蔽告警前需要被记录的次数，**默认 6**
- `BCUN_THRES` --- 可选 - 发出 CU 高丢包率告警前需要被记录的次数，**默认 6**
- `BCTN_THRES` --- 可选 - 发出 CT 高丢包率告警前需要被记录的次数，**默认 6**
- `BCMN_THRES` --- 可选 - 发出 CM 高丢包率告警前需要被记录的次数，**默认 6**
- `LN_THRES` --- 可选 - 发出高负载告警前需要被记录的次数，**默认 6**
- `ON_THRES` --- 可选 - 发出离线告警前需要被记录的次数，**默认 6**
- `DN_THRES` --- 可选 - 发出磁盘使用率告警前需要被记录的次数，**默认 6**
- `TN_THRES` --- 可选 - 发出 TCP 连接数告警前需要被记录的次数，**默认 6**
- `LOG_LVL` --- 可选 - 日志级别，**默认 INFO**，可选`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `LANG_UAGE` --- 可选 - 语言版本，**默认 ZH 中文**，可选`EN`(English)

## 独立控制

在 `ServerStatus/server/config.json` 文件中的 `host` 字段中可单独设置各服务器的告警阈值，目前支持的设置项：

- `PL_CM` --- CM 网络丢包率
- `PL_CT` --- CT 网络丢包率
- `PL_CU` --- CU 网络丢包率
- `SL_THRES` --- 系统负载告警阈值，以 **15 分钟均值（15 min load average）** 为准
- `DU_THRES` --- 磁盘使用率告警阈值，百分比数值
- `TCP_THRES` --- TCP 连接数阈值

格式：

`设置项+数值`，多个设置项用逗号(`,`)分隔

需要挂载的文件夹：

`/path/to/server:/ServerStatus/server`

示例设置：

```json
{
    "servers":
    [
        {
            "username": "name1",
            "name": "server1",
            "type": "na",
            "host": "PL_THRES70,PL_CM1.2,PL_CT1.2,PL_CU0.6,SL_THRES10,DU_THRES85,TCP_THRES100", #在这里设置，多个设置项用逗号(,)分隔
            "location": "na",
            "password": "passwd1"
        }
    ]
}
```


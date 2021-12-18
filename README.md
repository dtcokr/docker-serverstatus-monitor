# docker-serverstatus-monitor

![Docker Image Size (tag)](https://img.shields.io/docker/image-size/dtcokr/serverstatus-monitor/latest)
![Docker Pulls](https://img.shields.io/docker/pulls/dtcokr/serverstatus-monitor)
![GitHub last commit](https://img.shields.io/github/last-commit/dtcokr/docker-serverstatus-monitor)

与 [ServerStatus](https://github.com/cppla/ServerStatus) 一同工作的服务器监视器，部署在 Server 端，并将告警推送至 Telegram。

中文 | [EN](https://github.com/dtcokr/docker-serverstatus-monitor/README_EN.md)

## 使用

`docker run -v /path/to/json:/ServerStatus/json -v /path/to/log:/ServerStatus/log dtcokr/serverstatus-monitor`

## 挂载卷

`/path/to/json:/ServerStatus/json` --- `stats.json` 所在的目录，数据的来源
`/path/to/log:/ServerStatus/log` --- `server-monitor.log` 所在的目录，日志的归宿

## Docker 环境变量

`BOT_TOKEN` - **必填** - Telegram Bot 令牌，去找 _Bot Father_ 要
`ACC_ID` - **必填** - 你用于接收告警的 Telegram 用户 ID，很多 Bot 可以获取
`MON_INTRVL` - 可选 - 读取数据的间隔时间，**默认 10 秒**
`PL_THRES` - 可选 - 三网总计丢包率告警阈值，**默认 90%，即 30% 各网**，与三网**权重**共同作用，详见下方规则
`PL_CM` - 可选 - CM 网络丢包率权重，**默认 1.0**
`PL_CT` - 可选 - CT 网络丢包率权重，**默认 1.0**
`PL_CU` - 可选 - CU 网络丢包率权重，**默认 1.0**
`SL_THRES` - **必填** - 系统负载告警阈值，以 **15 分钟均值（15 min load average）** 为准
`DU_THRES` - **必填** - 磁盘使用率告警阈值，百分数值，_如：_ `DU_THRES=85` 为 85% 时告警
`BN_THRES` - 可选 - 发出高丢包率告警前需要被记录的次数，**默认 6**
`LN_THRES` - 可选 - 发出高负载告警前需要被记录的次数，**默认 6**
`ON_THRES` - 可选 - 发出离线告警前需要被记录的次数，**默认 6**
`LOG_LVL` - 可选 - 日志级别，**默认 INFO**，可选`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
`LANG_UAGE` - 可选 - 语言版本，**默认 ZH 中文**，可选`ZH`, `EN`(English)

### `PL_CM`, `PL_CT`, `PL_CU` 权重以及 `PL_THRES` 阈值

提供给对单一网络或其二网络或三网有不同优先级的需求的用户使用。比如你是 CT 用户，可提高 `PL_CT` 的权重，使监控更契合使用场景。

#### 规则

1. `PL_CM` + `PL_CT` + `PL_CU` = 3.0
2. 只要设定其中**任意至少一项**，则**三项都必须要设定**
3. `PL_THRES` 小于 **300** 时才有意义

## todo

- 引入配置文件，独立调整各监控对象的指标
- 优化代码


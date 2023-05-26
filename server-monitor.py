# !/usr/bin/env python3
# coding=utf-8

import json
import time
import requests
import logging
import os
import signal
import re


## preferences
bot_token = os.getenv('BOT_TOKEN') # telegram bot token
account_id = int(os.getenv('ACC_ID')) # telegram id
server_id = os.getenv('SERVER_ID', '').replace('_', '\_') # server identification in case you have multiple servers

monitor_interval = int(os.getenv('MON_INTRVL', 60)) # in seconds

packet_loss_weight_cm = float(os.getenv('PL_CM', 30.0)) # weight of CM packet loss
packet_loss_weight_ct = float(os.getenv('PL_CT', 30.0)) # weight of CT packet loss
packet_loss_weight_cu = float(os.getenv('PL_CU', 30.0)) # weight of CU packet loss

tcp_threshold = float(os.getenv('TCP_THRES', 300.0)) # tcp count
load_threshold = float(os.getenv('SL_THRES')) # 15 min load
disk_threshold = float(os.getenv('DU_THRES')) # % of disk usage

block_notify_threshold = int(os.getenv('BN_THRES', 6)) # how many times the server name appears in blocked list
badcu_notify_threshold = int(os.getenv('BCUN_THRES', 6)) # how many times the server name appears in badcu list
badct_notify_threshold = int(os.getenv('BCTN_THRES', 6)) # how many times the server name appears in badct list
badcm_notify_threshold = int(os.getenv('BCMN_THRES', 6)) # how many times the server name appears in badcm list
load_notify_threshold = int(os.getenv('LN_THRES', 6)) # how many times the server name appears in heavy load list
offline_notify_threshold = int(os.getenv('ON_THRES', 6)) # how many times the server name appears offline in list
diskfull_notify_threshold = int(os.getenv('DN_THRES', 6)) # how many times the server name appears disk usage in list
tcpcount_notify_threshold = int(os.getenv('TN_THRES', 6)) # how many times the server name appears tcp count in list
logging.debug(type(block_notify_threshold))
logging.debug(type(badcu_notify_threshold))
logging.debug(type(badct_notify_threshold))
logging.debug(type(badcm_notify_threshold))
logging.debug(type(load_notify_threshold))
logging.debug(type(offline_notify_threshold))
logging.debug(type(diskfull_notify_threshold))
logging.debug(type(tcpcount_notify_threshold))

log_level = os.getenv('LOG_LVL', 'ERROR').upper() # log level

lang_uage = os.getenv('LANG_UAGE', 'ZH') # language

stats_json = '/ServerStatus/json/stats.json' # stats.json from server status
log_file = '/ServerStatus/log/server-monitor.log' # log file location
configJson = '/ServerStatus/server/config.json' # server config.json file location
stash_json = '/ServerStatus/json/interrupt.json' # stash current lists when monitor is killed

logging.basicConfig(filename=log_file, 
                    level=log_level, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


## check if stash exist
if os.path.isfile(stash_json):
    with open(stash_json, 'r') as f_read:
        j2dict = json.load(f_read)
    
    offline = j2dict.get('offline', [])
    blocked = j2dict.get('blocked', [])
    highload = j2dict.get('highload', [])
    diskfull = j2dict.get('diskfull', [])
    tcptoomany = j2dict.get('tcptoomany', [])
    badcu = j2dict.get('badcu', [])
    badct = j2dict.get('badct', [])
    badcm = j2dict.get('badcm', [])

    olnotify = j2dict.get('olnotify', [])
    bknotify = j2dict.get('bknotify', [])
    hlnotify = j2dict.get('hlnotify', [])
    dfnotify = j2dict.get('dfnotify', [])
    tcpnotify = j2dict.get('tcpnotify', [])
    badcunotify = j2dict.get('badcunotify', [])
    badctnotify = j2dict.get('badctnotify', [])
    badcmnotify = j2dict.get('badcmnotify', [])

    os.remove(stash_json)
else:
    offline = []
    blocked = []
    highload = []
    diskfull = []
    tcptoomany = []
    badcu = []
    badct = []
    badcm = []
    
    olnotify = []
    bknotify = []
    hlnotify = []
    dfnotify = []
    tcpnotify = []
    badcunotify = []
    badctnotify = []
    badcmnotify = []


## function to stash lists
def _stash(l2file):
    jdict = {}
    
    jdict['offline'] = offline
    jdict['blocked'] = blocked
    jdict['highload'] = highload
    jdict['diskfull'] = diskfull
    jdict['tcptoomany'] = tcptoomany
    jdict['badcu'] = badcu
    jdict['badct'] = badct
    jdict['badcm'] = badcm

    jdict['olnotify'] = olnotify
    jdict['bknotify'] = bknotify
    jdict['hlnotify'] = hlnotify
    jdict['dfnotify'] = dfnotify
    jdict['tcpnotify'] = tcpnotify
    jdict['badcunotify'] = badcunotify
    jdict['badctnotify'] = badctnotify
    jdict['badcmnotify'] = badcmnotify
    
    with open(l2file, 'w') as f_write:
        json.dump(jdict, f_write, indent=4)
        logging.info('Lists stashed to interrupt.json.')

## function to receive docker signal
def _handle_sigterm(*args):
    raise KeyboardInterrupt()

signal.signal(signal.SIGTERM, _handle_sigterm)

## function to call Telegram API
def _tgapi_call(text):
    tgapi_url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {'chat_id': account_id, 'text': text, 'parse_mode': 'Markdown'}
    for _ in range(20):
        try:
            requests.get(tgapi_url, params=payload)
        except Exception as e:
            if lang_uage == 'EN':
                logging.error(f'{e}\nretrying..')
            elif lang_uage == 'ZH':
                logging.error(f'{e}\n正在重试..')
        else:
            break

## function to read default/custom threshold
def _readThreshold(configJson):
    with open(configJson, 'r') as statsJsonRead:
        stats2Dict = json.load(statsJsonRead)
    
    thresholdDict = {}
    pl_cmPattern = r'PL_CM(\d\.?\d*)'
    pl_ctPattern = r'PL_CT(\d\.?\d*)'
    pl_cuPattern = r'PL_CU(\d\.?\d*)'
    sl_thresPattern = r'SL_THRES(\d\.?\d*)'
    du_thresPattern = r'DU_THRES(\d\.?\d*)'
    tcp_thresPattern = r'TCP_THRES(\d\.?\d*)'
    
    for server in stats2Dict['servers']:
        
        serverName = server['name']
        serverHost = server['host']
            
        pl_cmMatch = re.search(pl_cmPattern, serverHost)
        if pl_cmMatch:
            pl_cm = float(pl_cmMatch.group(1))
        else:
            pl_cm = packet_loss_weight_cm
            
        pl_ctMatch = re.search(pl_ctPattern, serverHost)
        if pl_ctMatch:
            pl_ct = float(pl_ctMatch.group(1))
        else:
            pl_ct = packet_loss_weight_ct

        pl_cuMatch = re.search(pl_cuPattern, serverHost)
        if pl_cuMatch:
            pl_cu = float(pl_cuMatch.group(1))
        else:
            pl_cu = packet_loss_weight_cu

        sl_thresMatch = re.search(sl_thresPattern, serverHost)
        if sl_thresMatch:
            sl_thres = float(sl_thresMatch.group(1))
        else:
            sl_thres = load_threshold

        du_thresMatch = re.search(du_thresPattern, serverHost)
        if du_thresMatch:
            du_thres = float(du_thresMatch.group(1))
        else:
            du_thres = disk_threshold

        tcp_thresMatch = re.search(tcp_thresPattern, serverHost)
        if tcp_thresMatch:
            tcp_thres = float(tcp_thresMatch.group(1))
        else:
            tcp_thres = tcp_threshold
            
        thresholdDict[serverName] = {"PL_CM": pl_cm, "PL_CT": pl_ct, "PL_CU": pl_cu, "SL_THRES": sl_thres, "DU_THRES": du_thres, "TCP_THRES": tcp_thres}
    
    logging.debug(f'thresholdDict: {thresholdDict}')
    logging.debug(f'stats2Dict: {stats2Dict}')
    return thresholdDict

## monitor loop starts here
logging.info('Server monitor started.')
thresholdDict = _readThreshold(configJson)
if lang_uage == 'EN':
    text = f'#ServerStatus {server_id}\nServer monitor started.'
    _tgapi_call(text)
elif lang_uage == 'ZH':
    text = f'#ServerStatus {server_id}\n服务器监视器已启动。'
    _tgapi_call(text)

while True:
    try:
        ## status gathering
        with open(stats_json, 'r', encoding='utf-8') as f:
            js = json.load(f)
        logging.debug(js)
        for server in js['servers']:
            serverName = server['name']
            ## ipv4 and/or ipv6 online is considered online
            isonline = server['online4'] or server['online6']
            ## if server is offline(any other data is N/A) and not reach notify threshold, add it to offline list and finish loop
            if (isonline is False) and (offline.count(serverName) > offline_notify_threshold):
                offline.append(serverName)
                logging.info(f"Add offline server: {serverName}")

            ## if server is online, other data is available
            elif isonline is True:
                ## isfree is True means server is not blocked by CU and CT and CM
                ## isGood is True means server successful ping to CU, CT, CM is good
                isfree = (server['ping_10010'] + server['ping_189'] + server['ping_10086']) > 300.0
                ## using 15-min-avg load as current load reading
                load = server['load_15']
                isgoodload = load > thresholdDict[serverName]['SL_THRES']
                logging.debug(type(thresholdDict[serverName]['SL_THRES']))
                isgooddisk = server['hdd_used'] / (server['hdd_total'] if server['hdd_total'] != 0 else 1e16) < thresholdDict[serverName]['DU_THRES']/100.0
                isgoodtcp = server['tcp_count'] < thresholdDict[serverName]['TCP_THRES']
                isgoodcu = server['ping_10010'] < thresholdDict[serverName]['PL_CU']
                isgoodct = server['ping_189'] < thresholdDict[serverName]['PL_CT']
                isgoodcm = server['ping_10086'] < thresholdDict[serverName]['PL_CM']
                
                ## if server is previously offline and now online, remove it from offline list
                if serverName in offline:
                    offline.remove(serverName)
                    logging.info(f"Remove offline server: {serverName}")
                
                ## if server load >= threshold and not reach notify threshold, add it to highload list
                if (not isgoodload) and (highload.count(serverName) < load_notify_threshold):
                    highload.append(serverName)
                    logging.info(f"Add high load server: {serverName}, load {load}")
                ## else if server load < threshold and previously in highload list, remove it
                elif isgoodload and (serverName in highload):
                    highload.remove(serverName)
                    logging.info(f"Remove high load server: {serverName}, load {load}")
                
                ## if server is blocked and not reach notify threshold, add it to blocked list
                if (not isfree) and (blocked.count(serverName) < block_notify_threshold):
                    blocked.append(serverName)
                    logging.info(f"Add blocked server: {serverName}")
                ## else if server is unblocked and previously in blocked list, remove it
                elif isfree and (serverName in blocked):
                    blocked.remove(serverName)
                    logging.info(f"Remove blocked server: {serverName}")
                    
                ## if server disk usage >= threshold and not reach notify threshold, add it to diskfull list
                if (not isgooddisk) and (diskfull.count(serverName < diskfull_notify_threshold)):
                    diskfull.append(serverName)
                    logging.info(f"Add disk full server: {serverName}")
                ## else if server is not disk full and previously in diskfull list, remove it
                elif isgooddisk and (serverName in diskfull):
                    diskfull.remove(serverName)
                    logging.info(f"Remove disk full server: {serverName}")
                
                ## if server tcp count >= threshold and not reach notify threshold, add it to tcptoomany list
                if (not isgoodtcp) and (tcptoomany.count(serverName) < tcpcount_notify_threshold):
                    tcptoomany.append(serverName)
                    logging.info(f"Add tcptoomany server: {serverName}")
                ## else if server is not too many tcp and previously in toomanytcp list, remove it
                elif isgoodtcp and (serverName in tcptoomany):
                    tcptoomany.remove(serverName)
                    logging.info(f"Remove tcptoomany server: {serverName}")
                
                ## if server successful ping to CU >= threshold and not reach notify threshold, add it to badcu list
                if (not isgoodcu) and (badcu.count(serverName) < badcu_notify_threshold):
                    badcu.append(serverName)
                    logging.info(f"Add bad cu server: {serverName}")
                ## else if server is not bad cu and previously in badcu list, remove it
                elif isgoodcu and (serverName in badcu):
                    badcu.remove(serverName)
                    logging.info(f"Remove bad cu server: {serverName}")
                
                ## if server successful ping to CT >= threshold and not reach notify threshold, add it to badct list
                if (not isgoodct) and (badct.count(serverName) < badct_notify_threshold):
                    badct.append(serverName)
                    logging.info(f"Add bad ct server: {serverName}")
                ## else if server is not bad ct and previously in badct list, remove it
                elif isgoodct and (serverName in badct):
                    badct.remove(serverName)
                    logging.info(f"Remove bad ct server: {serverName}")
                
                ## if server successful ping to CM >= threshold and not reach notify threshold, add it to badcm list
                if (not isgoodcm) and (badcm.count(serverName) < badcm_notify_threshold):
                    badcm.append(serverName)
                    logging.info(f"Add bad cm server: {serverName}")
                ## else if server is not bad cm and previously in badcm list, remove it
                elif isgoodcm and (serverName in badcm):
                    badcm.remove(serverName)
                    logging.info(f"Remove bad cm server: {serverName}")

        ## notification
        for server in js['servers']:
            ## if server reaches offline notify threshold and not notified yet, notify and add it to notified list
            if (offline.count(serverName) >= offline_notify_threshold) and (serverName not in olnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} *OFFLINE*."
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} *已离线*."
                    _tgapi_call(text)
                olnotify.append(serverName)
                logging.info(f"Server offline notified: {serverName}")
            ## else if server is online and previously notified because of offline, notify and remove it from offline notify list
            elif (serverName not in offline) and (serverName in olnotify):
                olnotify = list(filter((serverName).__ne__, olnotify))
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} *ONLINE*."
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} *已恢复在线*."
                    _tgapi_call(text)
                logging.info(f"Server online notified: {serverName}")

            ## if server reaches highload notify threshold and not notified yet, notify and add it to notified list
            if (highload.count(serverName) >= load_notify_threshold) and (serverName not in hlnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} *HEAVY load*.\n1,5,15 min load: {server['load_1']}, {server['load_5']}, {server['load_15']}"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} *系统负载较高*.\n1,5,15 min load: {server['load_1']}, {server['load_5']}, {server['load_15']}"
                    _tgapi_call(text)
                hlnotify.append(serverName)
                logging.info(f"Highload server notified: {serverName}")
            ## else if server is normal load and previously notified because of highload, notify and remove it from offline notify list
            elif (serverName not in highload) and (serverName in hlnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} *NORMAL load*.\n1,5,15 min load: {server['load_1']}, {server['load_5']}, {server['load_15']}"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} *系统负载恢复正常*.\n1,5,15 min load: {server['load_1']}, {server['load_5']}, {server['load_15']}"
                    _tgapi_call(text)
                hlnotify = list(filter((serverName).__ne__, hlnotify))
                logging.info(f"Remove high load server: {serverName}, load {load}")

            ## if server reaches blocked notify threshold and not notified yet, notify and add it to notified list
            if (blocked.count(serverName) >= block_notify_threshold) and (serverName not in bknotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} is *BLOCKED* by CU & CT & CM.\nCU: {server['ping_10010']} %\nCT: {server['ping_189']} %\nCM: {server['ping_10086']} %"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} 已被三网屏蔽\nCU: {server['ping_10010']} %\nCT: {server['ping_189']} %\nCM: {server['ping_10086']} %"
                    _tgapi_call(text)
                bknotify.append(serverName)
                logging.info(f"Blocked server notified: {serverName}")
            ## else if server is unblocked and previously notified because of blocked, notify and remove it from blocked notify list
            elif (serverName not in blocked) and (serverName in bknotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} is *FREE*.\nCU: {server['ping_10010']} %\nCT: {server['ping_189']} %\nCM: {server['ping_10086']} %"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} 已解封\nCU: {server['ping_10010']} %\nCT: {server['ping_189']} %\nCM: {server['ping_10086']} %"
                    _tgapi_call(text)
                bknotify = list(filter((serverName).__ne__, bknotify))
                logging.info(f"Server unblocked: {serverName}")
            
            ## if server reaches disk full notify threshold and not notified yet, notify and add it to notified list
            if (diskfull.count(serverName) >= diskfull_notify_threshold) and (serverName not in dfnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\nDisk usage of #{serverName} *reached* {thresholdDict[serverName]['DU_THRES']}%.\nUsage: {round(server['hdd_used']/1024, 2)}/{round(server['hdd_total']/1024, 2)} GB"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} 磁盘使用率已达到 *{thresholdDict[serverName]['DU_THRES']}%*.\n使用量: {round(server['hdd_used']/1024, 2)}/{round(server['hdd_total']/1024, 2)} GB"
                    _tgapi_call(text)
                dfnotify.append(serverName)
                logging.info(f"Disk full server notified: {serverName}")
            ## else if server disk is not full and previously notified because of disk full, notify and remove it from disk full notify list
            elif (serverName not in diskfull) and (serverName in dfnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\nDisk usage of #{serverName} is *lower* than {thresholdDict[serverName]['DU_THRES']}%.\nUsage: {round(server['hdd_used']/1024, 2)}/{round(server['hdd_total']/1024, 2)} GB"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} 磁盘用量 *低于* {thresholdDict[serverName]['DU_THRES']}%.\n用量: {round(server['hdd_used']/1024, 2)}/{round(server['hdd_total']/1024, 2)} GB"
                    _tgapi_call(text)
                dfnotify = list(filter((serverName).__ne__, dfnotify))
                logging.info(f"Disk usage of *{serverName}* is lower.")
            
            ## if server reaches too many tcp notify threshold and not notified yet, notify and add it to notified list
            if (tcptoomany.count(serverName) >= tcpcount_notify_threshold) and (serverName not in tcpnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} too many TCP connections: {server['tcp_count']}, possible DDOS/CC attack"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} TCP 连接数过多: {server['tcp_count']}，可能遭遇攻击"
                    _tgapi_call(text)
                tcpnotify.append(serverName)
                logging.info(f"TCP too many notified: {serverName}")
            ## else if server tcp connection is not too many and previously notified because of too many tcp, notify and remove it from too many tcp notify list
            elif (serverName not in tcptoomany) and (serverName in tcpnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} TCP connections return to normal: {server['tcp_count']}"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} TCP 连接数恢复正常: {server['tcp_count']}"
                    _tgapi_call(text)
                tcpnotify = list(filter((serverName).__ne__, tcpnotify))
                logging.info(f"TCP connection return to normal: {serverName}")
            
            ## if server reaches bad cu notify threshold and not notified yet, notify and add it to notified list
            if (badcu.count(serverName) >= badcu_notify_threshold) and (serverName not in badcunotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} successful ping to CU *is less than* threshold\nCU: {server['ping_10010']}"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} PING CU 成功率低于阈值\nCU: {server['ping_10010']}"
                    _tgapi_call(text)
                badcunotify.append(serverName)
                logging.info(f"Bad CU notified: {serverName}")
            ## else if server tcp connection is not too many and previously notified because of too many tcp, notify and remove it from too many tcp notify list
            elif (serverName not in badcu) and (serverName in badcunotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} successful ping to CU return to normal\nCU: {server['ping_10010']}"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} PING CU 成功率恢复正常\nCU: {server['ping_10010']}"
                    _tgapi_call(text)
                badcunotify = list(filter((serverName).__ne__, badcunotify))
                logging.info(f"Bad CU server return to normal: {serverName}")
            
            ## if server reaches bad ct notify threshold and not notified yet, notify and add it to notified list
            if (badct.count(serverName) >= badct_notify_threshold) and (serverName not in badctnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} successful ping to CT *is less than* threshold\CT: {server['ping_189']}"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} PING CT 成功率低于阈值\CT: {server['ping_189']}"
                    _tgapi_call(text)
                badctnotify.append(serverName)
                logging.info(f"Bad CT notified: {serverName}")
            ## else if server tcp connection is not too many and previously notified because of too many tcp, notify and remove it from too many tcp notify list
            elif (serverName not in badct) and (serverName in badctnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} successful ping to CT return to normal\CT: {server['ping_189']}"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} PING CT 成功率恢复正常\CT: {server['ping_189']}"
                    _tgapi_call(text)
                badctnotify = list(filter((serverName).__ne__, badctnotify))
                logging.info(f"Bad CT server return to normal: {serverName}")
            
                        ## if server reaches bad ct notify threshold and not notified yet, notify and add it to notified list
            if (badcm.count(serverName) >= badcm_notify_threshold) and (serverName not in badcmnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} successful ping to CM *is less than* threshold\CM: {server['ping_10086']}"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} PING CM 成功率低于阈值\CM: {server['ping_10086']}"
                    _tgapi_call(text)
                badcmnotify.append(serverName)
                logging.info(f"Bad cm notified: {serverName}")
            ## else if server tcp connecmion is not too many and previously notified because of too many tcp, notify and remove it from too many tcp notify list
            elif (serverName not in badcm) and (serverName in badcmnotify):
                if lang_uage == 'EN':
                    text = f"#ServerStatus {server_id}\n#{serverName} successful ping to CM return to normal\CM: {server['ping_10086']}"
                    _tgapi_call(text)
                else:
                    text = f"#ServerStatus {server_id}\n#{serverName} PING CM 成功率恢复正常\CM: {server['ping_10086']}"
                    _tgapi_call(text)
                badcmnotify = list(filter((serverName).__ne__, badcmnotify))
                logging.info(f"Bad cm server return to normal: {serverName}")
        
        time.sleep(monitor_interval)
        
        logging.debug(f"Server(s) in [offline]: {offline}")
        logging.debug(f"Server(s) in [blocked]: {blocked}")
        logging.debug(f"Server(s) in [highload]: {highload}")
        logging.debug(f"Server(s) in [diskfull]: {diskfull}")
        logging.debug(f"Server(s) in [tcptoomany]: {tcptoomany}")
        logging.debug(f"Server(s) in [badcu]: {badcu}")
        logging.debug(f"Server(s) in [badct]: {badct}")
        logging.debug(f"Server(s) in [badcm]: {badcm}")
        
        logging.debug(f"Server(s) in [olnotify]: {olnotify}")
        logging.debug(f"Server(s) in [bknotify]: {bknotify}")
        logging.debug(f"Server(s) in [hlnotify]: {hlnotify}")
        logging.debug(f"Server(s) in [dfnotify]: {dfnotify}")
        logging.debug(f"Server(s) in [tcpnotify]: {tcpnotify}")
        logging.debug(f"Server(s) in [badcunotify]: {badcunotify}")
        logging.debug(f"Server(s) in [badctnotify]: {badctnotify}")
        logging.debug(f"Server(s) in [badcmnotify]: {badcmnotify}")
        
    except KeyboardInterrupt:
        print("\n**\nManually stopped\n**.")
        text = f'#ServerStatus {server_id}\nServer monitor gracefully stopped.'
        _tgapi_call(text)
        logging.info('Manually stopped')
        _stash(stash_json)
        break
    except Exception as e:
        if lang_uage == 'EN':
            text = f'#ServerStatus {server_id}\nServer monitor has an error, please check log.'
            _tgapi_call(text)
        elif lang_uage == 'ZH':
            text = f'#ServerStatus {server_id}\n服务器监视器遇到问题，请查看日志。'
            _tgapi_call(text)
        logging.error(f'Server monitor killed by an error.\n\n{e}')
        _stash(stash_json)
        break


#!/usr/bin/env python3
# coding=utf-8

import json
import time
from telegram import Bot
import logging
import os


## Preferences
bot_token = os.getenv('BOT_TOKEN') # telegram bot token
account_id = int(os.getenv('ACC_ID')) # telegram id
monitor_interval = int(os.getenv('MON_INTRVL', 10)) # in seconds
packet_loss_threshold = int(os.getenv('PL_THRES', 90)) # % of total packet loss
packet_loss_weight_cm = float(os.getenv('PL_CM', 1.0)) # weight of CM packet loss
packet_loss_weight_ct = float(os.getenv('PL_CT', 1.0)) # weight of CT packet loss
packet_loss_weight_cu = float(os.getenv('PL_CU', 1.0)) # weight of CU packet loss
load_threshold = int(os.getenv('SL_THRES')) # 15 min load
disk_threshold = int(os.getenv('DU_THRES')) # % of disk usage
block_notify_threshold = int(os.getenv('BN_THRES', 6)) # how many times the server name appears in list
load_notify_threshold = int(os.getenv('LN_THRES', 6)) # how many times the server name appears in list
offline_notify_threshold = int(os.getenv('ON_THRES', 6)) # how many times the server name appears in list
log_level = os.getenv('LOG_LVL', 'INFO').upper() # log level
lang_uage = os.getenv('LANG_UAGE', 'ZH') # language
stats_json = '/ServerStatus/json/stats.json' # change log location if needed
log_file = '/ServerStatus/log/server-monitor.log' # log file location
logging.basicConfig(filename=log_file, 
                    level=log_level, 
                    format='%(asctime)s - %(levelname)s - %(message)s')




## code starts
offline = []
blocked = []
highload = []
diskfull = []

olnotify = []
bknotify = []
hlnotify = []
dfnotify = []

## whitelist for servers that do not alert when system load is high
load_wl = []

## gathering data
bot = Bot(bot_token)
logging.info('Server monitor started.')
if lang_uage == 'EN':
    bot.send_message(chat_id=account_id, 
                    text='*#ServerStatus*\n\nServer monitor started.',
                    parse_mode='Markdown')
elif lang_uage == 'ZH':
    bot.send_message(chat_id=account_id, 
                    text='*#ServerStatus*\n\n服务器监视器已启动。',
                    parse_mode='Markdown')
time.sleep(5)
while True:
    try:
        with open(stats_json, 'r', encoding='utf-8') as f:
            js = json.load(f)
        for server in js['servers']:
            isonline = server['online4']
            if isonline is False:
                if offline.count(server['name']) < offline_notify_threshold:
                    offline.append(server['name'])
                    logging.info(f"New offline server: {server['name']}")
            elif isonline is True:
                #isfree = server['ip_status']
                isfree = (server['ping_10010']*packet_loss_weight_cu + server['ping_189']*packet_loss_weight_ct + server['ping_10086'])*packet_loss_weight_cm < packet_loss_threshold
                load = server['load_15']
                if server['name'] in offline:
                    offline = list(filter((server['name']).__ne__, offline))
                    logging.info(f"Remove offline server: {server['name']}")
                    if load > load_threshold and server['name'] not in load_wl:
                        if highload.count(server['name']) < load_notify_threshold:
                            highload.append(server['name'])
                            logging.info(f"New high load server: {server['name']}, load {load}")
                    elif load < load_threshold:
                        if server['name'] in highload:
                            highload = list(filter((server['name']).__ne__, highload))
                            logging.info(f"Remove high load server: {server['name']}, load {load}")
                elif isfree is False:
                    if blocked.count(server['name']) < block_notify_threshold:
                        blocked.append(server['name'])
                        logging.info(f"New blocked server: {server['name']}")
                    if load > load_threshold and server['name'] not in load_wl:
                        if highload.count(server['name']) < load_notify_threshold:
                            highload.append(server['name'])
                            logging.info(f"New high load server: {server['name']}, load {load}")
                    elif load < load_threshold:
                        if server['name'] in highload:
                            highload = list(filter((server['name']).__ne__, highload))
                            logging.info(f"Remove high load server: {server['name']}, load {load}")
                elif isfree is True:
                    if server['name'] in blocked:
                        blocked = list(filter((server['name']).__ne__, blocked))
                        logging.info(f"Remove blocked server: {server['name']}")
                        if load > load_threshold and server['name'] not in load_wl:
                            if highload.count(server['name']) < load_notify_threshold:
                                highload.append(server['name'])
                                logging.info(f"New high load server: {server['name']}, load {load}")
                        elif load < load_threshold:
                            if server['name'] in highload:
                                highload = list(filter((server['name']).__ne__, highload))
                                logging.info(f"Remove high load server: {server['name']}, load {load}")
                    elif load > load_threshold and server['name'] not in load_wl:
                        if highload.count(server['name']) < load_notify_threshold:
                            highload.append(server['name'])
                            logging.info(f"New high load server: {server['name']}, load {load}")
                    elif load < load_threshold:
                        if server['name'] in highload:
                            highload = list(filter((server['name']).__ne__, highload))
                            logging.info(f"Remove high load server: {server['name']}, load {load}")
                            
        ## nofify when threshold reached
        for server in js['servers']:
            if blocked.count(server['name']) == block_notify_threshold and bknotify.count(server['name']) < 1:
                if lang_uage == 'EN':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* packet loss rate is *HIGH*.\n*CT:* {server['ping_189']*packet_loss_weight_ct} %\n*CM:* {server['ping_10086']*packet_loss_weight_cm} %\n*CU:* {server['ping_10010']*packet_loss_weight_cu} %",
                                    parse_mode='Markdown')
                elif lang_uage == 'ZH':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* 的丢包率*较高*.\n*CT:* {server['ping_189']*packet_loss_weight_ct} %\n*CM:* {server['ping_10086']*packet_loss_weight_cm} %\n*CU:* {server['ping_10010']*packet_loss_weight_cu} %",
                                    parse_mode='Markdown')
                bknotify.append(server['name'])
                logging.info(f"Blocked server notified: {server['name']}")
                # time.sleep(5)
            elif offline.count(server['name']) == offline_notify_threshold and olnotify.count(server['name']) < 1:
                if lang_uage == 'EN':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* is *OFFLINE*.",
                                    parse_mode='Markdown')
                elif lang_uage == 'ZH':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* *已离线*.",
                                    parse_mode='Markdown')
                olnotify.append(server['name'])
                logging.info(f"Offline server notified: {server['name']}")
                # time.sleep(5)
            elif highload.count(server['name']) == load_notify_threshold and hlnotify.count(server['name']) < 1:
                if lang_uage == 'EN':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* is under *HEAVY LOAD*.\n1,5,15 min load: {server['load_1']}, {server['load_5']}, {server['load_15']}",
                                    parse_mode='Markdown')
                elif lang_uage == 'ZH':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* 的系统负载*较高*.\n1,5,15 min load: {server['load_1']}, {server['load_5']}, {server['load_15']}",
                                    parse_mode='Markdown')
                hlnotify.append(server['name'])
                logging.info(f"Highload server notified: {server['name']}")
                # time.sleep(5)
            elif server['name'] in olnotify and server['name'] not in offline:
                if lang_uage == 'EN':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* is *BACK ONLINE*.",
                                    parse_mode='Markdown')
                elif lang_uage == 'ZH':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* 已恢复*在线状态*.",
                                    parse_mode='Markdown')
                olnotify = list(filter((server['name']).__ne__, olnotify))
                logging.info(f"Server back online: {server['name']}")
                # time.sleep(5)
            elif server['name'] in bknotify and server['name'] not in blocked:
                if lang_uage == 'EN':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* packet loss rate is *LOW*.\n*CT:* {server['ping_189']*packet_loss_weight_ct} %\n*CM:* {server['ping_10086']*packet_loss_weight_cm} %\n*CU:* {server['ping_10010']*packet_loss_weight_cu} %",
                                    parse_mode='Markdown')
                elif lang_uage == 'ZH':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* 的丢包率*恢复正常*.\n*CT:* {server['ping_189']*packet_loss_weight_ct} %\n*CM:* {server['ping_10086']*packet_loss_weight_cm} %\n*CU:* {server['ping_10010']*packet_loss_weight_cu} %",
                                    parse_mode='Markdown')
                bknotify = list(filter((server['name']).__ne__, bknotify))
                logging.info(f"Server unblocked: {server['name']}")
                # time.sleep(5)
            elif server['name'] in hlnotify and server['name'] not in highload:
                if lang_uage == 'EN':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* is under *NORMAL LOAD*.\n1,5,15 min load: {server['load_1']}, {server['load_5']}, {server['load_15']}",
                                    parse_mode='Markdown')
                elif lang_uage == 'ZH':
                    bot.send_message(chat_id=account_id,
                                    text=f"*#ServerStatus*\n\n*{server['name']}* 的系统负载*恢复正常*.\n1,5,15 min load: {server['load_1']}, {server['load_5']}, {server['load_15']}",
                                    parse_mode='Markdown')
                hlnotify = list(filter((server['name']).__ne__, hlnotify))
                logging.info(f"Remove high load server: {server['name']}, load {load}")
                # time.sleep(5)
                    
        ## notify when disk >= `disk_threshold` full
        for server in js['servers']:
            isonline = server['online4']
            if isonline is True:
                if (server['hdd_used'] / (server['hdd_total'] if server['hdd_total'] != 0 else 1e16) >= disk_threshold/100) and (server['name'] not in dfnotify):
                    diskfull.append(server['name'])
                    if lang_uage == 'EN':
                        bot.send_message(chat_id=account_id,
                                        text=f"*#ServerStatus*\n\nDisk usage of *{server['name']}* has reached *{disk_threshold}%*.\nUsage: {round(server['hdd_used']/1024, 2)}/{round(server['hdd_total']/1024, 2)} GB",
                                        parse_mode='Markdown')
                    elif lang_uage == 'ZH':
                        bot.send_message(chat_id=account_id,
                                        text=f"*#ServerStatus*\n\n*{server['name']}* 的磁盘使用率已达到 *{disk_threshold}%*.\n使用量: {round(server['hdd_used']/1024, 2)}/{round(server['hdd_total']/1024, 2)} GB",
                                        parse_mode='Markdown')
                    dfnotify.append(server['name'])
                    logging.info(f"Disk full server notified: {server['name']}")
                    time.sleep(5)
                elif (server['hdd_used'] / (server['hdd_total'] if server['hdd_total'] != 0 else 1e16) < disk_threshold/100) and (server['name'] in dfnotify):
                    dfnotify = list(filter((server['name']).__ne__, dfnotify))
                    logging.info(f"Disk usage of *{server['name']}* is lower.")

        time.sleep(monitor_interval)
        
        logging.debug(f"Server(s) in [offline]: {offline}")
        logging.debug(f"Server(s) in [blocked]: {blocked}")
        logging.debug(f"Server(s) in [highload]: {highload}")
        logging.debug(f"Server(s) in [diskfull]: {diskfull}")
        
        logging.debug(f"Server(s) in [olnotify]: {olnotify}")
        logging.debug(f"Server(s) in [bknotify]: {bknotify}")
        logging.debug(f"Server(s) in [hlnotify]: {hlnotify}")
        logging.debug(f"Server(s) in [dfnotify]: {dfnotify}")
        
    except KeyboardInterrupt:
        print("\n**\nManually stopped\n**.")
        logging.info('Manually stopped')
        break
    except Exception as e:
        if lang_uage == 'EN':
            bot.send_message(chat_id=account_id,
                            text='*#ServerStatus*\n\nServer monitor killed by error, please check.',
                            parse_mode='Markdown')
        elif lang_uage == 'ZH':
            bot.send_message(chat_id=account_id,
                            text='*#ServerStatus*\n\n服务器监视器遇到问题停止工作，请查看。',
                            parse_mode='Markdown')
        logging.error(f'Server monitor killed by error.\n\n{e}')
        break


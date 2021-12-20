#!/usr/bin/env python3
# coding=utf-8

'''
feature_1: custom threshold for each server
'''

import configparser
import os


if os.getenv('PREF') == 'FILE':
    '''
    use preferences from reading `config.ini`
    ---
    `config.ini` format:
    
    [DEFAULT]
    PL_THRES=90
    PL_CM=1
    PL_CT=1
    PL_CU=1
    SL_THRES=
    DU_THRES=
    BN_THRES=6
    LN_THRES=6
    ON_THRES=6

    [custom1]
    server1=a😛
    server2=b-fdjs.com
    server3=c_a
    PL_THRES=10
    '''
    pass
elif os.getenv('PREF') == 'ENV':
    '''
    use preferences from docker env
    '''
    pass

config = configparser.ConfigParser()
config.optionxform = str
config.read('./config.ini')

print(config.sections())
path_items = config.items('custom1')
for key,value in path_items:
    if "server" in key:
        print(value)
    else:
        print(key,value)

'''
result:
['custom1']
pl_thres 90
pl_cm 1
pl_ct 1
pl_cu 5
a😛
b-fdjs.com
c_a
'''

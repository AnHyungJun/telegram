#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple Bot to reply to Telegram messages.

This is built on the API wrapper, see echobot2.py to see the same example built
on the telegram.ext bot framework.
This program is dedicated to the public domain under the CC0 license.
"""
import logging
from time import sleep
import requests
from datetime import datetime
import sys
import json
from typing import List,Dict
from pprint import pprint
import argparse
import util

CHECK_FIELD = ['item_count','response_count','data_size']

class MessageClient(object):


    def __init__(self,message_data:dict):
        #logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
        self.message_data = self.message_setting(message_data)
        self.check_flag,self.check_data_dict = self.db_flag_check(message_data)

    def message_setting(self,message_data:dict) -> Dict:
        self.db_flag = message_data.pop('db_save_flag')
        self.slack_flag = message_data.pop('slack_send_flag')
        self.sms_flag = message_data.pop('sms_send_flag')
        self.message_type = message_data['message_type']
        
        return message_data
    
    #check할 데이터를 check_data_dict로 설정하고 
    #message_data는 data 값으로 변경
    def db_flag_check(self,message_data:Dict) -> (bool,Dict):
        flag = False
        check_data_dict = dict()
        for field in CHECK_FIELD:
            try:
                if message_data[field]['flag'] != 'N':
                    flag = True
                    check_data_dict[field] = message_data[field]
                message_data[field] = message_data[field]['data']
            except:
                pass
        return flag,check_data_dict
    
    #n1 수집된 데이터
    #n2 이전 수집 데이터
    def check_field(self,n1,n2) -> bool:
        return True if n1 < n2 else False
        

    def make_error_messgae(self,message:str) -> Dict:
        send_dict = dict(
            spider_name=self.message_data['spider_name'],
            project_name=self.message_data['project_name'],
            process_num=self.message_data['process_num'],
            crawl_start_time=self.message_data['crawl_start_time'],
            message=message,
            message_type='EME_ERROR'
        )
        return send_dict


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    message_str = sys.argv[1]
    logging.info(message_str)
    # message_dict = json.loads(message_str)
    # client: HealthCheckMessage = HealthCheckMessage()
    
    # client.message_parsing(message_dict)
    # client.slack_message_parsing(message_dict)
    
    # client.db_client._close()
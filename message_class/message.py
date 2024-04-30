import os
import logging
import sys
import json
import requests
import argparse
from typing import Dict,Any
from datetime import datetime,timedelta
from pathlib import Path
#util의 __init__.py
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, os.path.abspath(SCRIPT_DIR))
sys.path.insert(0, os.path.abspath(ROOT_DIR))
import util
from message_item import ExtendMessage,BaseMessage
API_URL = 'http://10.1.41.28:9999/message.json'

class BaseMessageClass(object):

    def __init__(self,item:dict={}) -> None:
        self.cur_day = util.cur_day_str()
        self.message_item = self.create_message(item)

    def create_message(self,item:dict) -> BaseMessage:
        message_item = BaseMessage(item)
        message_item.validate() #message_item 유효성 check
        return message_item
    
    #api서버에 메세지 send
    def send_messege(self) -> None:
        json_item = self.get_message()
        response = requests.post(API_URL,data=json.dumps(json_item))
        return response
    
    #message_item에 dict 타입 데이터 update
    def add_dict(self,item:dict) -> None:
        for k,v in item.items():
            if isinstance(v,datetime):
                v = util.datetime_to_str(v)
            self.message_item[k] = v
        self.message_item.validate()
    
    #message_item setter field = key 
    def set_value(self,field:str,value:Any) -> None:
        #datetime의 경우 str 변환
        if isinstance(value,datetime):
            value = util.datetime_to_str(value)
        self.message_item[field] = value
        self.message_item.validate()
    
    #Model 데이터를 json 형식으로 반환
    def get_message(self) -> Dict:
        return self.message_item.to_primitive()
    
    def print_message(self) -> None:
        util.print_json_message(self.get_message())

    def reset_data(self):
        item = {
            'scrapy_name' : self.message_item['scrapy_name'],
            'project_name' : self.message_item['project_name'],
            'process_num' : self.message_item['process_num']
            }
        self.message_item = self.create_message(item)
    
    def __del__(self):
        #message 파일 저장
        pass
        #save_dir:str = 'message_out'
        #file_name:str = f'test_message_{self.cur_day}.json'
        #util.json_save_file(save_dir,file_name,self.get_message())

class TotalMessageClass(BaseMessageClass):
    
    
    def __init__(self,item:dict) -> None:
        super().__init__(item)

    def create_message(self,item:dict) -> ExtendMessage:
        message_item = ExtendMessage(item)
        message_item.validate()
        return message_item

    #수집 시간 계산
    def get_elapsed_time(self) -> str:
        elapsed_time:timedelta = util.cal_elapsed_time(self.message_item.crawl_start_time,self.message_item.crawl_end_time)
        return elapsed_time.total_seconds()
        

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--json_file", "-jf", type=str, required=True)
    args = parser.parse_args()
    with open(args.json_file) as f:
        item = json.loads(f.read().strip())
    #message = TotalMessage(item)
    message = BaseMessageClass(item)
    #수집 시간 계산 (TotalMessage)
    #elapsed_time = message.get_elapsed_time()
    #수집 시간 message data set
    #message.set_value('elapsed_time',elapsed_time)
    
    #message class print
    util.print_json_message(message.get_message())
    
    #api 서버로 데이터 str 전송
    logging.info(message.send_messege().text)






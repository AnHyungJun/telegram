import logging
import requests
import os
import inspect
import sys
from typing import List,Dict
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
import util
from datetime import timedelta

SLACK_CHANNEL_LIST: Dict = dict(
    SUCCESS=dict(
        token='xoxb-4780509238689-4753346949127-6YP4EDDq0swsqKwS85b0JArA',
        channel='#ahj_test',
    ),
    ERROR=dict(
        token='xoxb-4780509238689-4753346949127-6YP4EDDq0swsqKwS85b0JArA',
        channel='#error_a',
    ),
    EME_ERROR=dict(
        token='xoxb-4780509238689-4753346949127-6YP4EDDq0swsqKwS85b0JArA',
        channel='#error_b',
    )
)


class MessageSlackClient(object):


    def __init__(self):
        #logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
        for v in SLACK_CHANNEL_LIST.values():
            v['client'] = WebClient(token=v['token'])
    
    def send_messege(self,message:dict):
        message_type:str = message.pop('message_type')
        slack_info:dict = SLACK_CHANNEL_LIST[message_type]
        message_block:dict = self.make_message_block(message,message_type)

        response = slack_info['client'].chat_postMessage(
            channel=slack_info['channel'],
            blocks=message_block['blocks']
        )
        return response


    def bold_dict(self,key,value) -> str:
        return f"*{key}* :: {value}"

    def make_message_block(self,message:dict,message_type:str) -> None:
        def make_multi_section(section_list:dict) -> dict:
            
            _section = dict(
                type="section",
                fields=[]
            )
            for key,value in section_list.items():
                field = dict(
                    type="mrkdwn",
                    text=f"*{key}:*\n{value}"
                )
                _section['fields'].append(field)
            return _section
        
        def make_single_section(_text:str) -> dict:
            _section = dict(
                type="section",
                text=dict(
                    type="mrkdwn",
                    text=_text
                )
            )
            return _section
        
        result = dict(
            blocks=[
                {
                    "type":"header",
                    "text":{
                        "type": "plain_text",
				        "text": "################",
				        "emoji": True
                    }
                }
            ]
        )
        add_dict = make_multi_section(util.pop_field(message,['spider_name','project_name']))
        result['blocks'].append(add_dict)
        add_dict = make_multi_section(util.pop_field(message,['process_num','crawl_start_time']))
        result['blocks'].append(add_dict)
        if message_type != 'EME_ERROR':
            message['elapsed_time'] = str(timedelta(seconds=message['elapsed_time']))
            add_dict = make_multi_section(util.pop_field(message,['crawl_end_time','elapsed_time']))
            result['blocks'].append(add_dict)
        
        message['message'] = message.pop('message')
        for key,value in message.items():
            value = util.type_to_str(value)
            add_dict = make_single_section(self.bold_dict(key,value))
            result['blocks'].append(add_dict)
        return result
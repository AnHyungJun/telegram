#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple Bot to reply to Telegram messages.

This is built on the API wrapper, see echobot2.py to see the same example built
on the telegram.ext bot framework.
This program is dedicated to the public domain under the CC0 license.
"""
import logging
import telegram
from telegram.error import NetworkError
from time import sleep
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import asyncio
from datetime import datetime
import sys
from typing import List,Dict
import shutil

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

TEL_TYPE = {
    "CHECK" : "@BDL_Check",
    "ERROR" : "@daumsoft_sms"
        
}
TEL_TOKEN = {
    "CHECK" : "1268775444:AAEApd3FCqDJ9wqfWOTRuPzN4_21ZL8iPrg",
    "ERROR" : "1323719542:AAEvCCQyvDSPoKMAT1F2QiSdQRPaUZnchPU"

}

def main(message):
    """Run the bot."""
    # Telegram Bot Authorization Token
    bot = telegram.Bot(token=TEL_TOKEN[message['message_type']])

    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(echo(bot,message))
    #echo(bot,message)


async def echo(bot,message):
    """Echo the message the user sent."""
    
    # Request updates after the last update_id
    #updates = bot.getUpdates()
    #bot.sendMessage(chat_id='849126331', text='SERVER ALIVE')
    base_message = 'project :: {0}\nmessage :: {1}\n'.format(message['project_name'],message['message'])
    for etc in message.get('etc',[]):
        k,v = list(etc.items())[0]
        base_message += '{0} :: {1}\n'.format(k,v)
    await bot.sendMessage(chat_id=TEL_TYPE[message['message_type']], text=base_message)

def send_messege():
    # client = dict(
    #     token='xoxb-4780509238689-4753346949127-6YP4EDDq0swsqKwS85b0JArA',
    #     channel='#error_a',
        
    # )
    token='xoxb-4780509238689-4753346949127-6YP4EDDq0swsqKwS85b0JArA'
    client = WebClient(token=token)
    message_block:dict = dict(
            blocks=[
                {
                    "type":"header",
                    "text":{
                        "type": "plain_text",
				        "text": "################",
				        "emoji": True
                    }
                },
                {
                    "type":"section",
                    "text":dict(
                        type="mrkdwn",
                        text='telegram Q  log  error'
                    )
                }
            
            ]
        )
    response = client.chat_postMessage(
        channel='#error_a',
        blocks=message_block['blocks']
    )
    return response


if __name__ == '__main__':
    log_file = sys.argv[1]
    if log_file != 'timecheck':
        b = list()
        with open(log_file) as f:
            v = f.read()
            b = v.split('Traceback')
        
        for i in b[1:]:
            if 'sqlite3' in i or 'FileMigrateError' in i or 'AuthBytesInvalidError' in i:
                pass
            else:
                
                form_data = {
                        "message_type" : 'ERROR',
                        "project_name" : 'telegram Q',
                        "message" : 'log error',
                        "date_str" : datetime.now().strftime("%Y%m%d%H%M%S")
                }
                message = form_data
                
                main(message)
                send_messege()
                break
    else:
        form_data = {
                "message_type" : 'ERROR',
                "project_name" : 'telegram Q',
                "message" : 'log timecheck error',
                "date_str" : datetime.now().strftime("%Y%m%d%H%M%S")
        }
        message = form_data
        
        main(message)
        send_messege()
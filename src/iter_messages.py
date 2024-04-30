from telethon import TelegramClient
from telethon import utils
from telethon import types
from telethon.sessions import StringSession
from datetime import datetime
from extract_to_dict import extract_from
import json
import sys
import logging
import os
import time
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
COMMON_DIR = os.path.abspath(os.path.join(ROOT_DIR, "common"))
sys.path.insert(0, os.path.abspath(ROOT_DIR))
from common.db_client_telegram import TelegramDBClient
import util
import atexit
# Logging


logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)

# Credentials
api_id = '26473415'
api_hash = 'c4117337c10cd35735cccbd5edd44829'
client: TelegramClient = TelegramClient('anon', api_id, api_hash)
dbclient57: TelegramDBClient = TelegramDBClient(db_config_file='common/db_config/telegram57.ini')
dbclient58: TelegramDBClient = TelegramDBClient(db_config_file='common/db_config/telegram58.ini')
#channel_dict - channel_id,channel_name,crawl_message_id
channel_dict: dict = dbclient57.select_channel_info()
channel_out_list: list = []


def to_marked_channel_id(real_id: int) -> any:
  return utils.get_peer_id(types.PeerChannel(real_id))


def load_channel_info(path: str="config/channel_info.json") -> list:
  channel_list: list = list()
  with open(path) as f:
    for line in f:
      channel_list.append(json.loads(line.strip()))
  return channel_list

async def main(channel_dict: dict,output_file):
  try:
    channel_id = int(channel_dict['channel_id'])
    # 1. 수집 대상이 되는 채널 정보를 조회합니다.
    channel = await client.get_entity(to_marked_channel_id(channel_id))
    #path = f"./out/downloads/{channel_dict['channel_id']}"
    #if not os.path.isdir(path):
    #  os.mkdir(path)
    
    # 2. iter_messages() API로 메시지 히스토리를 조회합니다.
    async for message in client.iter_messages(channel, limit=None, offset_id=channel_dict['last_message_id'],reverse=True):
      
      # 3. message 객체에서 필요한 필드를 추출합니다.
      message_dict: dict = await extract_from(message)
      logging.info(message_dict['message'])
      logging.info(message_dict['message'].replace('\n','@@@'))

      #logging.info(f"{message_dict['message_id']}/{message_dict['datetime']}/{message_dict['message']}")
      #if channel_dict['last_message_id'] < message_dict['message_id'] :
      #  channel_dict['last_message_id'] = message_dict['message_id']
      #output_file.write(json.dumps(message_dict,ensure_ascii=False)+'\n')
      time.sleep(1)
  finally:
    channel_out_list.append(channel_dict)

def _close(path: str) -> None:
  with open(f'{path}.{util.cur_day_str()}','w') as f:
    for channel in channel_out_list:
      f.write(json.dumps(channel,ensure_ascii=False)+'\n')

if __name__ == '__main__':
  #1342927618
  #python iter_messages.py mode input_file/id
  #mode single | many 
  #single의 경우 채널 id many인 경우 파일 경로
  
  mode: str = sys.argv[1]
  output_file = open(f'out/telegram_message.json.{util.cur_day_str()}','w')
  if mode not in ['single','many']:
    logging.info('mode > single,many')
    logging.info('python iter_messages.py mode input_file/id')
    sys.exit()
  
  
  if mode == 'many':
    path: str = sys.argv[2]
    channel_list = load_channel_info(path)
  elif mode == 'single':
    channel_id: str = sys.argv[2]
    channel_list: list = [{"channel_name": None, "last_message_id": 100, "url": None, "channel_id": channel_id}]
  
  
    
  with client:
    try:
      for channel_dict in channel_list:
        logging.info(channel_dict)
        # channel_dict['channel_id'] = '1342927618'
        # channel_dict['channel_id'] = '2026710929' # test
        # channel_dict['last_message_id'] = 10
        client.loop.run_until_complete(main(channel_dict,output_file))
    finally:
      output_file.close()
      _close(path)

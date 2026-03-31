from telethon import TelegramClient, events
from datetime import datetime
from extract_to_dict import extract_from
import json
import sys
import logging
import os
import asyncio
import traceback
from embedded_crawler import TelegramUrlProcessor
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
COMMON_DIR = os.path.abspath(os.path.join(ROOT_DIR, "common"))
sys.path.insert(0, os.path.abspath(ROOT_DIR))
SAVE_DIR = '/locdisk/telegram_data'
#from common.db_client_telegram import TelegramDBClient
import util
from logging import handlers
from message_class.message import TotalMessageClass
from send_message import KafkaHandler

CHECK_TIME = 60*60 #1시간마다 message 체크
user_key:str = sys.argv[1]
out_dir: str = f'{ROOT_DIR}/out'
item_count: int = 0
cur_time: datetime = datetime.now()
cur_day: str = util.cur_day_str()


def log_setting():
  rotation_logger = logging.getLogger()
  formatter = logging.Formatter('%(asctime)s  (%(levelname)s) %(message)s')
  rotation_handler = handlers.TimedRotatingFileHandler(filename=f'{ROOT_DIR}/log/telegram.log.{user_key}',when='midnight', interval=1, encoding='utf-8')
  rotation_handler.suffix = '%Y%m%d'
  rotation_handler.setFormatter(formatter)
  rotation_logger.setLevel(logging.INFO)
  rotation_logger.addHandler(rotation_handler)
  return rotation_logger

def load_user_list() -> dict:
  with open(f'{ROOT_DIR}/config/user_info.json') as f:
    return json.loads(f.read().strip())

def read_channel_list(path=f"{ROOT_DIR}/etc/channel_list.{cur_day}.json") -> dict:
  with open(path) as f:
    p = json.loads(f.read().strip())
  return_dict = dict()
  for k,v in p.items():
    return_dict[int(k)] = v
  return return_dict

def load_message_json() -> dict:
  base_message_path: str = f"{ROOT_DIR}/config/telegram_message.json"
  with open(base_message_path) as f:
    base_message = json.loads(f.read().strip())
  return base_message 

def mkdir_path(channel_id: str) -> str:
  cur_date: str = util.cur_day_str()
  date_path: str = f"{SAVE_DIR}/etc_file/{cur_date}"
  if not os.path.isdir(date_path):
    os.mkdir(date_path)
  path: str = f"{date_path}/{channel_id}"
  if not os.path.isdir(path):
    os.mkdir(path)
  return f"{path}",f"{SAVE_DIR}/etc_file/{cur_date}/{channel_id}"

def _reset():
  global item_count,cur_time
  item_count = 0
  cur_time = datetime.now()


def send_cycle_message():
  message.set_value('crawl_end_time',datetime.now())
  elapsed_time = message.get_elapsed_time()
  message.set_value('elapsed_time',elapsed_time)
  message.set_value('item_count',{"flag":"W","data":item_count,"error_range":"1/5"})
  message.set_value('message','SUCCESS')
  message.set_value('slack_send_flag',False)
  message.send_message()
  _reset()
  message.create_message(message_json)


rotation_logger = log_setting()

user_list: dict = load_user_list()
message_json = load_message_json()

if not user_list.get(user_key,None):
    rotation_logger.error(f"User number {user_num} not found in user_info. Exiting.")
    sys.exit(1)

# Credentials
user_info = user_list[user_key]
client: TelegramClient = TelegramClient(user_info['session_file']+'.session', user_info['api_id'], user_info['api_hash'])
embedded_client: TelegramUrlProcessor = TelegramUrlProcessor()
kafka_client: KafkaHandler = KafkaHandler()
message: TotalMessageClass = TotalMessageClass(message_json)
message.set_value('crawl_start_time',datetime.now())

channel_dict = read_channel_list()
channel_id_list: list = list(channel_dict.keys())
#channel_id_list: list = list(map(lambda x: int(x), list(channel_dict.keys())))
message_file = open(f'{SAVE_DIR}/telegram_message.{cur_day}.json','a')

@client.on(events.NewMessage(
  incoming=True,        # 받은 메시지
  ))
  
# 1. handler의 매개변수인 event는 Message와 동일한 객체입니다.
async def handler(event):
  global item_count
  global message_file
  global cur_day
  # 2. message 객체에서 필요한 필드를 추출합니다.
  try:
    
    rotation_logger.info(event)
    if event.chat.id in channel_id_list:
      tmp_day: str = util.cur_day_str()
      message_dict: dict = await extract_from(event)
      if (message_dict['has_photo'] or message_dict['has_document']):
        path,save_dir = mkdir_path(message_dict['channel_id'])
        file_path: str = await event.download_media(file=path)
        if ' ' in file_path:
          replace_file_path = file_path.replace(' ','_')
          os.rename(file_path, replace_file_path)
          file_path = replace_file_path
        file_name = file_path.split("/")[-1]
        message_dict['file_path'] = f"{save_dir}/{file_name}"
        message_dict['file_name'] = file_name
      else:
        message_dict['file_path'] = None
        message_dict['file_name'] = None
      channel_info: dict = channel_dict[message_dict['channel_id']]
      channel_info['crawl_message_id'] = message_dict['message_id']
      embedded_urls, url_metadata = await asyncio.to_thread(embedded_client.extract_urls_and_metadata, message_dict["message"])
      message_dict["embedded_urls"] = embedded_urls
      message_dict["url_metadata"] = url_metadata
      message_file.write(json.dumps(message_dict,ensure_ascii=False)+'\n')
      rotation_logger.info(message_dict)
      await asyncio.to_thread(kafka_client.send_kafka, message_dict)
      #rotation_logger.info(r)
      
      if tmp_day != cur_day:
        cur_day = tmp_day
        message_file.close()
        message_file = open(f'{SAVE_DIR}/telegram_message.{cur_day}.json','a')
        with open(f'{ROOT_DIR}/etc/channel_list.{cur_day}.json','w') as f:
          f.write(json.dumps(channel_dict,ensure_ascii=False))
      item_count = item_count + 1
      #3600초 마다 send_message
      # if util.time_check(cur_time,CHECK_TIME):
      #   send_cycle_message()
    else:
      rotation_logger.info(f"[CHANNEL_ID NOT IN] {event.chat.id} / {event.chat.username}")
  except Exception as e:
    rotation_logger.error('ERROR MESSAGE')
    rotation_logger.error(event.chat_id)
    rotation_logger.error(traceback.format_exc())


#atexit.register(_close())
#channel_info: dict = load_channel_info()
try:
  client.start()
  client.run_until_disconnected()  
finally:
  send_item = {'item_count':{"flag":"W","data":item_count,"error_range":"1/5"}}
  message.send_error_message('END PROGRAM',send_item)
  rotation_logger.info('END PROGRAM')

from telethon import TelegramClient, events
from datetime import datetime
from extract_to_dict import extract_from
import json
import sys
import logging
import os
import traceback
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
COMMON_DIR = os.path.abspath(os.path.join(ROOT_DIR, "common"))
sys.path.insert(0, os.path.abspath(ROOT_DIR))
from common.db_client_telegram import TelegramDBClient
import util
from logging import handlers
from message_class.message import TotalMessageClass

CHECK_TIME = 60*60 #1시간마다 message 체크

#logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)
rotation_logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s  (%(levelname)s) %(message)s')
rotation_handler = handlers.TimedRotatingFileHandler(filename=f'{ROOT_DIR}/log/telegram.log',when='midnight', interval=1, encoding='utf-8')
rotation_handler.suffix = '%Y%m%d'
rotation_handler.setFormatter(formatter)
rotation_logger.setLevel(logging.INFO)
rotation_logger.addHandler(rotation_handler)


def load_message_json() -> dict:
  base_message_path: str = f"{ROOT_DIR}/config/telegram_message.json"
  with open(base_message_path) as f:
    base_message = json.loads(f.read().strip())
  return base_message 

# Credentials
api_id = '26473415'
api_hash = 'c4117337c10cd35735cccbd5edd44829'
out_dir: str = '/cluster/disk1/financial_crawled_data'
client: TelegramClient = TelegramClient('anon', api_id, api_hash)
dbclient57: TelegramDBClient = TelegramDBClient(db_config_file='common/db_config/telegram57.ini')
dbclient58: TelegramDBClient = TelegramDBClient(db_config_file='common/db_config/telegram58.ini')
message_json = load_message_json()
message: TotalMessageClass = TotalMessageClass(message_json)
message.set_value('crawl_start_time',datetime.now())
#channel_dict - channel_id,channel_name,crawl_message_id
channel_dict: dict = dbclient57.select_channel_info()
channel_id_list: list = channel_dict.keys()
channel_out_list: list = []
item_count: int = 0
cur_time: datetime = datetime.now()


@client.on(events.NewMessage(
  incoming=True,        # 받은 메시지
  # outgoing=True,      # 보낸 메시지
  # from_users=entity,  # 특정 user 로부터 받은 메시지 필터링
  # forwards=True,      # forward 된 메시지 필터링
  # pattern=r'\.save'   # 메시지 본문 매칭
  ))
  
# 1. handler의 매개변수인 event는 Message와 동일한 객체입니다.
async def handler(event):
  global item_count
  # 2. message 객체에서 필요한 필드를 추출합니다.
  try:
    # try:
    #   message_id = event.chat.id
    # except:
      
    if event.chat.id in channel_id_list:
      message_dict: dict = await extract_from(event)
      if (message_dict['has_photo'] or message_dict['has_document']):
        path,save_dir = mkdir_path(message_dict['channel_id'])
        file_path: str = await event.download_media(file=path)
        if ' ' in file_path:
          replace_file_path = file_path.replace(' ','_')
          mv_command = f"mv '{file_path}' '{replace_file_path}'" 
          logging.info(mv_command)
          os.system(mv_command)
          file_path = replace_file_path
        file_name = file_path.split("/")[-1]
        message_dict['file_path'] = f"{save_dir}/{file_name}"
        message_dict['file_name'] = file_name
      else:
        message_dict['file_path'] = None
        message_dict['file_name'] = None
      
      channel_info: dict = channel_dict[message_dict['channel_id']]
      channel_info['crawl_message_id'] = message_dict['message_id']
      dbclient57.insert_message(message_dict)
      dbclient58.insert_message(message_dict)
      dbclient57.update_channel_info(channel_info)
      dbclient58.update_channel_info(channel_info)
      rotation_logger.info(message_dict)
      item_count = item_count + 1
      #3600초 마다 send_message
      if util.time_check(cur_time,CHECK_TIME):
        send_cycle_message()
    else:
      rotation_logger.info(f"[CHANNEL_ID NOT IN] {event.chat.id} / {event.chat.username}")
  except Exception as e:
    logging.error('ERROR MESSAGE')
    logging.error(event)
    logging.error(traceback.format_exc())
    raise Exception('ERROR MESSAGE')
    

def mkdir_path(channel_id: str) -> str:
  cur_date: str = util.cur_day_str()
  date_path: str = f"{out_dir}/telegram_data/{cur_date}"
  if not os.path.isdir(date_path):
    os.mkdir(date_path)
  path: str = f"{date_path}/{channel_id}"
  if not os.path.isdir(path):
    os.mkdir(path)
  return f"{path}",f"telegram_data/{cur_date}/{channel_id}"

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


#atexit.register(_close())
#channel_info: dict = load_channel_info()
try:
  client.start()
  client.run_until_disconnected()  
finally:
  send_item = {'item_count':{"flag":"W","data":item_count,"error_range":"1/5"}}
  message.send_error_message('END PROGRAM',send_item)
  logging.info('END PROGRAM')
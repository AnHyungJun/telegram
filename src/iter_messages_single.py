from telethon import TelegramClient
from telethon import utils
from telethon import types
from telethon.sessions import StringSession
from datetime import datetime
#from extract_to_dict_copy import extract_from
from extract_to_dict import extract_from
from embedded_crawler import TelegramUrlProcessor
import json
import sys
import logging
import os
import time
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
COMMON_DIR = os.path.abspath(os.path.join(ROOT_DIR, "common"))
sys.path.insert(0, os.path.abspath(ROOT_DIR))
from send_message import KafkaHandler
import util
import atexit
# Logging


logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.INFO)

# Credentials
api_id = '27991267'
api_hash = '8dcb75ad0d21fb82c82cd86e7cf33581'
client: TelegramClient = TelegramClient('3086.session', api_id, api_hash)
embedded_client: TelegramUrlProcessor = TelegramUrlProcessor()
# api_id = '27991267'
# api_hash = '8dcb75ad0d21fb82c82cd86e7cf33581'
# client: TelegramClient = TelegramClient('3086.session', api_id, api_hash)
# api_id = '24231189'
# api_hash = 'a683b8e8c40c24029918efee71c8e968'
# client: TelegramClient = TelegramClient('3058.session', api_id, api_hash)
#channel_dict - channel_id,channel_name,crawl_message_i
channel_out_list: list = []
SAVE_DIR = './out'



def to_marked_channel_id(real_id: int) -> any:
  return utils.get_peer_id(types.PeerChannel(real_id))


def load_channel_info(path: str) -> list:
  # channel_list: list = list()
  with open(path) as f:
    return json.loads(f.read().strip())
  #   for line in f:
  #     channel_list.append(json.loads(line.strip()))
  # return channel_list

#async def main(channel_dict: dict):
async def main(channel_id: str, last_message_id: str):
    # channel_id = int(channel_dict['channel_id'])
    # 1. 수집 대상이 되는 채널 정보를 조회합니다.
    # v = to_marked_channel_id(channel_id)
    # #print (v)
    # channel = await client.get_entity(v)
    # print (channel)
    # async for message in client.iter_messages(channel, limit=1, offset_id=channel_dict['crawl_message_id'],reverse=True):
    #   # 3. message 객체에서 필요한 필드를 추출합니다.
    #   message_dict: dict = await extract_from(message)
    #   logging.info(message_dict['message_id'] )
    #   if (message_dict['has_photo'] or message_dict['has_document']):
    #     path,save_dir = mkdir_path(message_dict['channel_id'])
    #     #save_dir = f"{path}telegram_data/{cur_date}/{channel_id}"
    #     #file_path: str = await message.download_media(file=path)
    #     file_path: str = await message.download_media(file=save_dir)
    #     if ' ' in file_path:
    #       replace_file_path = file_path.replace(' ','_')
    #       mv_command = f"mv '{file_path}' '{replace_file_path}'" 
    #       os.system(mv_command)
    #       file_path = replace_file_path
    #     file_name = file_path.split("/")[-1]
    #     message_dict['file_path'] = f"{save_dir}/{file_name}"
    #     message_dict['file_name'] = file_name
    #   else:
    #     message_dict['file_path'] = None
    #     message_dict['file_name'] = None
    #   embedded_urls, url_metadata = embedded_client.extract_urls_and_metadata(message_dict["message"])
    #   message_dict["embedded_urls"] = embedded_urls
    #   message_dict["url_metadata"] = url_metadata
    #   with open(f'{SAVE_DIR}/telegram_message.json.{util.cur_day_str()}','a') as f:
    #     f.write(json.dumps(message_dict,ensure_ascii=False)+'\n')
    channel_id = int(channel_id)
    # 1. 수집 대상이 되는 채널 정보를 조회합니다.
    logging.info(channel_id)
    channel = await client.get_entity(to_marked_channel_id(channel_id))
    #channel = await client.get_entity(to_marked_channel_id(channel_id))
    #path = f"./out/downloads/{channel_dict['channel_id']}"
    #if not os.path.isdir(path):
    #  os.mkdir(path)
    # 2. iter_messages() API로 메시지 히스토리를 조회합니다.
    break_count = 0
    async for message in client.iter_messages(channel, limit=None, offset_id=int(last_message_id),reverse=True):
      # 3. message 객체에서 필요한 필드를 추출합니다.
      logging.info(message)
      if break_count >= 5:
        break 
      #try: 
      message_dict: dict = await extract_from(message)
      #except:
      #  logging.info(message)
      #  continue
      #logging.info(message_dict['message_id'] )
      if message_dict['message_id'] == str(channel_id):
        logging.info(f'finish crawl message{channel_id} : {message_dict["message_id"]}')
        break_count += 1
        continue
      # if message_dict['write_time'] < '2025-01-17 20:30:00' :
      #   continue
      if (message_dict['has_photo'] or message_dict['has_document']):
        path,save_dir = mkdir_path(message_dict['channel_id'])
        #save_dir = f"{path}telegram_data/{cur_date}/{channel_id}"
        #file_path: str = await message.download_media(file=path)
        file_path: str = await message.download_media(file=save_dir)
        if ' ' in file_path:
          replace_file_path = file_path.replace(' ','_')
          mv_command = f"mv '{file_path}' '{replace_file_path}'" 
          os.system(mv_command)
          file_path = replace_file_path
        file_name = file_path.split("/")[-1]
        message_dict['file_path'] = f"{save_dir}/{file_name}"
        message_dict['file_name'] = file_name
      else:
        message_dict['file_path'] = None
        message_dict['file_name'] = None
      embedded_urls, url_metadata = embedded_client.extract_urls_and_metadata(message_dict["message"])
      message_dict["embedded_urls"] = embedded_urls
      message_dict["url_metadata"] = url_metadata
      with open(f'{SAVE_DIR}/telegram_message.json.{util.cur_day_str()}','a') as f:
        f.write(json.dumps(message_dict,ensure_ascii=False)+'\n')
      time.sleep(1)
      


def mkdir_path(channel_id: str) -> str:
  cur_date: str = util.cur_day_str()
  date_path: str = f"{SAVE_DIR}/etc_file/{cur_date}"
  if not os.path.isdir(date_path):
    os.mkdir(date_path)
  path: str = f"{date_path}/{channel_id}"
  if not os.path.isdir(path):
    os.mkdir(path)
  return f"{path}",f"{SAVE_DIR}/etc_file/{cur_date}/{channel_id}"


# def mkdir_path(channel_id: str) -> str:
#   cur_date: str = util.cur_day_str()
#   date_path: str = f"{SAVE_DIR}/etc_file/{cur_date}"
#   if not os.path.isdir(date_path):
#     os.mkdir(date_path)
#   path: str = f"{date_path}/{channel_id}"
#   if not os.path.isdir(path):
#     os.mkdir(path)
#   return f"{path}",f"{SAVE_DIR}/etc_file/{cur_date}/{channel_id}"



# def _close(path: str) -> None:
#   with open(f'{path}.{util.cur_day_str()}','w') as f:
#     for channel in channel_out_list:
#       f.write(json.dumps(channel,ensure_ascii=False)+'\n')

if __name__ == '__main__':
    # 파일의 id와 last_message_id를 읽어와서 처리
    #channel_id: str = sys.argv[1]
    #channel_dict: dict = {channel_id:{"channel_name": None, "crawl_message_id": 62898, "url": None, "channel_id": channel_id}}
    #join_id = list()
  client.start()
  with open('/home/mining/user/data_updated.tsv') as f:
    for line in f:
      channel_id = line.strip().split('\t')[0]
      last_message_id = line.strip().split('\t')[1]
      client.loop.run_until_complete(main(channel_id, last_message_id))


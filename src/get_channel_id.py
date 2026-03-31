#텔레그렘 방에 들어가는 프로그램
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from datetime import datetime
import time
from telethon import types
from telethon import utils
import json,os,sys
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, os.path.abspath(ROOT_DIR))

import util
# Telegram API 정보
api_id: str = '26473415'
api_hash: str = 'c4117337c10cd35735cccbd5edd44829'
# 세션 파일 경로
session_file: str = 'my_session.session'
cur_day: str = util.cur_day_str()
# 채널 URL 또는 username 목록
new_channel_list = list()
# with open('./etc/new') as f:
#     for line in f:
#         d = line.strip()
#         new_channel_list.append(d)

async def join_channels(client: TelegramClient) -> None:
    try:
        # 세션 로그인 시도
        await client.start()
        with open(f'./etc/channel_list.{cur_day}.json') as f:
            channel_info = json.loads(f.read())
        new_channel_list = ['https://t.me/crebalinfo']
        # 채널에 참여
        for channel_url in new_channel_list:
            #print (channel_url)
            #channel_url = 'https://bit.ly/2nKHlh6'
            #cccc = utils.get_peer_id(types.PeerChannel(1453441728))
            #print (cccc)
            entity: any = await client.get_entity(channel_url)
            #print (channel_url)
            print (entity.id)
            # if str(entity.id) not in channel_info:
            #     print (f'@{str(channel_url)}')
            #     channel_info[str(entity.id)] = {
            #         'channel_name': entity.title,
            #         'last_message_id': None,
            #         'url': channel_url
                    
            #     }
            #     print (entity.title)
            #await client(JoinChannelRequest(entity))
            time.sleep(5)
    except Exception as e:
        print(f"Error: {e}")

    finally:
        # 세션 저장 및 닫기
        await client.disconnect()
        channel_info_file = open('./config/channel_test.json','w')
        channel_info_file.write(json.dumps(channel_info, ensure_ascii=False))
        channel_info_file.close()

# 비동기로 실행
client: TelegramClient = TelegramClient('anon', api_id, api_hash)
client.loop.run_until_complete(join_channels(client))
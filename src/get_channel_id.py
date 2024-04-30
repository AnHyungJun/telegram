#텔레그렘 방에 들어가는 프로그램
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
import time
import json
# Telegram API 정보
api_id: str = '26473415'
api_hash: str = 'c4117337c10cd35735cccbd5edd44829'
# 세션 파일 경로
session_file: str = 'my_session.session'

# 채널 URL 또는 username 목록
channel_list = list()
with open('./etc/channel_list.txt') as f:
    for line in f:
        channel_list.append(line.strip())
channel_list = ['https://t.me/+Lqv878nsRzoyODU1']
async def join_channels(client: TelegramClient) -> None:
    try:
        # 세션 로그인 시도
        await client.start()
        # with open('./config/channel_info.json') as f:
        #     channel_info = json.loads(f.read())
        
        # 채널에 참여
        for channel_url in channel_list:
            
            entity: any = await client.get_entity(channel_url)
            #print (channel_url)
            print (entity)
            # if str(entity.id) not in channel_info:
            #     channel_info[str(entity.id)] = {
            #         'channel_name': entity.title,
            #         'last_message_id': None,
            #         'url': channel_url
                    
            #     }
            #     print (entity.title)
            #await client(JoinChannelRequest(entity))
            time.sleep(10)
            #break
    except Exception as e:
        print(f"Error: {e}")

    finally:
        # 세션 저장 및 닫기
        await client.disconnect()
        # channel_info_file = open('./config/channel_test.json','w')
        # channel_info_file.write(json.dumps(channel_info, ensure_ascii=False))
        # channel_info_file.close()

# 비동기로 실행
client: TelegramClient = TelegramClient('anon', api_id, api_hash)
client.loop.run_until_complete(join_channels(client))
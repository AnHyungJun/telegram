#텔레그렘 방에 들어가는 프로그램
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
import time
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
async def join_channels(client: TelegramClient) -> None:
    try:
        # 세션 로그인 시도
        await client.start()

        # 채널에 참여
        for channel_url in channel_list:
            print (channel_url)
            entity: any = await client.get_entity(channel_url)
            try:
                await client(JoinChannelRequest(entity))
            except Exception as e:
                print (f'ERROR {channel_url} : {e}')
            time.sleep(20)
    except Exception as e:
        print(f"Error: {e}")

    finally:
        # 세션 저장 및 닫기
        await client.disconnect()


        
# 비동기로 실행
client: TelegramClient = TelegramClient('anon', api_id, api_hash)
client.loop.run_until_complete(join_channels(client))
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
with open('./config/channel_info.json') as f:
    # for line in f:
    #     channel_list.append(line.strip())
    b = json.loads(f.read().strip())
    for k,v in b.items():
        v['channel_id'] = k
        channel_list.append(v)

with open('f.json','w') as f:
    for line in channel_list:
        
        f.write(json.dumps(line, ensure_ascii=False)+'\n')
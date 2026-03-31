import json
import sys


date_str = sys.argv[1]  # 예시: 실제로는 원하는 날짜 문자열로 설정

# 기존 JSON 파일 불러오기
with open(f"channel_list.{date_str}.json") as f:
    channels = json.loads(f.readline().strip())

# TSV 파일 읽어서 추가
with open('add_channel.tsv', encoding='UTF-8-SIG') as f:
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) != 2:
            continue  # 형식이 잘못된 줄은 무시
        channel_id_str, channel_name = parts
        try:
            channel_id = int(channel_id_str)
        except ValueError:
            continue  # channel_id가 숫자가 아니면 무시

        # 이미 존재하면 pass
        if str(channel_id) in channels:
            continue

        # 없으면 추가
        print (channel_name)
        channels[str(channel_id)] = {
            "channel_id": channel_id,
            "channel_name": channel_name,
            "crawl_message_id": None
        }

# 결과 저장 (덮어쓰기)
with open(f"channel_list.aaaaaa.json", 'w') as f:
    json.dump(channels, f, ensure_ascii=False)

print("추가 완료!")


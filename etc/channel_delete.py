import json
import sys
date_str = sys.argv[1]  # 예시: 실제로는 원하는 날짜 문자열로 설정

# 기존 JSON 파일 불러오기
with open(f"channel_list.{date_str}.json") as f:
    channels = json.loads(f.readline().strip())

# TSV 파일 읽어서 제거
with open('delete.tsv', encoding='UTF-8-SIG') as f:
    for line in f:
        #print (line)
        channel_id_str = line.strip()
        try:
            a = channels.pop(channel_id_str,None)
            print (a)
        except:
            pass
# 결과 저장 (덮어쓰기)
with open(f"channel_list.aaaaaa.json", 'w') as f:
    json.dump(channels, f, ensure_ascii=False)

print("삭제 완료!")


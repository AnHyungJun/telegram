import requests
import json
import sys
import os
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
COMMON_DIR = os.path.abspath(os.path.join(ROOT_DIR, "common"))
sys.path.insert(0, os.path.abspath(ROOT_DIR))


class KafkaHandler:
    
    def __init__(self,token_path: str=f'{ROOT_DIR}/config/kafka_token'):
        self.reqeust_header = self.get_header(token_path)
    
    def get_header(self,token_path: str) -> dict:
        with open(token_path) as f:
            token = f.read().strip()
        headers = {
            'accept': 'application/json',
            'Authorization': f'Bearer {token}'
            }
        return headers
    
    def send_kafka(self,item: dict):
        url = 'http://112.175.32.5:8245/v1/internal/write/data/dip_telegram'
        form_data = {
            "value": item
            }
        
        return requests.post(url=url,headers=self.reqeust_header,data=json.dumps(form_data))
    
if __name__ == "__main__":
    c = KafkaHandler()
    with open('/locdisk/telegram_data/lose_data') as f:
        for line in f:
            c.send_kafka(json.loads(line.strip()))
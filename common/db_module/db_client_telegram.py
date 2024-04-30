'''
@author : ahj
@create_date : 2024-02-07
--------------------------------
@history
'''
import sys,os,logging,json
from datetime import datetime,timedelta
from typing import List,Any,Final
import inspect
CURRENT_DIR:str = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.insert(0, CURRENT_DIR)
from db_client import OracleClient


class BaseDBClient(OracleClient):

    def __init__(self,db_config_file: str=f'{CURRENT_DIR}/db_config/oracle_sample.ini', max_retry: int = 3):
        super(BaseDBClient, self).__init__(db_config_file, max_retry)
    
    def insert_channel_info(self,item:dict) -> None:
        table_name:str = 'TELEGRAM_CHANNEL'
        item['channel_id'] = int(item['channel_id'])
        item['crawl_message_id'] = item.pop('last_message_id')
        item['channel_url'] = item.pop('url')
        query = self.make_insert_query(item,table_name)
        logging.info(query)
        self._set(query)
    
    def update_channel_info(self,item:dict) -> None:
        table_name:str = 'TELEGRAM_CHANNEL'
        query = self.make_insert_query(item,table_name)
        logging.info(query)
        self._set(query)
        
    def __del__(self):
        self._close()



if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    db_config_file = sys.argv[1]
    b: BaseDBClient = BaseDBClient(db_config_file)
    query = 'select * from TELEGRAM_CHANNEL'
    print (query)
    print (b._get(query))
    with open('../../config/channel_info.json') as f:
        for line in f:
            channel_dict: dict = json.loads(line.strip())
            b.insert_channel_info(channel_dict)
            
    b._close()
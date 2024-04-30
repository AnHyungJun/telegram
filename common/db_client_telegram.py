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
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, CURRENT_DIR)
from db_module.db_client import OracleClient


class TelegramDBClient(OracleClient):

    def __init__(self,db_config_file: str=f'{SCRIPT_DIR}/db_config/telegram57.ini', max_retry: int = 3):
        super(TelegramDBClient, self).__init__(db_config_file, max_retry)
    
    def insert_channel_info(self,item:dict) -> None:
        table_name:str = 'TELEGRAM_CHANNEL'
        #item['channel_id'] = item.pop('channel_id')
        item['crawl_message_id'] = item.pop('last_message_id')
        item['channel_url'] = item.pop('url')
        query = self.make_insert_query(item,table_name)
        logging.info(query)
        self._set(query)
    
    
    def insert_message(self,item:dict) -> None:
        table_name:str = 'TELEGRAM_MESSAGE'
        message = item['message']
        item['message'] = self.str_to_clob(message)
        for k,v in item.items():
            if v is True:
                item[k] = 'T'
            elif v is False:
                item[k] = 'F'
        #upper_dict = {f'"{key}"': value for key, value in item.items()}
        
        
        query = self.make_insert_query(item,table_name)
        logging.info(query)
        _check = self._set(query)
        if not _check:
            item['message'] = message
            logging.error('DB INSERT ERROR')
            logging.error(item)
            with open(f"{ROOT_DIR}/etc/error.message.json",'a') as f:
                f.write(json.dumps(item,ensure_ascii=False))
    
    def update_channel_info(self,item:dict) -> None:
        table_name: str = 'TELEGRAM_CHANNEL'
        #update_dict = {f'"{key}"': value for key, value in item.items()}
        #update_dict = {f'"{key.upper()}"': value for key, value in item.items()}
        item['update_date'] = datetime.now().strftime('%Y%m%d%H%M%S')
        update_fields: list = ['update_date','crawl_message_id']
        where_query: str = ' channel_id = {}'.format(item['channel_id'])
        query: str = self.make_update_query(item, table_name, update_fields,where_query)
        logging.info(query)
        self._set(query)

    def select_channel_info(self) -> dict:
        table_name: str = 'TELEGRAM_CHANNEL'
        query = f'select * from {table_name}'
        channel_info_list:list = self._get(query)
        channel_dict: dict = dict()
        for channel in channel_info_list:
            #logging.info(channel)
            item = dict(
                channel_id=channel['CHANNEL_ID'],
                channel_name=channel['CHANNEL_NAME'],
                crawl_message_id=channel['CRAWL_MESSAGE_ID']
            )
            channel_dict[channel['CHANNEL_ID']] = item
        
        return channel_dict
        
    def __del__(self):
        self._close()



if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    #db_config_file = sys.argv[1]
    b: TelegramDBClient = TelegramDBClient()
    
    with open(f"{ROOT_DIR}/etc/channel_info.{datetime.now().strftime('%Y%m%d%H%M%S')}.json",'w') as f:
        f.write(json.dumps(b.select_channel_info(),ensure_ascii=False))
    
    #print (query)
    b._close()

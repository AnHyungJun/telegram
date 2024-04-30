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
import subprocess
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
        #item['crawl_message_id'] = item.pop('last_message_id')
        #item['channel_url'] = item.pop('url')
        query = self.make_insert_query(item,table_name)
        logging.info(query)
        self._set(query)
    
    
    def insert_message(self,item:dict) -> None:
        table_name:str = 'TELEGRAM_MESSAGE'
        item['MESSAGE'] = self.str_to_clob(item['MESSAGE'])
        #upper_dict = {f'"{key}"': value for key, value in item.items()}
        
        
        query = self.make_insert_query(item,table_name)
        logging.info(query)
        #self._set(query)
    
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
            item = dict(
                channel_id=channel['channel_id'],
                channel_name=channel['channel_name'],
                crawl_message_id=channel['crawl_message_id']
            )
            channel_dict[channel['channel_id']] = item
        
        return channel_dict
        
    def __del__(self):
        self._close()



if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    #db_config_file = sys.argv[1]
    b: TelegramDBClient = TelegramDBClient()
    c: TelegramDBClient = TelegramDBClient(f'{SCRIPT_DIR}/db_config/telegram58.ini')
    query = 'select * from TELEGRAM_MESSAGE where channel_id=1479376547 and message_id=73318'
    hh = b._get(query)
    with open('message.json','w') as f:
        for ll in hh:
            logging.info(ll)
            try:
                ll['MESSAGE'] = ll['MESSAGE'].read()
            except:
                ll['MESSAGE'] = ''
            f.write(json.dumps(ll,ensure_ascii=False)+'\n')
    # with open('channel_info.json') as f:
    #     jjj = json.loads(f.read())
    #     for line in jjj:
    #         b.insert_channel_info(line)
    #         c.insert_channel_info(line)
    # with open('channel_message.json') as f:
        
    #     for line in f:
    #         jjj = json.loads(line.strip())
    #         b.insert_message(jjj)
    #         c.insert_message(jjj)
    # c = '/home/mining/crawler/finance/telegram_crawler/'
    
    with open('message.json') as f:
        for line in f:
            json_data = json.loads(line.strip())
            message = json_data['MESSAGE']
            channel_id = str(json_data['CHANNEL_ID'])
            message_id = str(json_data['MESSAGE_ID'])
            query = f"update TELEGRAM_MESSAGE set message={b.str_to_clob(message)} where channel_id={channel_id} and message_id={message_id}"
            logging.info(query)
            b._set(query)
            c._set(query)
            #logging.info(b.str_to_clob(json_data['MESSAGE']))
            # if json_data['FILE_PATH'] :
            #     e_file = json_data['FILE_PATH'].replace('/cluster/disk1/financial_crawled_data/','')
            #     #date_str = json_data['WRITE_TIME'].split(' ')[0].replace('-','')
            #     channel_id = str(json_data['CHANNEL_ID'])
            #     message_id = str(json_data['MESSAGE_ID'])
            #     file_name = json_data['FILE_NAME'].replace(' ','_')
            #     #e_file = f'/cluster/disk1/financial_crawled_data/telegram_data/{date_str}/{channel_id}/{file_name}'
            #     query = f"update TELEGRAM_MESSAGE set file_path='{e_file}' where channel_id='{channel_id}' and message_id='{message_id}'"
            #     logging.info(query)
            #     b._set(query)
            #     c._set(query)
            
    #cursor.setinputsizes(clob_column=cx_Oracle.CLOB)
    #cursor.execute(sql_insert, {'clob_column': long_data})
    
         
        #     json_data = json.loads(line.strip())
        #     if json_data['FILE_PATH'] :
        #         ori_file = c + json_data['FILE_PATH']
        #         date_str = json_data['WRITE_TIME'].split(' ')[0].replace('-','')
        #         channel_id = str(json_data['CHANNEL_ID'])
        #         file_name = json_data['FILE_NAME']
        #         e_file = f'/cluster/disk1/financial_crawled_data/telegram_data/{date_str}/{channel_id}/{file_name}'
                
        #         if not os.path.isdir(f'/cluster/disk1/financial_crawled_data/telegram_data/{date_str}'):
        #             os.mkdir(f'/cluster/disk1/financial_crawled_data/telegram_data/{date_str}')
        #         if not os.path.isdir(f'/cluster/disk1/financial_crawled_data/telegram_data/{date_str}/{channel_id}'):
        #             os.mkdir(f'/cluster/disk1/financial_crawled_data/telegram_data/{date_str}/{channel_id}')
        #         #logging.info(f"mv {ori_file} {e_file}" )
        #         e_file = e_file.replace(' ','_')
        #         if channel_id == '1080519355':
        #             try:
        #                 logging.info(f"mv '{ori_file}' '{e_file}'" )
        #                 os.system(f"mv '{ori_file}' '{e_file}'" )
        #             except Exception as e:
        #                 import traceback
        #                 logging.error(traceback.format_exc())
        #                 logging.error(ori_file) 
    b._close()
    c._close()
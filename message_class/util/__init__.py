import pprint
import json
from datetime import datetime,timedelta
from pathlib import Path

def print_json_message(item:dict) -> None:
    print(json.dumps(item,indent=4))

def datetime_to_str(_time:datetime,cv_format:str='%Y-%m-%d %H:%M:%S') -> str:
    return datetime.strftime(_time,cv_format)

def str_to_datetime(_time_str:str,cv_format:str='%Y-%m-%d %H:%M:%S') -> datetime:
    return datetime.strptime(_time_str,cv_format)

#json data file저장
def json_save_file(save_dir:str='./',file_name:str='test.json',item:dict={}) -> None:
    p = Path(save_dir)
    p.mkdir(parents=True, exist_ok=True)
    filepath = p / file_name
    with filepath.open("w", encoding ="utf-8") as f:
        f.write(json.dumps(item, indent=4)+'\n')

#오늘날짜 get
def cur_day_str(date_format='%Y%m%d') -> str:
    return datetime.now().strftime(date_format)

#시간 계산
def cal_elapsed_time(start_time,end_time = datetime.now()) -> timedelta:
    if isinstance(start_time,str):
        start_time = str_to_datetime(start_time)
    if isinstance(end_time,str):
        end_time = str_to_datetime(end_time)
    crawl_time = end_time - start_time
    return crawl_time

def time_check(tmp_time:datetime,check_time:int) -> bool:
    now = datetime.now()
    if (now - tmp_time).seconds >= check_time:
        return True
    else:
        return False

def json_to_str(json_data:dict,sep='::',date_format='%Y-%m-%dT%H:%M:%S') -> str:
    result_str:list = []
    for k,v in json_data.items():
        if isinstance(v,int):
            v = str(v)
        elif isinstance(v,datetime):
            v = datetime_to_str(v,date_format)
        elif isinstance(v,list):
            v = ', '.join(v)
        elif isinstance(v,dict):
            v = json.dumps(v)
        one_line = ' '.join([k,sep,v])
        result_str.append(one_line)
    return '\n'.join(result_str) 

def process_time(fun) -> str:
    logging.info(f'{fun.__name__} time :: {datetime.now()}')

def pop_field(item:dict,keys:list) -> dict:
    result_dict = dict()
    for key in keys:
        result_dict[key] = item.pop(key) 
    return result_dict
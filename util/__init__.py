import json
from datetime import datetime,timedelta
from pathlib import Path
from typing import Any
import pytz
from dateutil.parser import parse
#json print
def pretty_json(item: dict[Any,Any]) -> None:
    print(json.dumps(item,indent=4))

#datetime -> str
def datetime_to_str(_time: datetime, _format: str='%Y-%m-%d %H:%M:%S') -> str:
    return datetime.strftime(_time,_format)

#str -> datetime
def str_to_datetime(time_str: str, _format: str='%Y-%m-%d %H:%M:%S') -> datetime:
    return datetime.strptime(time_str,_format)

#json data file저장
def json_save_file(save_dir: str='./', file_name: str='test.json', item: dict={}, pretty: bool=False) -> None:
    p = Path(save_dir)
    p.mkdir(parents=True, exist_ok=True)
    filepath = p / file_name
    if pretty:
        with filepath.open("w", encoding ="utf-8") as f:
            f.write(json.dumps(item,indent=4)+'\n')
    else:
        with filepath.open("w", encoding ="utf-8") as f:
            f.write(json.dumps(item)+'\n')

#현재시간을 date_format에 맞게 string return
def cur_day_str(date_format:str='%Y%m%d') -> str:
    return datetime.now().strftime(date_format)

#end_time - start_time
def cal_elapsed_time(start_time: datetime|str,end_time: datetime = datetime.now()) -> timedelta:
    if isinstance(start_time,str):
        start_time = str_to_datetime(start_time)
    if isinstance(end_time,str):
        end_time = str_to_datetime(end_time)
    crawl_time = end_time - start_time
    return crawl_time

#start_time이 check_time을 넘어갈 경우 False 
def time_check(start_time: datetime, check_time: int) -> bool:
    cur_time: datetime = datetime.now()
    if (cur_time - start_time).seconds >= check_time:
        return True
    else:
        return False

#여러개의 key를 한번에 dict로 pop
def pop_field(item: dict[str,Any],keys: list[str]) -> dict:
    result_dict: dict[str,Any] = dict()
    for key in keys:
        result_dict[key] = item.pop(key) 
    return result_dict

#timezone 컨버터
def convert_timezone(input_datetime: datetime, from_local: str='America/New_York', to_local: str='Asia/Seoul'):
    # 입력된 datetime 객체에 원래 timezone을 설정합니다.
    from_timezone: Any = pytz.timezone(from_local)
    to_timezone: Any = pytz.timezone(to_local)
    input_datetime: datetime = from_timezone.localize(input_datetime)
    # 원하는 timezone으로 변환합니다.
    output_datetime: datetime = input_datetime.astimezone(to_timezone)
    return output_datetime

if __name__ == "__main__":
    #print (cal_elapsed_time(datetime.now()))
    #print (pop_field({},[]))
    #print (print_json_message({'a':1}))
    print (convert_timezone(datetime.now()))
    pass

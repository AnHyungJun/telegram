from datetime import datetime
from schematics.models import Model
from schematics.types import StringType,IntType,ListType,ModelType,DictType,BooleanType


class BaseMessage(Model):
    spider_name = StringType(required=True) # 수집기 종류
    project_name = StringType(required=True) # 수집 프로젝트
    process_num = IntType(default=0) #멀티프로세스 번호
    message = StringType(default='')
    crawl_start_time = StringType(default=datetime.strftime(datetime.now(),'%Y-%m-%d %H:%M:%S')) # 수집 시작 시간 YYYY-mm-ddTHH:MM:SS
    message_type = StringType(choices=['SUCCESS','ERROR','EME_ERROR']) # 장애 없을시,에러인지 SUCCESS|ERROR|EME_ERROR
    db_save_flag = BooleanType(default=True)
    slack_send_flag = BooleanType(default=True)
    sms_send_flag = BooleanType(default=False)

#파일 비교가 필요한 field DateModel
class Checkfield(Model):
    flag = StringType(default='N',choices=['N','W','M','D']) #데이터 비교 범위 N:비교 X W:1주일 M:1달 D:1일
    data = IntType()
    error_range = StringType(default='1/2') # 분수 형식의 데이터
    
class ExtendMessage(BaseMessage):

    data_size = ModelType(Checkfield) #수집 데이터 용량
    response_count = ModelType(Checkfield) # response 수
    crawl_end_time = StringType() 
    elapsed_time = IntType() # 수집 시간  crawl_start_time - crawl_end_time
    item_count = ModelType(Checkfield) #수집 아이템 수
    status_code = DictType(IntType) #status code ex) {'200':10,'302':15}
    log_error_count = IntType(default=0) # error 수
    validation_error_list = ListType(StringType) #임시 데이터 ['item_error','status_error',.....]
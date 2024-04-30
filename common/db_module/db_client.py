'''
@author : ahj
@create_date : 2024-02-07
--------------------------------
@history
'''
import os
import logging
from datetime import datetime
import re
import pymysql
import cx_Oracle
import json
from configparser import ConfigParser,NoSectionError
from typing import Any,Final,Optional
from abc import ABC,abstractmethod

COMMIT_INTERVAL: Final[int] = 60


class CustomConfigParser(ConfigParser):

    def __init__(self,config_file: str) -> None:
        super().__init__()
        self.read(config_file)

    def get_section(self, section: str, default_section: dict={}) -> dict:
        try:
            item: dict = self.process_values(dict(self.items(section)))      
            return item
        except NoSectionError:
            return default_section
    
    def process_values(self,item: dict[str,str]) -> dict:
        for k,v in item.items():
            v = self.value_return(v)
            item[k] = v
        return item
    
    def value_return(self,value: str) -> str|int|bool:
        if value.isnumeric():
            return int(value)
        elif value.upper() in ('TRUE','T'):
            return True
        elif value.upper() in ('FALSE','F'):
            return False
        else:
            return value

class DBClient(ABC):
    '''MariaDBClient 및 OracleDBClient 의 부모 class'''

    def __init__(self, db_conf_file: str, max_retry: int=3, connection_type: str='SERVICE_NAME') -> None:
        db_conf: CustomConfigParser = CustomConfigParser(db_conf_file)
        self.config: dict = db_conf.get_section('DB_INFO')
        self.max_retry: int = max_retry
        self.conn: Any = None
        self.connection_type: str = connection_type
        self._connect()

    def __del__(self) -> None:
        self._close()

    def _close(self) -> None:
        if self.conn:
            logging.info('DB CLOSE')
            self.conn.commit()
            self.conn.close()
            self.conn = None

    def _reconnect(self) -> None:
        self._close()
        self._connect()
    
    @abstractmethod
    def _connect(self) -> None:
        pass
    
    # 데이터를 받아오는 쿼리 처리
    @abstractmethod
    def _get(self, query: str) -> tuple|list:
        pass
    
    # update,insert 같은 쿼리 처리
    @abstractmethod
    def _set(self, query: str) -> bool:
        pass
    
    def str_to_clob(self, text: str) -> str:
        clob_text: str = ""
        split_text: list[str] = re.split('\s', text)
        for i in range(len(split_text) / 50 + 1):
            sub_text: str = " ".join(split_text[50 * i:50 * (i + 1)]).replace("'", "`")
            clob_text: str = clob_text + f"to_clob('{sub_text}') || "
        return clob_text[:-4]
   
    # scrapy item 인스턴스(혹은 dict)로부터 insert query를 생성해주는 유틸리티 함수
    # ignore_flag : '' or 'IGNORE'
    def make_insert_query(self, item: dict, table_name: str, ignore_flag: str='') -> str:
        keys: list[str] = sorted(item.keys())
        values: list[str] = map(lambda k: self.value2str(item[k]), keys)
        return f'INSERT {ignore_flag} INTO {table_name} ( {", ".join(keys)} ) VALUES ( {", ".join(values)} )'
    
    
    def value2str(self, v: Any) -> str:
        if v is None:
            return "NULL"
        elif isinstance(v, (int, float)):
            return str(v)
        elif isinstance(v, str):
            if 'to_clob' in v :
                return v
            else :
                v: str = v.replace("'", "`")
                return f"'{v}'"
        elif isinstance(v, datetime):
            return datetime.strftime(v, "'%Y-%m-%d %H:%M:%S'")
        else:
            raise Exception(f'[make_insert_query] unknown value type ::: {str(type(v))}, {str(v)}')


class MysqlDBClient(DBClient):
    '''Mysql DB 용 클라이언트'''

    # for new connection
    def _connect(self) -> None:
        self.last_commit_time: datetime = datetime.now()
        try:
            self.conn: pymysql.connections.Connection = pymysql.connect(**self.config)
            logging.info('DB OPEN')
        except:
            self.conn = None
            err_config = json.dumps(self.config)
            logging.error(f'db connection failed :: {err_config}')
            raise Exception('db connection failed')

    # for select, show, ...
    def _get(self, query: str) -> list[dict]:
        for retry in range(self.max_retry):
            with self.conn.cursor(pymysql.cursors.DictCursor) as cur:
                try:
                    cur.execute(query)
                    return cur.fetchall()
                except pymysql.err.OperationalError as e:
                    # reconnect and try again
                    logging.warn(f'[OperationalError] {str(e)}')
                except Exception as e:
                    # no retry
                    logging.error(f'[SelectError] {str(e)}')
                    return []
            # reconnect and try again
            self._reconnect()
        # when failed up to max_retry
        logging.error('too many retry during select')
        return []

    # for insert, update, ...
    def _set(self, query: str) -> bool:
        for retry in range(self.max_retry):
            with self.conn.cursor() as cur:
                try:
                    cur.execute(query)
                    now: datetime = datetime.now()
                    if (now - self.last_commit_time).seconds >= COMMIT_INTERVAL:
                        self.last_commit_time: datetime = now
                        self.conn.commit()
                    return True
                except pymysql.err.OperationalError as e:
                    # reconnect and try again
                    logging.warn(f'[OperationalError] {str(e)}')
                except pymysql.err.IntegrityError as e:
                    # no retry
                    logging.warn(f'[IntegrityError] {str(e)}')
                    return False
                except Exception as e:
                    # no retry
                    logging.error(f'[ExecuteError] {str(e)}')
                    return False
            # reconnect and try again
            self._reconnect()
        # when failed up to max_retry
        logging.error('too many retry during execute')
        return False
    
    def make_update_query(self, item: dict, table_name: str, update_fields: list[str],where_query: str='') -> str:
        update_query: str = self.make_update_list(item,update_fields)
        if where_query != '' :
            where_query = f' WHERE {where_query}'
        query: str = f'UPDATE {table_name} SET {update_query}{where_query};'
        return query
    
    def make_merge_query(self, item, table_name, update_fields) -> str:
        query: str = f'{self.make_insert_query(item, table_name)} on duplicate key update '
        update_query: str = self.make_update_list(item,update_fields)
        return query + update_query

    def make_update_list(self, item: dict, update_fields: list[str]) -> str:
        #['key = value','key = value',....]
        update_list: list[str] = map(lambda x: f"{x} = {self.value2str(item[x])}", update_fields)
        update_query: str = ', '.join(update_list)
        return update_query


class OracleClient(DBClient):
    '''Oracle DB 용 클라이언트'''

    # for new connection
    def _connect(self) -> None:
        self.last_commit_time: datetime = datetime.now()
        if self.connection_type == 'SERVICE_NAME': #SERVICE_NAME or SID
            dsn_tns: str = cx_Oracle.makedsn(self.config['ip'], self.config['port'], service_name=self.config['db'])
        else:
            dsn_tns: str = cx_Oracle.makedsn(self.config['ip'], self.config['port'], sid=self.config['db'])
        try:
            self.conn: cx_Oracle.Connection = cx_Oracle.connect(self.config['user'], self.config['password'], dsn_tns)
            logging.info('DB OPEN')
        except Exception as e:
            self.conn = None
            logging.error(f'db connection failed :: {json.dumps(self.config)}')
            raise Exception('db connection failed')

    # for select, show, ...
    def _get(self, query: str) -> list:
        for retry in range(self.max_retry):
            try:
                cur: cx_Oracle.Cursor = self.conn.cursor()
                cur.execute(query)
                rows: list = cur.fetchall()
                cols: list = list(map(lambda x: x[0], cur.description))
                cur.close()
                return list(map(lambda row: dict(zip(cols, row)), rows))
            except Exception as e:
                # no retry
                logging.error(f'[SelectError] {str(e)}')
                cur.close()
                return []
        # when failed up to max_retry
        logging.error('too many retry during select')
        return []

    # for insert, update, ...
    def _set(self, query: str) -> bool:
        for retry in range(self.max_retry):
            try:
                cur: cx_Oracle.Cursor = self.conn.cursor()
                cur.execute(query)
                now: datetime = datetime.now()
                if (now - self.last_commit_time).seconds >= COMMIT_INTERVAL:
                    self.last_commit_time: datetime = now
                    self.conn.commit()
                cur.close()
                return True
            except Exception as e:
                # no retry
                logging.error(f'[ExecuteError] {str(e)}')
                cur.close()
                return False
        # when failed up to max_retry
        logging.error('too many retry during execute')
        return False
    
    def execute_many(self,sql: str, data: list) -> bool:
        for retry in range(self.max_retry):
            try:
                cur: cx_Oracle.Cursor = self.conn.cursor()
                cur.prepare(sql)
                cur.executemany(None, data)
                self.conn.commit()
                cur.close()
                return True
            except Exception as e:
                # no retry
                import traceback
                traceback.print_exc()
                logging.error(f'[ExecuteError] {str(e)}')
                cur.close()
                return False

    def make_many_insert_query(self, fields: list[str], table_name: str) -> str:
        #INSERT INTO table_name ( a, b, c ) VALUES ( :a, :b, :c )
        values: map[str] = map(lambda k: f':{k}', fields)
        return f"INSERT INTO {table_name} ( {', '.join(fields)} ) VALUES ( {', '.join(values)} )"
    
    #MERGE INTO table_name USING DUAL ON (a=b and c=d) WHEN MATCHED THEN UPDATE SET a = 20 .. WHEN NOT MATCHED THEN INSERT (a,c) value (h,h)
    def make_merge_query(self, item: dict, table_name: str, pk_fields: list, update_fields: list=[]) -> str:
        def make_merge_insert_query(item: dict) -> str:
            keys: list[str] = sorted(item.keys())
            values: map[Any] = map(lambda k: self.value2str(item[k]), keys)
            return f"INSERT ( {', '.join(keys)} ) VALUES ( {', '.join(values)} )"
        def make_lamdajoin_query(item: dict, fields: list, seq: str) -> str:
            return f' {seq} '.join(map(lambda x: f'{x} = {self.value2str(item[x])}', fields))
        
        merge_query: str = f'MERGE INTO {table_name} USING DUAL ON ( {make_lamdajoin_query(item,pk_fields,"AND")} ) ' 
        not_matched_query: str = f' WHEN NOT MATCHED THEN {make_merge_insert_query(item)}'
        
        if update_fields:
            matched_query: str = f' WHEN MATCHED THEN UPDATE SET {make_lamdajoin_query(item,update_fields,",")}'
            return merge_query + matched_query + not_matched_query
        else:
            return merge_query + not_matched_query

#async로 추가 개발 필요
class OracleClientPool(OracleClient):
    '''Oracle Pool DB 용 클라이언트'''
    
    def __init__(self, db_conf_file: str, max_retry: int=3, connection_type: str='SERVICE_NAME',\
        pool_config: dict={ "_min":2, "_max":10, "_increment":1}) -> None:
        db_conf: CustomConfigParser = CustomConfigParser(db_conf_file)
        self.config: dict = db_conf.get_section('DB_INFO')
        self.max_retry: int = max_retry
        self.connection_type: str = connection_type
        self.pool_config: dict = pool_config
        self.pool: cx_Oracle.SessionPool = self._connect()
        
    # for new connection
    def _connect(self) -> cx_Oracle.SessionPool:
        self.last_commit_time: datetime = datetime.now()
        if self.connection_type == 'SERVICE_NAME': #SERVICE_NAME or SID
            dsn_tns: str = cx_Oracle.makedsn(self.config['ip'], self.config['port'], service_name=self.config['db'])
        else:
            dsn_tns: str = cx_Oracle.makedsn(self.config['ip'], self.config['port'], sid=self.config['db'])

        try:
            logging.info('DB POOL OPEN')
            return cx_Oracle.SessionPool(user=self.config['user'], password=self.config['password'],
                             dsn=dsn_tns, min=self.pool_config['_min'],
                             max=self.pool_config['_max'], increment=self.pool_config['_increment'])
        except Exception as e:
            self.conn = None
            logging.error(f'db connection failed :: {json.dumps(self.config)}')
            raise Exception('db connection failed')
        
    def _poolcall(self) -> cx_Oracle.Connection:
        return self.pool.acquire()

    def _poolrelease(self,conn: cx_Oracle.Connection) -> None:
        if conn:
            self.pool.release(conn)

    def _close(self) -> None:
        if self.pool:
            self.pool.close(force = True)
            self.pool = None
        logging.info('DB POOL CLOSE')

    def _reconnect(self) -> None:
        self._close()
        self.pool: cx_Oracle.SessionPool = self._connect()
    
        # for select, show, ...
    def _get(self, query: str, conn: cx_Oracle.Connection) -> list:
        for retry in range(self.max_retry):
            try:
                cur: cx_Oracle.Cursor = conn.cursor()
                cur.execute(query)
                rows: list = cur.fetchall()
                cols: list = list(map(lambda x: x[0], cur.description))
                cur.close()
                return list(map(lambda row: dict(zip(cols, row)), rows))
            except Exception as e:
                # no retry
                logging.error(f'[SelectError] {str(e)}')
                cur.close()
                return []
        # when failed up to max_retry
        logging.error('too many retry during select')
        return []

    # for insert, update, ...
    def _set(self, query: str, conn: cx_Oracle.Connection) -> bool:
        for retry in range(self.max_retry):
            try:
                cur: cx_Oracle.Cursor = conn.cursor()
                cur.execute(query)
                now: datetime = datetime.now()
                if (now - self.last_commit_time).seconds >= COMMIT_INTERVAL:
                    self.last_commit_time: datetime = now
                    self.conn.commit()
                cur.close()
                return True
            except Exception as e:
                # no retry
                logging.error(f'[ExecuteError] {str(e)}')
                cur.close()
                return False
        # when failed up to max_retry
        logging.error('too many retry during execute')
        return False
    
if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

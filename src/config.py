import json
import os
import sys

SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, ROOT_DIR)

import util


class CrawlerConfig:
    def __init__(self, user_key: str, save_dir: str = '/locdisk/telegram_data'):
        self.user_key = user_key
        self.root_dir = ROOT_DIR
        self.save_dir = save_dir
        self.cur_day = util.cur_day_str()
        self.user_info = self._load_user_info()
        self.channel_dict = self._load_channel_list()

    @property
    def channel_ids(self) -> list:
        return list(self.channel_dict.keys())

    @property
    def session_file(self) -> str:
        return self.user_info['session_file'] + '.session'

    @property
    def api_id(self) -> str:
        return self.user_info['api_id']

    @property
    def api_hash(self) -> str:
        return self.user_info['api_hash']

    @property
    def log_path(self) -> str:
        return f'{self.root_dir}/log/telegram.log.{self.user_key}'

    def _load_user_info(self) -> dict:
        path = f'{self.root_dir}/config/user_info.json'
        with open(path) as f:
            user_list = json.loads(f.read().strip())
        if self.user_key not in user_list:
            raise ValueError(f"User key {self.user_key} not found in user_info.json")
        return user_list[self.user_key]

    def _load_channel_list(self, date_str: str = None) -> dict:
        if date_str is None:
            date_str = self.cur_day
        path = f'{self.root_dir}/etc/channel_list.{date_str}.json'
        with open(path) as f:
            data = json.loads(f.read().strip())
        return {int(k): v for k, v in data.items()}

    def save_channel_list(self, date_str: str = None):
        if date_str is None:
            date_str = self.cur_day
        path = f'{self.root_dir}/etc/channel_list.{date_str}.json'
        with open(path, 'w') as f:
            f.write(json.dumps(self.channel_dict, ensure_ascii=False))

    def message_file_path(self, date_str: str = None) -> str:
        if date_str is None:
            date_str = self.cur_day
        return f'{self.save_dir}/telegram_message.{date_str}.json'

    def media_dir(self, channel_id) -> str:
        cur_date = util.cur_day_str()
        path = f"{self.save_dir}/etc_file/{cur_date}/{channel_id}"
        os.makedirs(path, exist_ok=True)
        return path

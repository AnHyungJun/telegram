import json
import os
import logging

from extract_to_dict import extract_from
import util


class MessageProcessor:
    def __init__(self, config, embedded_client, kafka_client=None, logger=None):
        self.config = config
        self.embedded_client = embedded_client
        self.kafka_client = kafka_client
        self.logger = logger or logging.getLogger()
        self.cur_day = util.cur_day_str()
        self.message_file = open(config.message_file_path(self.cur_day), 'a')
        self.item_count = 0

    async def process(self, message, skip_ids: set = None) -> dict | None:
        message_dict = await extract_from(message)
        if skip_ids is not None and message_dict['message_id'] in skip_ids:
            return None
        await self._download_media(message, message_dict)
        self._update_channel_info(message_dict)
        self._extract_urls(message_dict)
        self._save_to_file(message_dict)
        if self.kafka_client:
            self.kafka_client.send_kafka(message_dict)
        self._check_day_change()
        self.item_count += 1
        return message_dict

    async def _download_media(self, message, msg):
        if msg['has_photo'] or msg['has_document']:
            media_dir = self.config.media_dir(msg['channel_id'])
            file_path = await message.download_media(file=media_dir)
            if file_path and ' ' in file_path:
                new_path = file_path.replace(' ', '_')
                os.rename(file_path, new_path)
                file_path = new_path
            if file_path:
                file_name = os.path.basename(file_path)
                msg['file_path'] = f"{media_dir}/{file_name}"
                msg['file_name'] = file_name
            else:
                msg['file_path'] = None
                msg['file_name'] = None
        else:
            msg['file_path'] = None
            msg['file_name'] = None

    def _update_channel_info(self, msg):
        channel_info = self.config.channel_dict.get(msg['channel_id'])
        if channel_info:
            channel_info['crawl_message_id'] = msg['message_id']

    def _extract_urls(self, msg):
        embedded_urls, url_metadata = self.embedded_client.extract_urls_and_metadata(msg["message"])
        msg["embedded_urls"] = embedded_urls
        msg["url_metadata"] = url_metadata

    def _save_to_file(self, msg):
        self.message_file.write(json.dumps(msg, ensure_ascii=False) + '\n')

    def _check_day_change(self):
        new_day = util.cur_day_str()
        if new_day != self.cur_day:
            self.cur_day = new_day
            self.message_file.close()
            self.message_file = open(self.config.message_file_path(self.cur_day), 'a')
            self.config.save_channel_list(self.cur_day)

    def close(self):
        if self.message_file and not self.message_file.closed:
            self.message_file.close()

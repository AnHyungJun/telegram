import sys
import json
import logging
import time

from telethon import TelegramClient, utils, types

from config import CrawlerConfig
from message_processor import MessageProcessor
from embedded_crawler import TelegramUrlProcessor


def load_crawled_ids(file_path: str) -> dict:
    """기수집 메시지 ID 로딩. {channel_id: set(message_ids)}"""
    result = {}
    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            msg = json.loads(line)
            ch_id = msg['channel_id']
            if ch_id not in result:
                result[ch_id] = set()
            result[ch_id].add(msg['message_id'])
    return result


class BackfillCrawler:
    def __init__(self, user_key: str, save_dir: str = '/locdisk/telegram_data'):
        self.config = CrawlerConfig(user_key, save_dir=save_dir)
        self.client = TelegramClient(
            self.config.session_file,
            self.config.api_id,
            self.config.api_hash
        )
        self.processor = MessageProcessor(
            config=self.config,
            embedded_client=TelegramUrlProcessor(),
            logger=logging.getLogger()
        )

    @staticmethod
    def to_marked_channel_id(real_id: int):
        return utils.get_peer_id(types.PeerChannel(real_id))

    async def backfill_channel(self, channel_id: int, offset_id: int = 0, crawled_ids: set = None):
        channel = await self.client.get_entity(self.to_marked_channel_id(channel_id))
        skip_count = 0

        async for message in self.client.iter_messages(channel, limit=None, offset_id=offset_id, reverse=True):
            if skip_count >= 5:
                break
            try:
                result = await self.processor.process(message, skip_ids=crawled_ids)
            except Exception:
                logging.exception(f"Failed to process message in channel {channel_id}")
                continue

            if result is None:
                logging.info(f'Already crawled {channel_id}: {message.id}')
                skip_count += 1
                continue

            skip_count = 0
            time.sleep(1)

    def run_channel(self, channel_id: int, offset_id: int = 0, crawled_ids: set = None):
        with self.client:
            self.client.loop.run_until_complete(
                self.backfill_channel(channel_id, offset_id, crawled_ids)
            )

    def close(self):
        self.processor.close()


if __name__ == '__main__':
    logging.basicConfig(
        format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
        level=logging.INFO
    )

    if len(sys.argv) < 4:
        print('Usage: python backfill.py <user_key> <single|many> <channel_id|input_file> [crawled_file]')
        sys.exit(1)

    user_key = sys.argv[1]
    mode = sys.argv[2]
    target = sys.argv[3]

    crawled_dict = {}
    if len(sys.argv) > 4:
        crawled_dict = load_crawled_ids(sys.argv[4])

    crawler = BackfillCrawler(user_key)

    try:
        if mode == 'single':
            channel_id = int(target)
            crawled_ids = crawled_dict.get(channel_id, set())
            crawler.run_channel(channel_id, crawled_ids=crawled_ids)
        elif mode == 'many':
            with open(target) as f:
                channels = json.loads(f.read().strip())
            for key, info in channels.items():
                ch_id = info.get('channel_id', int(key))
                offset = info.get('crawl_message_id', 0) or 0
                crawled_ids = crawled_dict.get(ch_id, set())
                crawler.run_channel(ch_id, offset, crawled_ids)
        else:
            print('mode must be "single" or "many"')
            sys.exit(1)
    finally:
        crawler.close()

import sys
import logging
import traceback
from logging import handlers

from telethon import TelegramClient, events

from config import CrawlerConfig
from message_processor import MessageProcessor
from embedded_crawler import TelegramUrlProcessor
from send_message import KafkaHandler


class TelegramCrawler:
    def __init__(self, user_key: str):
        self.config = CrawlerConfig(user_key)
        self.logger = self._setup_logger()
        self.client = TelegramClient(
            self.config.session_file,
            self.config.api_id,
            self.config.api_hash
        )
        self.processor = MessageProcessor(
            config=self.config,
            embedded_client=TelegramUrlProcessor(),
            kafka_client=KafkaHandler(),
            logger=self.logger
        )

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger()
        formatter = logging.Formatter('%(asctime)s  (%(levelname)s) %(message)s')
        handler = handlers.TimedRotatingFileHandler(
            filename=self.config.log_path,
            when='midnight', interval=1, encoding='utf-8'
        )
        handler.suffix = '%Y%m%d'
        handler.setFormatter(formatter)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        return logger

    async def on_new_message(self, event):
        try:
            self.logger.info(event)
            if event.chat.id not in self.config.channel_ids:
                self.logger.info(f"[CHANNEL_ID NOT IN] {event.chat.id} / {event.chat.username}")
                return
            await self.processor.process(event)
        except Exception:
            self.logger.error('ERROR MESSAGE')
            self.logger.error(event.chat_id)
            self.logger.error(traceback.format_exc())
            raise

    def run(self):
        self.client.on(events.NewMessage(incoming=True))(self.on_new_message)
        try:
            self.client.start()
            self.client.run_until_disconnected()
        finally:
            self.processor.close()
            self.logger.info('END PROGRAM')


if __name__ == '__main__':
    user_key = sys.argv[1]
    crawler = TelegramCrawler(user_key)
    crawler.run()

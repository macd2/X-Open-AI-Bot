import datetime
import logging

from dotenv import dotenv_values
from telegram import Bot

env = dotenv_values(".env")


# https://github.com/python-telegram-bot/python-telegram-bot
def telegram_send_message_to(message):
    if env["telegramToken"] and env["telegramChatId"] and message:
        try:
            bot = Bot(token=env["telegramToken"])
            bot.send_message(chat_id=int(env["telegramChatId"]), text=f"{message}")
        except Exception:
            pass


class TelegramLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record):
        log_entry = self.format(record)
        if log_entry.strip():  # Check if the log entry is not empty or only contains whitespace
            try:
                telegram_send_message_to(message=f"{datetime.datetime.now().strftime('%d.%m %H:%M:%S')}:: {log_entry}")
            except Exception as e:
                logger.error(f"Telegram issue {e}")


def setup_logger():
    # Configure logging
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%b %d %H:%M:%S',
                        level=logging.INFO)

    # Create the Telegram log handler
    telegram_handler = TelegramLogHandler()
    telegram_handler.setLevel(logging.INFO)

    # Get the root logger_ and add the Telegram log handler
    logger_ = logging.getLogger()
    logger_.addHandler(telegram_handler)

    return logger_


logger = setup_logger()

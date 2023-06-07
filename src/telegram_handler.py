from telegram import Bot
from dotenv import dotenv_values

env = dotenv_values(".env")


# https://github.com/python-telegram-bot/python-telegram-bot
def telegram_send_message_to(message):
    if env["telegramToken"] and env["telegramChatId"] and message:
        bot = Bot(token=env["telegramToken"])
        bot.send_message(chat_id=int(env["telegramChatId"]), text=f"{message}")



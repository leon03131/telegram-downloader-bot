import os
import telebot
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def handle_start(message):
    hi_text = "Привет! Я бот для скачивания медиа. Отправьте мне фото, видео или ссылку на стикерпак."
    bot.reply_to(message, hi_text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    ph_text = "Я получил фото! 👌🏿"
    bot.reply_to(message, ph_text)

bot.polling(none_stop=True)
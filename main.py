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

# ниже пиздец

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    photo_id = message.photo[-1].file_id
    unique_id = message.photo[-1].file_unique_id
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = f"{unique_id}.jpg"
    with open(filename, 'wb') as new_file:
        new_file.write(downloaded_file)

    ph_text = "Я получил фото! 👌🏿"
    bot.reply_to(message, ph_text)

bot.polling(none_stop=True)
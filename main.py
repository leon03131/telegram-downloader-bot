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
    photo_id = message.photo[-1].file_id
    unique_id = message.photo[-1].file_unique_id
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = f"{unique_id}.jpg"
    with open(filename, 'wb') as new_file:
        new_file.write(downloaded_file)

    ph_text = "Я получил фото! 👌🏿"
    bot.reply_to(message, ph_text)

    with open(filename, 'rb') as file_to_send:
        bot.send_document(message.chat.id, file_to_send, caption="Держи файл без сжатия!")
    
    os.remove(filename)

@bot.message_handler(content_types=['video']) # тут всё по аналогии с фото ничего нового
def handle_video(message):
    video_id = message.video.file_id
    unique_id = message.video.file_unique_id
    file_info = bot.get_file(video_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = f"{unique_id}.mp4"
    with open(filename, 'wb') as new_file:
        new_file.write(downloaded_file)

    ph_text = "Я получил видео! 👌🏿"
    bot.reply_to(message, ph_text)

    with open(filename, 'rb') as file_to_send:
        bot.send_document(message.chat.id, file_to_send, caption="Держи файл без сжатия!")
    
    os.remove(filename)

@bot.message_handler(content_types=['text']) # хотелось бы чтобы существовал url но боты не умеют ловить ссылки а только текст :(
def handle_text(message):
    if message.text.startswith("https://t.me/addstickers/"): # ищет сообщения начинающиеся на https://t.me/addstickers/
            prefix = "https://t.me/addstickers/" # обозначаю https://t.me/addstickers/ как префикс (ну не нужное)
            pack_name = message.text.replace(prefix, "") # заменяю ссылку на пустоту чтобы остался только код стикерпака
            print(pack_name) # это для тестов
    else:
        print("Это обычный текст.")
    

bot.polling(none_stop=True)
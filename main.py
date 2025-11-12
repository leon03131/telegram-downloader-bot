import os
import telebot
from moviepy import VideoFileClip
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
            sticker_set = bot.get_sticker_set(pack_name) # ну прописываем его в переменную
            for sticker in sticker_set.stickers: # через перебор скачиваем всё
                print(sticker) # это нада (ключи чекнуть)
                sticker_id = sticker.file_id # ну это для скачивания по аналогии с фотками и видео
                unique_id = sticker.file_unique_id # ...
                file_info = bot.get_file(sticker_id) # ...
                downloaded_file = bot.download_file(file_info.file_path) # ... б... это такой просто
                if sticker.is_video: # проверка анимированный стикер или нет
                    temp_filename_mp4 = f"{unique_id}.mp4" # Короче как оказалось анимированные стикеры в тг это видео поэтому пришлось всё перелопатить потому что простов видео в формате webp или gif нельзя скачать он ломается и получается какиш
                    final_filename_gif = f"{unique_id}.gif" # задаю переменные
                    with open(temp_filename_mp4, 'wb') as new_file: # скачивание видео (стикера)
                        new_file.write(downloaded_file) # всё ещё скачивание ...
                    video_clip = VideoFileClip(temp_filename_mp4) # конвертация видео в гиф с помощью moviepy (да это долго но что делать просто видосы никому не нужны 100%)
                    video_clip.write_gif(final_filename_gif) # всё ещё конвертация
                    video_clip.close() # конец конвертации
                    os.remove(temp_filename_mp4) # удаление временого файла видео
                else: # else
                    filename = f"{unique_id}.png" # ну скачивание стикера если он картинка
                    with open(filename, 'wb') as new_file: # скачивание
                        new_file.write(downloaded_file) # скачивание ...
    else:
        print("Это обычный текст.")
    

bot.polling(none_stop=True)
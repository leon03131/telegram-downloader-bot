import os
import telebot
import shutil
from moviepy import VideoFileClip
from dotenv import load_dotenv
from rlottie_python import LottieAnimation

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(token)

def convert_tgs_to_gif(tgs_path, gif_path):
    anim = LottieAnimation.from_tgs(tgs_path)
    anim.save_animation(gif_path)

@bot.message_handler(commands=['start'])
def handle_start(message):
    hi_text = "Привет! Я бот для скачивания медиа. Отправьте мне фото, видео или ссылку на стикерпак."
    bot.reply_to(message, hi_text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    photo_id = message.photo[-1].file_id
    unique_id = message.photo[-1].file_unique_id
    os.mkdir(photo_id)
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = f"{photo_id}/{unique_id}.jpg"

    with open(filename, 'wb') as new_file:
        new_file.write(downloaded_file)

    ph_text = "Я получил фото! 👌🏿"
    bot.reply_to(message, ph_text)

    with open(filename, 'rb') as file_to_send:
        bot.send_document(message.chat.id, file_to_send, caption="Держи файл без сжатия!")
    
    shutil.rmtree(photo_id) # удаление папки

@bot.message_handler(content_types=['video']) # тут всё по аналогии с фото ничего нового
def handle_video(message):
    video_id = message.video.file_id
    unique_id = message.video.file_unique_id
    os.mkdir(video_id)
    file_info = bot.get_file(video_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = f"{video_id}/{unique_id}.mp4"

    with open(filename, 'wb') as new_file:
        new_file.write(downloaded_file)

    ph_text = "Я получил видео! 👌🏿"
    bot.reply_to(message, ph_text)

    with open(filename, 'rb') as file_to_send:
        bot.send_document(message.chat.id, file_to_send, caption="Держи файл без сжатия!")
    
    shutil.rmtree(video_id) # удаление папки

@bot.message_handler(content_types=['text']) # хотелось бы чтобы существовал url но боты не умеют ловить ссылки а только текст :(
def handle_text(message):

    if message.text.startswith("https://t.me/addstickers/"): # ищет сообщения начинающиеся на https://t.me/addstickers/
            prefix = "https://t.me/addstickers/" # обозначаю https://t.me/addstickers/ как префикс (ну не нужное)
            pack_name = message.text.replace(prefix, "") # заменяю ссылку на пустоту чтобы остался только код стикерпака
            print(pack_name) # это для тестов
            os.mkdir(pack_name) # создаю папочку отдельную чтобы туда скачивать
            sticker_set = bot.get_sticker_set(pack_name) # ну прописываем его в переменную

            for sticker in sticker_set.stickers: # через перебор скачиваем всё
                print(sticker) # это нада (ключи чекнуть)
                sticker_id = sticker.file_id # ну это для скачивания по аналогии с фотками и видео
                unique_id = sticker.file_unique_id # ...
                file_info = bot.get_file(sticker_id) # ...
                downloaded_file = bot.download_file(file_info.file_path) # ... б... это такой просто
                
                if sticker.is_video: # проверка анимированный стикер или нет
                    temp_filename_mp4 = f"{pack_name}/{unique_id}.mp4" # Короче как оказалось анимированные стикеры в тг это видео поэтому пришлось всё перелопатить потому что простов видео в формате webp или gif нельзя скачать он ломается и получается какиш
                    final_filename_gif = f"{pack_name}/{unique_id}.gif" # задаю переменные

                    with open(temp_filename_mp4, 'wb') as new_file: # скачивание видео (стикера)
                        new_file.write(downloaded_file) # всё ещё скачивание ...
                        
                    video_clip = VideoFileClip(temp_filename_mp4) # конвертация видео в гиф с помощью moviepy (да это долго но что делать просто видосы никому не нужны 100%)
                    video_clip.write_gif(final_filename_gif) # всё ещё конвертация
                    video_clip.close() # конец конвертации
                    os.remove(temp_filename_mp4) # удаление временого файла видео

                elif sticker.is_animated:
                    temp_filename_tgs = f"{pack_name}/{unique_id}.tgs"
                    with open(temp_filename_tgs, 'wb') as new_file:
                        new_file.write(downloaded_file)

                    print(f"конвертирую: {temp_filename_tgs}")
                    try:
                        convert_tgs_to_gif(temp_filename_tgs, final_filename_gif)
                    except Exception as e:
                        print(f"ошибка конвертации: {e}")
                else: # else
                    filename = f"{pack_name}/{unique_id}.png" # ну скачивание стикера если он картинка

                    with open(filename, 'wb') as new_file: # скачивание
                        new_file.write(downloaded_file) # скачивание ...
            shutil.make_archive(pack_name, 'zip', pack_name) # упаковываю в zip
            shutil.rmtree(pack_name) # удаляю папку

            with open(pack_name + ".zip", 'rb') as file_to_send:
                bot.send_document(message.chat.id, file_to_send, caption="Дeржи свой стикер пак!") # отправляю архив с стикерами
            os.remove(pack_name + ".zip") # удаляю архив
    else:
        print("Это обычный текст.")

@bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn1 = telebot.types.InlineKeyboardButton(
        text="Скачать стикер", 
        callback_data="dl_sticker"
    )
    btn2 = telebot.types.InlineKeyboardButton(
        text="Скачать стикерпак", 
        callback_data="dl_pack"
    )
    markup.add(btn1,btn2)

    bot.reply_to(message, "Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):

    if call.data == "dl_sticker":
        sticker_id = call.message.reply_to_message.sticker.file_id
        unique_id = call.message.reply_to_message.sticker.file_unique_id
        os.mkdir(sticker_id)
        file_info = bot.get_file(sticker_id)
        downloaded_file = bot.download_file(file_info.file_path) # ... б... это такой просто

        if call.message.reply_to_message.sticker.is_video: # проверка анимированный стикер или нет
            temp_filename_mp4 = f"{sticker_id}/{unique_id}.mp4" # Короче как оказалось анимированные стикеры в тг это видео поэтому пришлось всё перелопатить потому что простов видео в формате webp или gif нельзя скачать он ломается и получается какиш
            final_filename_gif = f"{sticker_id}/{unique_id}.gif" # задаю переменные

            with open(temp_filename_mp4, 'wb') as new_file: # скачивание видео (стикера)
                new_file.write(downloaded_file) # всё ещё скачивание ...
            video_clip = VideoFileClip(temp_filename_mp4) # конвертация видео в гиф с помощью moviepy (да это долго но что делать просто видосы никому не нужны 100%)
            video_clip.write_gif(final_filename_gif) # всё ещё конвертация
            video_clip.close() # конец конвертации
            os.remove(temp_filename_mp4) # удаление временого файла видео

            with open(final_filename_gif, 'rb') as file_to_send:
                bot.send_document(call.message.chat.id, file_to_send, caption="ДЕржи свой стикер!")
            shutil.rmtree(sticker_id) 

        else: # else
            filename = f"{sticker_id}/{unique_id}.png" # ну скачивание стикера если он картинка

            with open(filename, 'wb') as new_file: # скачивание
                new_file.write(downloaded_file) # скачивание ...

            with open(filename, 'rb') as file_to_send:
                bot.send_document(call.message.chat.id, file_to_send, caption="ДЕржи свой стикер!")
            shutil.rmtree(sticker_id) 

bot.polling(none_stop=True)
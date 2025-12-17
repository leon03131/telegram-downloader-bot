import os
import telebot
import shutil
import ffmpeg
import zipfile
import yt_dlp
from PIL import Image
from dotenv import load_dotenv
from rlottie_python import LottieAnimation
from yandex_music import Client

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
yandextoken = os.getenv('YANDEX_TOKEN')

bot = telebot.TeleBot(token)
client = Client(yandextoken).init()

def convert_tgs_to_gif(tgs_path, gif_path):
    anim = LottieAnimation.from_tgs(tgs_path)
    anim.save_animation(gif_path)

def download_video_from_url(url):
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
    }

    if not os.path.exists('downloads'):
        os.mkdir('downloads')
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        print(f"Ошибка при скачивании: {e}")
        return None

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

    ph_text = "Я получил фото!"
    bot.reply_to(message, ph_text)

    with open(filename, 'rb') as file_to_send:
        bot.send_document(message.chat.id, file_to_send, caption="Держи файл без сжатия!")
    
    shutil.rmtree(photo_id)

@bot.message_handler(content_types=['video'])
def handle_video(message):
    video_id = message.video.file_id
    unique_id = message.video.file_unique_id
    os.mkdir(video_id)
    file_info = bot.get_file(video_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = f"{video_id}/{unique_id}.mp4"

    with open(filename, 'wb') as new_file:
        new_file.write(downloaded_file)

    ph_text = "Я получил видео!"
    bot.reply_to(message, ph_text)

    with open(filename, 'rb') as file_to_send:
        bot.send_document(message.chat.id, file_to_send, caption="Держи файл без сжатия!")
    
    shutil.rmtree(video_id)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text

    if "music.yandex" in text:
        bot.reply_to(message, "Вижу трек из Яндекс.Музыки! Пробую скачать...")
        user_id = message.from_user.id

        try:
            url = text.split("?")[0]

            if "/track/" in url:
                parts = url.split("/track/")
                track_id = parts[1].split("/")[0]

                track = client.tracks([track_id])[0]

                if not os.path.exists('music'):
                    os.mkdir('music')

                artist = track.artists[0].name if track.artists else "Неизвестен"
                title = track.title

                safe_artist = "".join(c for c in artist if c not in r'\/:*?"<>|')
                safe_title = "".join(c for c in title if c not in r'\/:*?"<>|')

                user_music_dir = f"music/music_{user_id}"

                if not os.path.exists(user_music_dir):
                    os.mkdir(user_music_dir)

                filename = f"{user_music_dir}/{safe_artist} - {safe_title}.mp3"

                jpg_cover_path = f"{user_music_dir}/{safe_artist} - {safe_title}.jpg"
                png_cover_path = f"{user_music_dir}/{safe_artist} - {safe_title}.png"

                bot.reply_to(message, "Скачиваю трек и обложку...")

                track.download(filename)
                track.download_cover(jpg_cover_path, "400x400")

                try:
                    img = Image.open(jpg_cover_path)
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    img.save(png_cover_path, format='PNG')
                except Exception as e:
                    print(f"Ошибка обработки обложки: {e}")
                    png_cover_path = jpg_cover_path

                with open(filename, 'rb') as f:
                    audio_data = f.read()
                
                with open(png_cover_path, 'rb') as f:
                    thumb_data = f.read()

                bot.send_audio(
                    message.chat.id,
                    audio_data,
                    caption="Держи трек!",
                    performer=artist,
                    title=title,
                    thumb=thumb_data
                )

                if os.path.exists(user_music_dir):
                    shutil.rmtree(user_music_dir)
                
            else:
                bot.reply_to(message, "Это ссылка на Яндекс, но я не вижу там трека.")

        except Exception as e:
            bot.reply_to(message, f"Ой, ошибка: {e}")
            print(e)

    elif "youtube.com" in text or "youtu.be" in text or "rutube.ru" in text or "vkvideo.ru" in text:
        bot.reply_to(message, "Я пока не умею скачивать видео, это сложно :( Но я умею стикеры и музыку!")

    elif message.text.startswith("https://t.me/addstickers/"):
            prefix = "https://t.me/addstickers/"
            pack_name = message.text.replace(prefix, "")
            user_id = message.from_user.id
            clean_pack_name = "".join(c for c in pack_name if c not in r'\/:*?"<>|')
            safe_pack_name = f"{user_id}_{clean_pack_name}"
            print(pack_name)
            os.mkdir(safe_pack_name)
            sticker_set = bot.get_sticker_set(pack_name)
            bot.reply_to(message, "⏳ Скачиваю пак. Если там есть анимации, это займет время...")

            files_to_send = []
            current_size = 0
            part_num = 1
            LIMIT = 45 * 1024 * 1024

            for sticker in sticker_set.stickers:
                print(sticker)
                sticker_id = sticker.file_id
                unique_id = sticker.file_unique_id
                file_info = bot.get_file(sticker_id)
                downloaded_file = bot.download_file(file_info.file_path)
                
                current_file = ""

                if sticker.is_video:
                    temp_filename_mp4 = f"{safe_pack_name}/{unique_id}.mp4"
                    final_filename_gif = f"{safe_pack_name}/{unique_id}.gif"

                    with open(temp_filename_mp4, 'wb') as new_file:
                        new_file.write(downloaded_file)
                        
                    (
                        ffmpeg  
                        .input(temp_filename_mp4)
                        .output(final_filename_gif)
                        .run()
                    )
                    os.remove(temp_filename_mp4)

                    current_file = final_filename_gif

                elif sticker.is_animated:
                    temp_filename_tgs = f"{safe_pack_name}/{unique_id}.tgs"
                    final_filename_gif = f"{safe_pack_name}/{unique_id}.gif"

                    with open(temp_filename_tgs, 'wb') as new_file:
                        new_file.write(downloaded_file)

                    print(f"конвертирую: {temp_filename_tgs}")
                    try:
                        convert_tgs_to_gif(temp_filename_tgs, final_filename_gif)

                        if os.path.exists(temp_filename_tgs):
                            os.remove(temp_filename_tgs)

                    except Exception as e:
                        print(f"ошибка конвертации: {e}")

                    current_file = final_filename_gif

                else: # else
                    filename = f"{safe_pack_name}/{unique_id}.png"

                    with open(filename, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    current_file = filename

                if current_file and os.path.exists(current_file):
                    file_size = os.path.getsize(current_file)
                
                if current_size + file_size > LIMIT:
                    archive_name = f"{safe_pack_name}/{clean_pack_name}_part{part_num}.zip"
                    print(f"📦 Отправляю часть {part_num}...")
                    
                    with zipfile.ZipFile(archive_name, 'w') as zipf:
                        for file_path in files_to_send:
                            zipf.write(file_path)
                    
                    with open(archive_name, 'rb') as doc:
                        bot.send_document(message.chat.id, doc, caption=f"📦 Часть {part_num}", timeout=120)
                    
                    os.remove(archive_name)
                    files_to_send = []
                    current_size = 0
                    part_num += 1
                
                files_to_send.append(current_file)
                current_size += file_size

            if files_to_send:
                archive_name = f"{safe_pack_name}/{clean_pack_name}_part{part_num}.zip"
                print(f"📦 Отправляю финал...")
                
                with zipfile.ZipFile(archive_name, 'w') as zipf:
                    for file_path in files_to_send:
                        zipf.write(file_path)
                
                with open(archive_name, 'rb') as doc:
                    bot.send_document(message.chat.id, doc, caption=f"📦 Часть {part_num} (Финал)", timeout=120)
                os.remove(archive_name)

            if os.path.exists(safe_pack_name):
                shutil.rmtree(safe_pack_name)
            print("✅ Готово!")
    else:
        print(".")

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
        user_id = call.from_user.id
        sticker_id = call.message.reply_to_message.sticker.file_id
        unique_id = call.message.reply_to_message.sticker.file_unique_id
        clean_sticker_id = "".join(c for c in sticker_id if c not in r'\/:*?"<>|')
        safe_sticker_id = f"{user_id}_{clean_sticker_id}"
        if not os.path.exists(safe_sticker_id):
            os.mkdir(safe_sticker_id)
        file_info = bot.get_file(sticker_id)
        downloaded_file = bot.download_file(file_info.file_path)

        if call.message.reply_to_message.sticker.is_video:
            temp_filename_mp4 = f"{safe_sticker_id}/{unique_id}.mp4"
            final_filename_gif = f"{safe_sticker_id}/{unique_id}.gif"

            with open(temp_filename_mp4, 'wb') as new_file:
                new_file.write(downloaded_file)

            (
                        ffmpeg  
                        .input(temp_filename_mp4)
                        .output(final_filename_gif)
                        .run()
                    )
            
            os.remove(temp_filename_mp4)

            with open(final_filename_gif, 'rb') as file_to_send:
                bot.send_document(call.message.chat.id, file_to_send, caption="Держи свой стикер!")
            shutil.rmtree(safe_sticker_id)

        elif call.message.reply_to_message.sticker.is_animated:
            temp_filename_tgs = f"{safe_sticker_id}/{unique_id}.tgs"
            final_filename_gif = f"{safe_sticker_id}/{unique_id}.gif"

            with open(temp_filename_tgs, 'wb') as new_file:
                new_file.write(downloaded_file)

            print(f"конвертирую: {temp_filename_tgs}")
            try:
                convert_tgs_to_gif(temp_filename_tgs, final_filename_gif)

                if os.path.exists(temp_filename_tgs):
                    os.remove(temp_filename_tgs)

            except Exception as e:
                print(f"ошибка конвертации: {e}")

            if os.path.exists(final_filename_gif):
                with open(final_filename_gif, 'rb') as file_to_send:
                    bot.send_document(call.message.chat.id, file_to_send, caption="Держи свой стикер!")
            
            shutil.rmtree(safe_sticker_id)

        else: # else
            filename = f"{safe_sticker_id}/{unique_id}.png"

            with open(filename, 'wb') as new_file:
                new_file.write(downloaded_file)

            with open(filename, 'rb') as file_to_send:
                bot.send_document(call.message.chat.id, file_to_send, caption="Держи свой стикер!")
            shutil.rmtree(safe_sticker_id)
    else:
            user_id = call.from_user.id
            pack_name = call.message.reply_to_message.sticker.set_name
            clean_pack_name = "".join(c for c in pack_name if c not in r'\/:*?"<>|')
            safe_pack_name = f"{user_id}_{clean_pack_name}"
            os.mkdir(safe_pack_name)
            sticker_set = bot.get_sticker_set(pack_name)
            bot.reply_to(call.message, "⏳ Скачиваю пак. Если там есть анимации, это займет время...")

            files_to_send = []
            current_size = 0
            part_num = 1
            LIMIT = 45 * 1024 * 1024

            for sticker in sticker_set.stickers:
                print(sticker)
                sticker_id = sticker.file_id
                unique_id = sticker.file_unique_id
                file_info = bot.get_file(sticker_id)
                downloaded_file = bot.download_file(file_info.file_path)
                
                current_file = ""

                if sticker.is_video:
                    temp_filename_mp4 = f"{safe_pack_name}/{unique_id}.mp4"
                    final_filename_gif = f"{safe_pack_name}/{unique_id}.gif"

                    with open(temp_filename_mp4, 'wb') as new_file:
                        new_file.write(downloaded_file)
                        
                    (
                        ffmpeg  
                        .input(temp_filename_mp4)
                        .output(final_filename_gif)
                        .run()
                    )
                    os.remove(temp_filename_mp4)

                    current_file = final_filename_gif

                elif sticker.is_animated:
                    temp_filename_tgs = f"{safe_pack_name}/{unique_id}.tgs"
                    final_filename_gif = f"{safe_pack_name}/{unique_id}.gif"

                    with open(temp_filename_tgs, 'wb') as new_file:
                        new_file.write(downloaded_file)

                    print(f"конвертирую: {temp_filename_tgs}")
                    try:
                        convert_tgs_to_gif(temp_filename_tgs, final_filename_gif)

                        if os.path.exists(temp_filename_tgs):
                            os.remove(temp_filename_tgs)

                    except Exception as e:
                        print(f"ошибка конвертации: {e}")

                    current_file = final_filename_gif

                else: # else
                    filename = f"{safe_pack_name}/{unique_id}.png"

                    with open(filename, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    current_file = filename

                if current_file and os.path.exists(current_file):
                    file_size = os.path.getsize(current_file)
                
                if current_size + file_size > LIMIT:
                    archive_name = f"{safe_pack_name}/{clean_pack_name}_part{part_num}.zip"
                    print(f"📦 Отправляю часть {part_num}...")
                    
                    with zipfile.ZipFile(archive_name, 'w') as zipf:
                        for file_path in files_to_send:
                            zipf.write(file_path)
                    
                    with open(archive_name, 'rb') as doc:
                        bot.send_document(call.message.chat.id, doc, caption=f"📦 Часть {part_num}", timeout=120)
                    
                    os.remove(archive_name)
                    files_to_send = []
                    current_size = 0
                    part_num += 1
                
                files_to_send.append(current_file)
                current_size += file_size

            if files_to_send:
                archive_name = f"{safe_pack_name}/{clean_pack_name}_part{part_num}.zip"
                print(f"📦 Отправляю финал...")
                
                with zipfile.ZipFile(archive_name, 'w') as zipf:
                    for file_path in files_to_send:
                        zipf.write(file_path)

                with open(archive_name, 'rb') as doc:
                    bot.send_document(call.message.chat.id, doc, caption=f"📦 Часть {part_num} (Финал)", timeout=120)
                os.remove(archive_name)

            if os.path.exists(safe_pack_name):
                shutil.rmtree(safe_pack_name)
                print("✅ Готово!")
            else:
                print(".")

bot.polling(none_stop=True)
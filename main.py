import os
import telebot
import shutil
import ffmpeg
import zipfile
from PIL import Image
from dotenv import load_dotenv
from rlottie_python import LottieAnimation
from yandex_music import Client

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
yandextoken = os.getenv('YANDEX_TOKEN')

bot = telebot.TeleBot(token)
client = Client(yandextoken).init()

def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def convert_tgs_to_gif(tgs_path, gif_path):
    anim = LottieAnimation.from_tgs(tgs_path)
    anim.save_animation(gif_path)

@bot.message_handler(commands=['start'])
def handle_start(message):
    hi_text = "Привет! Я бот для скачивания медиа. Отправьте мне фото, видео или ссылку на стикерпак."
    bot.reply_to(message, hi_text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id
    unique_id = message.photo[-1].file_unique_id
    user_dir = f"photos/photos_{user_id}"
    ensure_folder(user_dir)
    file_info = bot.get_file(photo_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = f"{user_dir}/{unique_id}.jpg"

    with open(filename, 'wb') as new_file:
        new_file.write(downloaded_file)

    ph_text = "Я получил фото!"
    bot.reply_to(message, ph_text)

    with open(filename, 'rb') as file_to_send:
        bot.send_document(message.chat.id, file_to_send, caption="Держи файл без сжатия!")
    
    shutil.rmtree(user_dir)

@bot.message_handler(content_types=['video'])
def handle_video(message):
    user_id = message.from_user.id
    video_id = message.video.file_id
    unique_id = message.video.file_unique_id
    user_dir = f"videos/videos_{user_id}"
    ensure_folder(user_dir)
    file_info = bot.get_file(video_id)
    downloaded_file = bot.download_file(file_info.file_path)
    filename = f"{user_dir}/{unique_id}.mp4"

    with open(filename, 'wb') as new_file:
        new_file.write(downloaded_file)

    ph_text = "Я получил видео!"
    bot.reply_to(message, ph_text)

    with open(filename, 'rb') as file_to_send:
        bot.send_document(message.chat.id, file_to_send, caption="Держи файл без сжатия!")
    
    shutil.rmtree(user_dir)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    text = message.text
    user_id = message.from_user.id

    if "music.yandex" in text:
        bot.reply_to(message, "Вижу трек из Яндекс.Музыки! Пробую скачать...")
        
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
                ensure_folder(user_music_dir)

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
            clean_pack_name = "".join(c for c in pack_name if c not in r'\/:*?"<>|')
            base_user_dir = f"stickers/stickers_{user_id}"
            pack_dir = f"{base_user_dir}/{clean_pack_name}"
            ensure_folder(pack_dir)
            sticker_set = bot.get_sticker_set(pack_name)
            pack_title = sticker_set.title 
            clean_pack_title = "".join(c for c in pack_title if c not in r'\/:*?"<>|').strip()
            if not clean_pack_title: 
                clean_pack_title = "sticker_pack"
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
                    temp_filename_mp4 = f"{pack_dir}/{unique_id}.mp4"
                    final_filename_gif = f"{pack_dir}/{unique_id}.gif"

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
                    temp_filename_tgs = f"{pack_dir}/{unique_id}.tgs"
                    final_filename_gif = f"{pack_dir}/{unique_id}.gif"

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
                    filename = f"{pack_dir}/{unique_id}.png"

                    with open(filename, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    current_file = filename

                if current_file and os.path.exists(current_file):
                    file_size = os.path.getsize(current_file)
                
                if current_size + file_size > LIMIT:
                    archive_name = f"{base_user_dir}/{clean_pack_title}_part{part_num}.zip"
                    print(f"📦 Отправляю часть {part_num}...")
                    
                    with zipfile.ZipFile(archive_name, 'w') as zipf:
                        for file_path in files_to_send:
                            zipf.write(file_path, arcname=os.path.basename(file_path))
                    
                    with open(archive_name, 'rb') as doc:
                        bot.send_document(message.chat.id, doc, caption=f"📦 Часть {part_num}", timeout=120)
                    
                    os.remove(archive_name)
                    files_to_send = []
                    current_size = 0
                    part_num += 1
                
                files_to_send.append(current_file)
                current_size += file_size

            if files_to_send:
                archive_name = f"{base_user_dir}/{clean_pack_title}_part{part_num}.zip"
                print(f"📦 Отправляю финал...")
                
                with zipfile.ZipFile(archive_name, 'w') as zipf:
                    for file_path in files_to_send:
                        zipf.write(file_path, arcname=os.path.basename(file_path))
                
                with open(archive_name, 'rb') as doc:
                    bot.send_document(message.chat.id, doc, caption=f"📦 Часть {part_num} (Финал)", timeout=120)
                os.remove(archive_name)

            if os.path.exists(base_user_dir):
                shutil.rmtree(base_user_dir)
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
    user_id = call.from_user.id
    
    if call.data == "dl_sticker":
        sticker_id = call.message.reply_to_message.sticker.file_id
        unique_id = call.message.reply_to_message.sticker.file_unique_id

        base_user_dir = f"stickers/stickers_{user_id}"
        task_dir = f"{base_user_dir}/single_{unique_id}"
        ensure_folder(task_dir)

        file_info = bot.get_file(sticker_id)
        downloaded_file = bot.download_file(file_info.file_path)

        if call.message.reply_to_message.sticker.is_video:
            temp_filename_mp4 = f"{task_dir}/{unique_id}.mp4"
            final_filename_gif = f"{task_dir}/{unique_id}.gif"

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
            shutil.rmtree(task_dir)

        elif call.message.reply_to_message.sticker.is_animated:
            temp_filename_tgs = f"{task_dir}/{unique_id}.tgs"
            final_filename_gif = f"{task_dir}/{unique_id}.gif"

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
            
            shutil.rmtree(task_dir)

        else: # else
            filename = f"{task_dir}/{unique_id}.png"

            with open(filename, 'wb') as new_file:
                new_file.write(downloaded_file)

            with open(filename, 'rb') as file_to_send:
                bot.send_document(call.message.chat.id, file_to_send, caption="Держи свой стикер!")
            shutil.rmtree(task_dir)
    else:
            user_id = call.from_user.id
            pack_name = call.message.reply_to_message.sticker.set_name
            clean_pack_name = "".join(c for c in pack_name if c not in r'\/:*?"<>|')

            base_user_dir = f"stickers/stickers_{user_id}"
            pack_dir = f"{base_user_dir}/{clean_pack_name}"
            ensure_folder(pack_dir)

            sticker_set = bot.get_sticker_set(pack_name)
            pack_title = sticker_set.title 
            clean_pack_title = "".join(c for c in pack_title if c not in r'\/:*?"<>|').strip()
            if not clean_pack_title: 
                clean_pack_title = "sticker_pack"
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
                    temp_filename_mp4 = f"{pack_dir}/{unique_id}.mp4"
                    final_filename_gif = f"{pack_dir}/{unique_id}.gif"

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
                    temp_filename_tgs = f"{pack_dir}/{unique_id}.tgs"
                    final_filename_gif = f"{pack_dir}/{unique_id}.gif"

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
                    filename = f"{pack_dir}/{unique_id}.png"

                    with open(filename, 'wb') as new_file:
                        new_file.write(downloaded_file)
                    current_file = filename

                if current_file and os.path.exists(current_file):
                    file_size = os.path.getsize(current_file)
                
                if current_size + file_size > LIMIT:
                    archive_name = f"{base_user_dir}/{clean_pack_title}_part{part_num}.zip"
                    print(f"📦 Отправляю часть {part_num}...")
                    
                    with zipfile.ZipFile(archive_name, 'w') as zipf:
                        for file_path in files_to_send:
                            zipf.write(file_path, arcname=os.path.basename(file_path))
                    
                    with open(archive_name, 'rb') as doc:
                        bot.send_document(call.message.chat.id, doc, caption=f"📦 Часть {part_num}", timeout=120)
                    
                    os.remove(archive_name)
                    files_to_send = []
                    current_size = 0
                    part_num += 1
                
                files_to_send.append(current_file)
                current_size += file_size

            if files_to_send:
                archive_name = f"{base_user_dir}/{clean_pack_title}_part{part_num}.zip"
                print(f"📦 Отправляю финал...")
                
                with zipfile.ZipFile(archive_name, 'w') as zipf:
                    for file_path in files_to_send:
                        zipf.write(file_path, arcname=os.path.basename(file_path))

                with open(archive_name, 'rb') as doc:
                    bot.send_document(call.message.chat.id, doc, caption=f"📦 Часть {part_num} (Финал)", timeout=120)
                os.remove(archive_name)

            if os.path.exists(base_user_dir):
                shutil.rmtree(base_user_dir)
                print("✅ Готово!")
            else:
                print(".")

bot.polling(none_stop=True)
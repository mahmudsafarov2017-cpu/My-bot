import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

TOKEN = "8638543243:AAHpMYhv8L-Y1aazkf6UZwqf3ndt8y0lVE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на видео (YouTube, TikTok и др.), и я предложу выбрать формат для скачивания.")

@dp.message()
async def handle_url(message: types.Message):
    url = message.text
    if not url or not url.startswith("http"):
        await message.reply("Пожалуйста, отправь корректную ссылку на видео.")
        return

    # Создаем инлайн-кнопки выбора формата
    builder = InlineKeyboardBuilder()
    # Передаем ссылку через callback_data (в реальных проектах лучше сохранять во временный словарь, но для простоты вставим так)
    builder.button(text="🎬 Скачать видео (MP4)", callback_data=f"vid_{url[:50]}")
    builder.button(text="🎵 Скачать аудио (MP3)", callback_data=f"aud_{url[:50]}")
    builder.adjust(1)

    # Сохраняем ссылку в памяти процесса или словаре, чтобы не резать длинные ссылки
    # Для простоты сделаем прямую обработку или сохранение в глобальный словарь:
    global user_links
    if 'user_links' not in globals():
        user_links = {}
    user_links[message.from_user.id] = url

    await message.answer("Выберите формат для скачивания:", reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data.startswith("vid_") or c.data.startswith("aud_"))
async def process_download(callback: types.CallbackQuery):
    action = callback.data[:3]
    user_id = callback.from_user.id
    
    if 'user_links' not in globals() or user_id not in user_links:
        await callback.message.edit_text("❌ Ссылка устарела. Отправьте её заново.")
        return

    url = user_links[user_id]
    await callback.message.edit_text("⏳ Начинаю скачивание...")

    os.makedirs("downloads", exist_ok=True)

    if action == "vid_":
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'cookiefile': 'cookies.txt',
        }
    else: # Аудио MP3
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'cookiefile': 'cookies.txt',
        }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await callback.message.edit_text("📥 Обрабатываю файл...")
            info = ydl.extract_info(url, download=True)
            
            if action == "aud_":
                # Меняем расширение на mp3 после конвертации через ffmpeg
                base_path, _ = os.path.splitext(ydl.prepare_filename(info))
                filename = base_path + ".mp3"
            else:
                filename = ydl.prepare_filename(info)

        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:
            await callback.message.edit_text("❌ Файл слишком большой (больше 50 МБ). Telegram не разрешает ботам отправлять такие файлы.")
            if os.path.exists(filename):
                os.remove(filename)
            return

        await callback.message.edit_text("📤 Отправляю файл...")
        file_to_send = types.FSInputFile(filename)

        if action == "vid_":
            await callback.message.answer_video(file_to_send)
        else:
            await callback.message.answer_audio(file_to_send)

        await callback.message.delete()

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp

TOKEN = "8638543243:AAHpMYhv8L-Y1aazkf6UZwqf3ndt8y0lVE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на видео (YouTube, TikTok и др.), и я скачаю его.")

@dp.message()
async def download_media(message: types.Message):
    url = message.text
    if not url or not url.startswith("http"):
        await message.reply("Пожалуйста, отправь корректную ссылку на видео.")
        return

    processing_msg = await message.reply("⏳ Загружаю информацию о файле...")
    
    # Настройки yt-dlp: стараемся скачать качественное, но подходящее по размеру видео
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'max_filesize': 50 * 1024 * 1024,  # Лимит Telegram на отправку файлов через бота (50 МБ)
        'cookiefile': 'cookies.txt',       # Куки для обхода блокировок и авторизации
    }
    
    os.makedirs("downloads", exist_ok=True)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await processing_msg.edit_text("📥 Скачиваю файл...")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # Проверяем реальный размер файла на диске перед отправкой
        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:
            await processing_msg.edit_text("❌ Видео слишком большое (весит больше 50 МБ). Telegram не позволяет ботам отправлять такие файлы.")
            if os.path.exists(filename):
                os.remove(filename)
            return

        await processing_msg.edit_text("📤 Отправляю файл...")
        
        file_extension = info.get('ext', '')
        file_to_send = types.FSInputFile(filename)
        
        if file_extension in ['mp4', 'mkv', 'webm', 'mov']:
            await message.answer_video(file_to_send)
        else:
            await message.answer_document(file_to_send)
            
        await processing_msg.delete()
        
    except Exception as e:
        await processing_msg.edit_text(f"❌ Ошибка при скачивании или отправке: {str(e)}")
        
    finally:
        # Всегда очищаем скачанный файл с сервера, чтобы не забивать память
        if 'filename' in locals() and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


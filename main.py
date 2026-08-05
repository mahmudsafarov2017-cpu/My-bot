import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import yt_dlp

TOKEN = os.getenv("TOKEN")


bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на видео, и я скачаю его.")

@dp.message()
async def download_media(message: types.Message):
    url = message.text
    if not url or not url.startswith("http"):
        await message.reply("Пожалуйста, отправь корректную ссылку на видео.")
        return

    processing_msg = await message.reply("⏳ Загружаю информацию о файле...")
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'max_filesize': 50 * 1024 * 1024,
    }
    
    os.makedirs("downloads", exist_ok=True)
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await processing_msg.edit_text("📥 Скачиваю файл...")
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        await processing_msg.edit_text("📤 Отправляю файл...")
        
        file_extension = info.get('ext', '')
        
        if file_extension in ['mp4', 'mkv', 'webm']:
            file_to_send = types.FSInputFile(filename)
            await message.answer_video(file_to_send)
        else:
            file_to_send = types.FSInputFile(filename)
            await message.answer_document(file_to_send)
            
        await processing_msg.delete()
        
        if os.path.exists(filename):
            os.remove(filename)
            
    except Exception as e:
        await processing_msg.edit_text(f"❌ Ошибка при скачивании: {str(e)}")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

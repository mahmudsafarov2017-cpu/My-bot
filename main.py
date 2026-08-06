import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import yt_dlp

TOKEN = "8638543243:AAHpMYhv8L-Y1aazkf6UZwqf3ndt8y0lVE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_links = {}

# Заглушка веб-сервера для Render, чтобы он видел открытый порт
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на видео (YouTube, TikTok и др.), и я предложу скачать его.")

@dp.message()
async def handle_url(message: types.Message):
    url = message.text
    if not url or not url.startswith("http"):
        await message.reply("Пожалуйста, отправь корректную ссылку на видео.")
        return

    user_links[message.from_user.id] = url

    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Скачать видео / файл", callback_data="download_media_file")
    builder.adjust(1)

    await message.answer("Нажми кнопку ниже, чтобы начать скачивание:", reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data == "download_media_file")
async def process_download(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if user_id not in user_links:
        await callback.message.edit_text("❌ Ссылка устарела. Отправьте её заново.")
        return

    url = user_links[user_id]
    await callback.message.edit_text("⏳ Скачиваю файл, подождите...")

    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'cookiefile': 'cookies.txt',
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:
            await callback.message.edit_text("❌ Файл слишком большой (больше 50 МБ). Telegram не разрешает ботам отправлять такие файлы.")
            if os.path.exists(filename):
                os.remove(filename)
            return

        await callback.message.edit_text("📤 Отправляю файл...")
        file_to_send = types.FSInputFile(filename)
        
        file_extension = info.get('ext', '')
        if file_extension in ['mp4', 'mkv', 'webm', 'mov']:
            await callback.message.answer_video(file_to_send)
        else:
            await callback.message.answer_document(file_to_send)

        await callback.message.delete()

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при скачивании: {str(e)}")

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

async def main():
    logging.basicConfig(level=logging.INFO)
    # Запускаем веб-сервер для Render и поллинг бота одновременно
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


import asyncio
import logging
import sqlite3
import os
import pandas as pd
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.media_group import MediaGroupBuilder
from aiohttp import web

logging.basicConfig(level=logging.INFO)

# ⚠️ O'ZINGIZNING HAQIQIY TOKEN VA ID-LARINGIZNI YOZING
BOT_TOKEN = "7331441395:AAH3mDpe6Gf7A2mev9XF"  
ADMIN_IDS = [5114777553]  

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# FSM Holatlari
class BotStates(StatesGroup):
    START = State()
    UPLOAD_FILE = State()

# Ma'lumotlar bazasini sozlash
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            fullname TEXT,
            class_name TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Tugmalar
def get_main_keyboard(user_id):
    buttons = []
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="📥 Fayl yuklash")])

    buttons.append([KeyboardButton(text="🔍 Qidirish")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.START)
    await message.answer(
        "Assalomu alaykum! Maktab maslahatchi botiga xush kelibsiz.",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@dp.message(lambda msg: msg.text == "📥 Fayl yuklash")
async def upload_file_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await state.set_state(BotStates.UPLOAD_FILE)
    await message.answer("Iltimos, Excel (.xlsx) faylini yuboring:")

@dp.message(BotStates.UPLOAD_FILE)
async def handle_docs(message: types.Message, state: FSMContext):
    if not message.document:
        await message.answer("Bu fayl emas. Iltimos, Excel fayl yuboring.")
        return

    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    destination = message.document.file_name

    await bot.download_file(file_path, destination)

    try:
        df = pd.read_excel(destination)

        required_columns = ['ID', 'FISM', 'Sinf']
        if not all(col in df.columns for col in required_columns):
            await message.answer("Xato: Excel faylda 'ID', 'FISM', 'Sinf' ustunlari bo'lishi shart!")
            return

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        added_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            s_id = str(row['ID']).strip()
            fullname = str(row['FISM']).strip()
            class_name = str(row['Sinf']).strip()
            try:
                cursor.execute("INSERT INTO students (id, fullname, class_name) VALUES (?, ?, ?)", (s_id, fullname, class_name))
                added_count += 1
            except sqlite3.IntegrityError:
                cursor.execute("UPDATE students SET fullname=?, class_name=? WHERE id=?", (fullname, class_name, s_id))
                skipped_count += 1

        conn.commit()
        conn.close()

        await message.answer(f"✅ Yuklash yakunlandi!\nYangi qo'shildi: {added_count}\nYangilandi: {skipped_count}")
    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {e}")
    finally:
        if os.path.exists(destination):
            os.remove(destination)
        await state.clear()

# Render uchun Veb Server (Portni eshitish qismi)
async def handle(request):
    return web.Response(text="Bot ishlamoqda...")

async def main():
    port = int(os.environ.get("PORT", 10000))
    app = web.Application()
    app.router.add_get('/', handle)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    asyncio.create_task(site.start())

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
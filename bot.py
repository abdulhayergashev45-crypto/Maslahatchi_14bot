import os
import sqlite3
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- BAZA ---
conn = sqlite3.connect("students.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS students 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, info TEXT, photo_id TEXT)""")
conn.commit()

# --- HOLATLAR ---
class BotStates(StatesGroup):
    waiting_for_name = State()

# --- MENYU ---
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 O'quvchini qidirish")
    builder.button(text="📊 Hisobot")
    builder.button(text="📁 Ijtimoiy portfel")
    builder.button(text="ℹ️ Bot haqida")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Assalomu alaykum! Maktab maslahatchisi tizimiga xush kelibsiz.", reply_markup=main_menu())

@dp.message(F.text == "🔍 O'quvchini qidirish")
async def start_search(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_name)
    await message.answer("O'quvchining ismini yozing (masalan: Aziz):")

@dp.message(BotStates.waiting_for_name)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.strip().lower()
    # Ism bo'yicha aniq qidiruv
    cursor.execute("SELECT info, photo_id FROM students WHERE LOWER(name) = ?", (query,))
    result = cursor.fetchone()
    
    if result:
        await message.answer_photo(photo=result[1], caption=f"👤 O'quvchi: {message.text}\n\n{result[0]}")
    else:
        await message.answer("❌ Bunday ismli o'quvchi topilmadi.")
    await state.clear()

# --- BOSHQA MENYULAR ---
@dp.message(F.text == "📊 Hisobot")
async def show_report(message: types.Message):
    await message.answer("📊 Hisobotlar bo'limi: Hozircha bo'sh.")

@dp.message(F.text == "📁 Ijtimoiy portfel")
async def show_portfolio(message: types.Message):
    await message.answer("📁 O'quvchilarning ijtimoiy portfeli.")

@dp.message(F.text == "ℹ️ Bot haqida")
async def show_info(message: types.Message):
    await message.answer("🤖 Maktab Maslahatchisi Boti v1.1")

# --- KEEP-ALIVE ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

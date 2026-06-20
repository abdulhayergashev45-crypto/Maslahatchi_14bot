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

# LOGGING
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- KEEP-ALIVE SERVERI ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()
    logging.info("Keep-Alive server 10000-portda ishga tushdi.")

# --- BAZA ---
conn = sqlite3.connect("students.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS students 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, info TEXT, photo_id TEXT)""")
conn.commit()

# --- HOLATLAR ---
class BotStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_add_name = State()
    waiting_for_add_info = State()
    waiting_for_add_photo = State()

# --- KLAVIATURA ---
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 O'quvchini qidirish")
    builder.button(text="📌 Asosiy vazifalar")
    builder.button(text="🛠 Asosiy funksiyalar")
    builder.button(text="ℹ️ Bot haqida")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Assalomu alaykum! Maktab maslahatchisining tizimiga xush kelibsiz.", reply_markup=main_menu())

@dp.message(F.text == "👤 O'quvchini qidirish")
async def start_search(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_name)
    await message.answer("Qidirilayotgan o'quvchining ismini kiriting:")

@dp.message(BotStates.waiting_for_name)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.lower()
    cursor.execute("SELECT info, photo_id FROM students WHERE name LIKE ?", ('%' + query + '%',))
    result = cursor.fetchone()
    if result:
        await message.answer_photo(photo=result[1], caption=f"🔍 Natija:\n\n{result[0]}")
    else:
        await message.answer("❌ Bunday o'quvchi topilmadi.")
    await state.clear()

@dp.message(Command("add"))
async def add_student(message: types.Message, state: FSMContext):
    await message.answer("O'quvchi ismini kiriting:")
    await state.set_state(BotStates.waiting_for_add_name)

@dp.message(BotStates.waiting_for_add_name)
async def add_info(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.lower())
    await message.answer("Ma'lumotni kiriting:")
    await state.set_state(BotStates.waiting_for_add_info)

@dp.message(BotStates.waiting_for_add_info)
async def add_photo(message: types.Message, state: FSMContext):
    await state.update_data(info=message.text)
    await message.answer("Rasmni yuboring:")
    await state.set_state(BotStates.waiting_for_add_photo)

@dp.message(BotStates.waiting_for_add_photo, F.photo)
async def save_student(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    cursor.execute("INSERT INTO students (name, info, photo_id) VALUES (?, ?, ?)", 
                   (data['name'], data['info'], photo_id))
    conn.commit()
    await message.answer("✅ Muvaffaqiyatli qo'shildi!", reply_markup=main_menu())
    await state.clear()

@dp.message(F.text == "📌 Asosiy vazifalar")
async def show_tasks(message: types.Message):
    await message.answer("🔹 Iqtidorli farzandlar loyihasi.\n🔹 To'garaklar nazorati.")

@dp.message(F.text == "🛠 Asosiy funksiyalar")
async def show_functions(message: types.Message):
    await message.answer("✅ Kasbga yo'naltirish.\n✅ Grant ma'lumotlari.")

@dp.message(F.text == "ℹ️ Bot haqida")
async def show_info(message: types.Message):
    await message.answer("🤖 Maktab Maslahatchisi Boti v1.0")

# --- ISHGA TUSHIRISH ---
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

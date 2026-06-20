import asyncio, os, sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiohttp import web
import pandas as pd

# Sozlamalar
BOT_TOKEN = "8834151202:AAGmoLHQcLiYJY58KAonOSJ8Ph1rYCn3z-I"
DB_PATH = "school_data.db"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Bazani yuklash
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS students (FIO TEXT, SINF TEXT, SINF_RAHBAR TEXT)")
    conn.commit()
    conn.close()

init_db()

class States(StatesGroup):
    SEARCH = State()

# Menyuni doimiy qilish uchun funksiya
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔍 Qidirish")]], 
        resize_keyboard=True,
        is_persistent=True # Tugma doimiy turadi
    )

@dp.message(CommandStart())
async def start(msg: types.Message):
    await msg.answer("Maktab maslahatchisi botiga xush kelibsiz!", reply_markup=main_kb())

@dp.message(F.text == "🔍 Qidirish")
async def search_start(msg: types.Message, state: FSMContext):
    await state.set_state(States.SEARCH)
    await msg.answer("O'quvchining ismini kiriting:", reply_markup=ReplyKeyboardRemove())

@dp.message(States.SEARCH)
async def perform_search(msg: types.Message, state: FSMContext):
    query = msg.text.lower()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # SQL orqali qidirish (tezroq)
    cursor.execute("SELECT FIO, SINF FROM students WHERE FIO LIKE ?", (f'%{query}%',))
    results = cursor.fetchall()
    conn.close()
    
    if results:
        text = "🔎 Topilgan o'quvchilar:\n\n"
        for r in results:
            text += f"👤 {r[0]}\n📚 Sinf: {r[1]}\n\n"
        await msg.answer(text, reply_markup=main_kb())
    else:
        await msg.answer("Afsus, bunday o'quvchi topilmadi.", reply_markup=main_kb())
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

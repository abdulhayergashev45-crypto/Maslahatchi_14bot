import os
import sqlite3
import pandas as pd
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# Tokenni Render'dagi Environment o'zgaruvchisidan oling
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Baza va Excel nomlari
DB_FILE = "students.db"
EXCEL_FILE = "Baza 2025-2026 (2).xlsx"

# Baza yaratish funksiyasi
def init_db():
    try:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            conn = sqlite3.connect(DB_FILE)
            # Ustun nomlari kodga mos kelishi kerak
            df.to_sql('students', conn, if_exists='replace', index=False)
            conn.close()
            logging.info("Ma'lumotlar bazasi muvaffaqiyatli yaratildi.")
        else:
            logging.error(f"Xatolik: {EXCEL_FILE} fayli topilmadi!")
    except Exception as e:
        logging.error(f"Baza yaratishda xato: {e}")

# Ishga tushganda bazani tayyorlash
init_db()

# Menyu
def get_main_menu():
    kb = [
        [types.KeyboardButton(text="🔍 O'quvchini qidirish")],
        [types.KeyboardButton(text="📊 Hisobot"), types.KeyboardButton(text="📁 Ijtimoiy portfel")],
        [types.KeyboardButton(text="ℹ️ Bot haqida")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

class SearchStates(StatesGroup):
    waiting_for_name = State()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Assalomu alaykum! Maktab maslahatchisi tizimi.", reply_markup=get_main_menu())

@dp.message(F.text == "🔍 O'quvchini qidirish")
async def ask_name(message: types.Message, state: FSMContext):
    await message.answer("O'quvchining ismini yozing:")
    await state.set_state(SearchStates.waiting_for_name)

@dp.message(SearchStates.waiting_for_name)
async def search_student(message: types.Message, state: FSMContext):
    query = message.text.lower().strip()
    conn = sqlite3.connect(DB_FILE)
    try:
        # SQL orqali qidiruv
        query_sql = f"SELECT * FROM students WHERE LOWER([Полное наименование]) LIKE '%{query}%'"
        df = pd.read_sql_query(query_sql, conn)
        
        if not df.empty:
            # Birinchi natijani ko'rsatish
            row = df.iloc[0]
            await message.answer(f"👤 Natija: {row['Полное наименование']}\n📌 Sinf: {row['Класс']}", reply_markup=get_main_menu())
        else:
            await message.answer("❌ Bunday ismli o'quvchi topilmadi.", reply_markup=get_main_menu())
    except Exception as e:
        logging.error(f"Qidiruv xatosi: {e}")
        await message.answer("⚠️ Baza bilan xatolik yuz berdi.", reply_markup=get_main_menu())
    conn.close()
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

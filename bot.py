import os
import sqlite3
import pandas as pd
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# TOKENni Render'da "Environment Variables" qismiga qo'shing
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- MENYU ---
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 O'quvchini qidirish")
    builder.button(text="📊 Hisobot")
    builder.button(text="📁 Ijtimoiy portfel")
    builder.button(text="ℹ️ Bot haqida")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# --- BAZA YARATISH (Excel'dan) ---
def init_db():
    db_file = "students.db"
    excel_file = 'Baza 2025-2026 (2).xlsx'
    
    # Excel fayl mavjudligini tekshirish
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file)
        # Baza faylini toza holatda yaratish
        conn = sqlite3.connect(db_file)
        df.to_sql('students', conn, if_exists='replace', index=False)
        conn.close()
        print("Bazaga ma'lumotlar muvaffaqiyatli yuklandi!")
    else:
        print(f"Xatolik: {excel_file} topilmadi!")

# Bot ishga tushganda bazani tayyorlaydi
init_db()

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Assalomu alaykum! Maktab maslahatchisi tizimi.", reply_markup=main_menu())

@dp.message(F.text == "🔍 O'quvchini qidirish")
async def start_search(message: types.Message, state: FSMContext):
    await message.answer("O'quvchining ismini yozing:")
    await state.set_state("waiting_for_name")

@dp.message(F.state == "waiting_for_name")
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.lower()
    
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    # Eslatma: Excel ustun nomi aniq "Полное наименование" bo'lishi kerak
    cursor.execute("SELECT * FROM students WHERE LOWER([Полное наименование]) LIKE ?", ('%' + query + '%',))
    result = cursor.fetchone()
    conn.close()

    if result:
        # Natijani chiroyli formatda chiqarish
        await message.answer(f"👤 Natija: {result[0]}\n📌 Sinf: {result[1]}", reply_markup=main_menu())
    else:
        await message.answer("❌ Bunday ismli o'quvchi topilmadi.", reply_markup=main_menu())
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

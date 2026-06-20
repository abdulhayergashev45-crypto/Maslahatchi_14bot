import sqlite3
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

TOKEN = "TOKENINGIZNI_SHU_YERGA_YAZING"
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

# EXCEL'DAN BAZANI YARATISH (Har safar ishga tushganda yangilaydi)
def init_db():
    df = pd.read_excel('Baza 2025-2026 (2).xlsx')
    conn = sqlite3.connect("students.db")
    df.to_sql('students', conn, if_exists='replace', index=False)
    conn.close()

init_db()

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
    # Excel ustunlaringizga mos so'rov (Полное наименование ustuni 'name' deb nomlangan deb faraz qilamiz)
    cursor.execute("SELECT * FROM students WHERE LOWER([Полное наименование]) LIKE ?", ('%' + query + '%',))
    result = cursor.fetchone()
    conn.close()

    if result:
        # result[0] - ismi, result[1] - sinfi
        await message.answer(f"👤 Natija: {result[0]}\n📌 Sinf: {result[1]}", reply_markup=main_menu())
    else:
        await message.answer("❌ Bunday ismli o'quvchi topilmadi.", reply_markup=main_menu())
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

import os
import sqlite3
import pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Holatlar
class BotStates(StatesGroup):
    waiting_for_name = State()

# Menyuni qayta tiklash
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 O'quvchini qidirish")
    builder.button(text="📊 Hisobot")
    builder.button(text="📁 Ijtimoiy portfel")
    builder.button(text="ℹ️ Bot haqida")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Assalomu alaykum! Maktab maslahatchisi tizimi.", reply_markup=main_menu())

@dp.message(F.text == "🔍 O'quvchini qidirish")
async def start_search(message: types.Message, state: FSMContext):
    await message.answer("Iltimos, o'quvchining ismini yozing:")
    await state.set_state(BotStates.waiting_for_name)

@dp.message(BotStates.waiting_for_name)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.lower().strip()
    
    # Baza faylini ochish
    conn = sqlite3.connect("students.db")
    # Jadval nomini tekshiring! Exceldan olingan jadval nomi 'students' bo'lishi shart
    try:
        df = pd.read_sql_query(f"SELECT * FROM students WHERE LOWER([Полное наименование]) LIKE '%{query}%'", conn)
        
        if not df.empty:
            result_text = "👤 Topilgan natijalar:\n\n"
            for index, row in df.iterrows():
                result_text += f"🔹 {row['Полное наименование']} — Sinf: {row['Класс']}\n"
            await message.answer(result_text, reply_markup=main_menu())
        else:
            await message.answer("❌ Bunday ismli o'quvchi topilmadi.", reply_markup=main_menu())
    except Exception as e:
        await message.answer(f"⚠️ Xatolik yuz berdi: {e}")
    
    conn.close()
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

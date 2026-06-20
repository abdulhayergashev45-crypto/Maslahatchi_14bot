import os
import pandas as pd
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Loglar
logging.basicConfig(level=logging.INFO)

# Tokenni muhit o'zgaruvchisidan olish
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Excel fayl nomi
EXCEL_FILE = "Baza 2025-2026 (2).xlsx"

class Search(StatesGroup):
    name = State()

def main_menu():
    kb = [
        [types.KeyboardButton(text="🔍 O'quvchini qidirish")],
        [types.KeyboardButton(text="📊 Hisobot"), types.KeyboardButton(text="📁 Ijtimoiy portfel")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Assalomu alaykum! Maktab maslahatchisi tizimi.", reply_markup=main_menu())

@dp.message(F.text == "🔍 O'quvchini qidirish")
async def ask_name(message: types.Message, state: FSMContext):
    await message.answer("O'quvchining ismini yozing:")
    await state.set_state(Search.name)

@dp.message(Search.name)
async def find_student(message: types.Message, state: FSMContext):
    query = message.text.lower().strip()
    
    try:
        df = pd.read_excel(EXCEL_FILE)
        # Ismni qidirish (ustun nomi aniq bo'lishi kerak, masalan: 'Полное наименование')
        result = df[df['Полное наименование'].astype(str).str.contains(query, case=False, na=False)]
        
        if not result.empty:
            ans = "✅ Topilgan natijalar:\n"
            for _, row in result.iterrows():
                ans += f"🔹 {row['Полное наименование']} | Sinf: {row['Класс']}\n"
            await message.answer(ans, reply_markup=main_menu())
        else:
            await message.answer("❌ Bunday ismli o'quvchi topilmadi.", reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("⚠️ Ma'lumotlar bazasida xatolik yuz berdi.", reply_markup=main_menu())
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

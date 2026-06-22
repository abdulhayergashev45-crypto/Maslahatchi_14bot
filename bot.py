import os
import pandas as pd
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Loglar
logging.basicConfig(level=logging.INFO)

# TOKENni shu yerga kiriting (xavfsizlik uchun .env ishlatish tavsiya etiladi)
TOKEN = "8834151202:AAGCOWr4FswvIGIWQJbmGHcYRTwVerSvxkA" 
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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
    
    if not os.path.exists(EXCEL_FILE):
        await message.answer("⚠️ Xatolik: Baza fayli topilmadi!")
        await state.clear()
        return

    try:
        df = pd.read_excel(EXCEL_FILE)
        # Ustun nomlari borligini tekshirish
        if 'Полное наименование' not in df.columns or 'Класс' not in df.columns:
            await message.answer("⚠️ Xatolik: Excel fayldagi ustun nomlari mos kelmayapti.")
            await state.clear()
            return

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
        await message.answer("⚠️ Ma'lumotlarni o'qishda xatolik yuz berdi.", reply_markup=main_menu())
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

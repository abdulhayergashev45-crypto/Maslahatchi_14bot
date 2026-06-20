import os
import sqlite3
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# BAZANI SOZLASH
conn = sqlite3.connect("students.db")
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS students 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, info TEXT, photo_id TEXT)""")
conn.commit()

class BotStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_add_name = State()
    waiting_for_add_info = State()
    waiting_for_add_photo = State()

# --- ADMIN FUNKSIYALARI ---
@dp.message(Command("add"))
async def add_student(message: types.Message, state: FSMContext):
    await message.answer("O'quvchi ismini kiriting:")
    await state.set_state(BotStates.waiting_for_add_name)

@dp.message(BotStates.waiting_for_add_name)
async def add_info(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.lower())
    await message.answer("O'quvchi haqida ma'lumotni kiriting:")
    await state.set_state(BotStates.waiting_for_add_info)

@dp.message(BotStates.waiting_for_add_info)
async def add_photo(message: types.Message, state: FSMContext):
    await state.update_data(info=message.text)
    await message.answer("O'quvchi rasmini yuboring:")
    await state.set_state(BotStates.waiting_for_add_photo)

@dp.message(BotStates.waiting_for_add_photo, F.photo)
async def save_student(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_id = message.photo[-1].file_id
    cursor.execute("INSERT INTO students (name, info, photo_id) VALUES (?, ?, ?)", 
                   (data['name'], data['info'], photo_id))
    conn.commit()
    await message.answer("✅ O'quvchi bazaga qo'shildi!")
    await state.clear()

# --- FOYDALANUVCHI FUNKSIYALARI ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 O'quvchini qidirish")
    builder.adjust(1)
    await message.answer("Assalomu alaykum!", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text == "👤 O'quvchini qidirish")
async def search_student(message: types.Message, state: FSMContext):
    await message.answer("Ismni yozing:")
    await state.set_state(BotStates.waiting_for_name)

@dp.message(BotStates.waiting_for_name)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.lower()
    cursor.execute("SELECT info, photo_id FROM students WHERE name LIKE ?", ('%' + query + '%',))
    result = cursor.fetchone()
    
    if result:
        await message.answer_photo(photo=result[1], caption=f"🔍 Natija:\n\n{result[0]}")
    else:
        await message.answer("❌ Topilmadi. 💡 <b>EBR</b> orqali tekshiring.", parse_mode="HTML")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

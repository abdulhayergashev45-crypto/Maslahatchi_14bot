import asyncio
import logging
import sqlite3
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# O'z tokeningiz va admin IDingizni kiriting
BOT_TOKEN = "8834151202:AAGmoLHQcLiYJY58KAonOSJ8Ph1rYCn3z-I"  
ADMIN_IDS = [1396115927]  

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Baza yo'li (Render uchun /tmp/ papkasi xavfsiz)
DB_PATH = "/tmp/database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            fullname TEXT,
            class_name TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Menyu tugmalari (Rasm asosida)
def get_main_keyboard(user_id):
    buttons = [
        [KeyboardButton(text="🎓 Kasbga yo'naltirish")],
        [KeyboardButton(text="🎨 To'garaklar"), KeyboardButton(text="🏛️ Loyihalar")],
        [KeyboardButton(text="🔍 Qidirish")]
    ]
    if user_id in ADMIN_IDS:
        buttons.append([KeyboardButton(text="📥 Fayl yuklash")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

class BotStates(StatesGroup):
    UPLOAD_FILE = State()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "Assalomu alaykum! Maktab maslahatchi botiga xush kelibsiz. Kerakli bo'limni tanlang:",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

# Yangi menyu funksiyalari
@dp.message(lambda msg: msg.text == "🎓 Kasbga yo'naltirish")
async def show_career(message: types.Message):
    await message.answer("🎓 **Kasbga yo'naltirish:** 7-9 sinf o'quvchilarini kasb-hunarga yo'naltirish, psixologik testlar va 'Prezident iqtidorli farzandlari' dasturi bo'yicha ma'lumotlar.")

@dp.message(lambda msg: msg.text == "🎨 To'garaklar")
async def show_clubs(message: types.Message):
    await message.answer("🎨 **To'garaklar:** Madaniyat, Robototexnika, San'at, Kitobxonlik va Sport yo'nalishlari.")

@dp.message(lambda msg: msg.text == "🏛️ Loyihalar")
async def show_projects(message: types.Message):
    await message.answer("🏛️ **Loyiha va tashabbuslar:** 'Turon teatr', 'Jadidlar izidan', 'Eco-schools' va 'Raqamli avlod' klublari faoliyati.")

# Qidirish funksiyasi
@dp.message(lambda msg: msg.text == "🔍 Qidirish")
async def search_student(message: types.Message):
    await message.answer("Ma'lumotlar bazasidan qidirish funksiyasi (Hozircha test rejimida).")

# Fayl yuklash (Admin uchun)
@dp.message(lambda msg: msg.text == "📥 Fayl yuklash")
async def upload_file_start(message: types.Message, state: FSMContext):
    if message.from_user.id in ADMIN_IDS:
        await state.set_state(BotStates.UPLOAD_FILE)
        await message.answer("Iltimos, Excel faylni (.xlsx) yuboring:")

@dp.message(BotStates.UPLOAD_FILE)
async def handle_docs(message: types.Message, state: FSMContext):
    if message.document:
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        destination = message.document.file_name
        await bot.download_file(file.file_path, destination)
        
        df = pd.read_excel(destination)
        conn = sqlite3.connect(DB_PATH)
        df.to_sql('students', conn, if_exists='append', index=False)
        conn.close()
        
        await message.answer("✅ Ma'lumotlar bazaga muvaffaqiyatli saqlandi!")
        os.remove(destination)
        await state.clear()

# Render uchun Veb Server
async def handle(request):
    return web.Response(text="Bot ishlamoqda...")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

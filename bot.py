import asyncio, os, sqlite3, pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web
from transliterate import translit

def to_latin(text):
    return translit(text, 'uz', reversed=True)
# Sozlamalar
BOT_TOKEN = "8834151202:AAGmoLHQcLiYJY58KAonOSJ8Ph1rYCn3z-I"
DB_PATH = "school_data.db"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 1. Matnni birlashtirish funksiyasi (Lotinlashtirish)
def normalize(text):
    if not text: return ""
    return to_latin(str(text)).lower().replace("`", "'").replace("‘", "'").replace("’", "'")

# 2. Bazani yuklash va tayyorlash
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS students (FIO TEXT, SINF TEXT, SINF_RAHBAR TEXT)")
    
    # "Baza 2025-2026 (2).xlsx" faylidan yuklash
    if cursor.execute("SELECT count(*) FROM students").fetchone()[0] == 0:
        if os.path.exists("Baza 2025-2026 (2).xlsx"):
            df = pd.read_excel("Baza 2025-2026 (2).xlsx", header=4)
            df.columns = ['FIO', 'SINF', 'SINF_RAHBAR']
            df.to_sql('students', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()

init_db()

class States(StatesGroup):
    SEARCH = State()

@dp.message(CommandStart())
async def start(msg: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔍 Qidirish")]], resize_keyboard=True)
    await msg.answer("Maktab maslahatchisi botiga xush kelibsiz! O'quvchini qidirish uchun tugmani bosing.", reply_markup=kb)

@dp.message(F.text == "🔍 Qidirish")
async def search_start(msg: types.Message, state: FSMContext):
    await state.set_state(States.SEARCH)
    await msg.answer("O'quvchining ismi yoki familiyasini kiriting:")

@dp.message(States.SEARCH)
async def perform_search(msg: types.Message, state: FSMContext):
    query = normalize(msg.text)
    conn = sqlite3.connect(DB_PATH)
    students = pd.read_sql("SELECT * FROM students", conn)
    conn.close()
    
    # Qidiruv logikasi
    results = students[students['FIO'].apply(lambda x: query in normalize(x))]
    
    if not results.empty:
        text = "🔎 Topilgan o'quvchilar:\n\n"
        for _, r in results.iterrows():
            text += f"👤 {r['FIO']}\n📚 Sinf: {r['SINF']}\n\n"
        await msg.answer(text)
    else:
        await msg.answer("Afsus, bunday o'quvchi topilmadi.")
    await state.clear()

# 24/7 ishlashi uchun web server
async def web_app():
    app = web.Application()
    return app

async def main():
    runner = web.AppRunner(await web_app())
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio, logging, sqlite3, os, pandas as pd
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiohttp import web

# Sozlamalar
BOT_TOKEN = "8834151202:AAGmoLHQcLiYJY58KAonOSJ8Ph1rYCn3z-I"
ADMIN_IDS = [1396115927]
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
DB_PATH = "/tmp/database.db"

# Bazani sozlash va Exceldan yuklash
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS students (id TEXT PRIMARY KEY, fullname TEXT, class_name TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS portfolio (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, content TEXT)")
    
    # Exceldan avtomatik yuklash
    cursor.execute("SELECT count(*) FROM students")
    if cursor.fetchone()[0] == 0 and os.path.exists("students.xlsx"):
        df = pd.read_excel("students.xlsx")
        df.to_sql('students', conn, if_exists='append', index=False)
        logging.info("Excel fayldan o'quvchilar bazasi yuklandi.")
            
    conn.commit()
    conn.close()
init_db()

class States(StatesGroup):
    PORTFOLIO = State()

def get_keyboard(user_id):
    btns = [[KeyboardButton(text="🎓 Kasbga yo'naltirish"), KeyboardButton(text="📂 Ijtimoiy portfolio")],
            [KeyboardButton(text="🎨 To'garaklar"), KeyboardButton(text="🏛️ Loyihalar")],
            [KeyboardButton(text="🔍 Qidirish")]]
    if user_id in ADMIN_IDS: 
        btns.append([KeyboardButton(text="📊 Hisobot olish")])
    return ReplyKeyboardMarkup(keyboard=btns, resize_keyboard=True)

@dp.message(CommandStart())
async def start(msg: types.Message):
    await msg.answer("Maktab maslahatchisi botiga xush kelibsiz!", reply_markup=get_keyboard(msg.from_user.id))

@dp.message(F.text == "📂 Ijtimoiy portfolio")
async def start_portfolio(msg: types.Message, state: FSMContext):
    await state.set_state(States.PORTFOLIO)
    await msg.answer("Yutuqlaringizni yuboring (matn yoki rasm):")

@dp.message(States.PORTFOLIO)
async def save_portfolio(msg: types.Message, state: FSMContext):
    content = msg.text or msg.caption or "Rasm yuborildi"
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO portfolio (user_id, content) VALUES (?, ?)", (str(msg.from_user.id), content))
    conn.commit()
    conn.close()
    await msg.answer("✅ Yutuqlaringiz qabul qilindi!")
    await state.clear()

@dp.message(F.text == "📊 Hisobot olish")
async def report(msg: types.Message):
    if msg.from_user.id not in ADMIN_IDS: return
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM portfolio", conn)
    conn.close()
    df.to_excel("Hisobot.xlsx", index=False)
    await msg.answer_document(FSInputFile("Hisobot.xlsx"))

# Boshqa oddiy javoblar
@dp.message(F.text == "🎓 Kasbga yo'naltirish")
async def show_career(msg: types.Message): await msg.answer("🎓 Kasbga yo'naltirish bo'yicha ma'lumotlar.")
@dp.message(F.text == "🎨 To'garaklar")
async def show_clubs(msg: types.Message): await msg.answer("🎨 To'garaklarimiz ro'yxati...")
@dp.message(F.text == "🏛️ Loyihalar")
async def show_projects(msg: types.Message): await msg.answer("🏛️ Joriy loyihalarimiz...")

async def main():
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000)))
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

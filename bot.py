import os
import logging
import asyncio
import cyrtranslit
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# LOGGING
logging.basicConfig(level=logging.INFO)

# TOKEN (Render'da 'TOKEN' nomli Environment Variable qo'shishni unutmang)
TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# HOLATLAR
class BotStates(StatesGroup):
    waiting_for_name = State()

# MA'LUMOTLAR BAZASI
STUDENTS_DATA = {
    "abduvohidov alisher": """Ism: Abduvohidov Alisher
Sinf: 10-A
Yutuqlari: Matematika olimpiadasi g'olibi
Yo'nalishi: IT va Dasturlash""",
    
    "karimova nigora": """Ism: Karimova Nigora
Sinf: 11-B
Yutuqlari: "Yosh kitobxon" tanlovi ishtirokchisi
Yo'nalishi: Filologiya""",
    
    "aliyev ali": """Ism: Aliyev Ali
Sinf: 9-V
Ijtimoiy holati: Namunali
Qiziqishi: Robototexnika"""
}

# YORDAMCHI FUNKSIYALAR
def normalize_text(text: str) -> str:
    if not text:
        return ""
    return cyrtranslit.to_latin(text.lower()).strip()

# KLAVIATURA
def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 O'quvchini qidirish")
    builder.button(text="📌 Asosiy vazifalar")
    builder.button(text="🛠 Asosiy funksiyalar")
    builder.button(text="ℹ️ Bot haqida")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# HANDLERLAR
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Assalomu alaykum! Maktab maslahatchisining tizimiga xush kelibsiz.",
        reply_markup=main_menu_keyboard()
    )

@dp.message(F.text == "👤 O'quvchini qidirish")
async def start_search(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_name)
    await message.answer("Qidirilayotgan o'quvchining ismini kiriting:")

@dp.message(BotStates.waiting_for_name)
async def process_search(message: types.Message, state: FSMContext):
    query = normalize_text(message.text)
    found = False
    for name_key, info in STUDENTS_DATA.items():
        if query in name_key:
            await message.answer(f"🔍 Natija:\n\n{info}")
            found = True
            break
    if not found:
        await message.answer("❌ O'quvchi topilmadi.")
    await state.clear()

@dp.message(F.text == "📌 Asosiy vazifalar")
async def show_tasks(message: types.Message):
    await message.answer("<b>Vazifalar:</b>\n\n🔹 Iqtidorli farzandlar loyihasi.\n🔹 To'garaklar nazorati.", parse_mode="HTML")

@dp.message(F.text == "🛠 Asosiy funksiyalar")
async def show_functions(message: types.Message):
    await message.answer("<b>Funksiyalar:</b>\n\n✅ Kasbga yo'naltirish.\n✅ Grant ma'lumotlari.", parse_mode="HTML")

@dp.message(F.text == "ℹ️ Bot haqida")
async def show_info(message: types.Message):
    await message.answer("🤖 <b>Maktab Maslahatchisi Boti v1.0</b>", parse_mode="HTML")

# ISHGA TUSHIRISH
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

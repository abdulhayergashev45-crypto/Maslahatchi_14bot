import os
import logging
import asyncio
import cyrtranslit
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# 1. LOGGING VA KONFIGURATSIYA
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TOKEN") # Renderda Environment Variable qilib kiritasiz

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. HOLATLAR (FSM)
class BotStates(StatesGroup):
    waiting_for_name = State()

# 3. MA'LUMOTLAR BAZASI (NAMUNA)
# Bu yerga o'quvchilarni qo'shib chiqasiz. Kalit so'z har doim lotin kichik harflarida bo'lsin.
STUDENTS_DATA = {
    'abduvohidov alisher': 'Ism: Abduvohidov Alisher\nSinf: 10-A\nYutuqlari: Matematika olimpiadasi g'olibi\nYo'nalishi: IT va Dasturlash',
    'karimova nigora': 'Ism: Karimova Nigora\nSinf: 11-B\nYutuqlari: 'Yosh kitobxon' tanlovi ishtirokchisi\nYo'nalishi: Filologiya',
    'aliyev ali': 'Ism: Aliyev Ali\nSinf: 9-V\nIjtimoiy holati: Namunali\nQiziqishi: Robototexnika'
}

# 4. YORDAMCHI FUNKSIYALAR
def normalize_text(text: str):
    """Matnni lotin alifbosiga o'giradi va kichik harflarga o'tkazadi"""
    if not text:
        return ""
    # Agar matn krill bo'lsa lotinga o'giradi, bo'lmasa o'zini qoldiradi
    converted = cyrtranslit.to_latin(text.lower())
    return converted.strip()

# 5. KLAVIATURA (MENYU)
def main_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 O'quvchini qidirish")
    builder.button(text="📌 Asosiy vazifalar")
    builder.button(text="🛠 Asosiy funksiyalar")
    builder.button(text="ℹ️ Bot haqida")
    builder.adjust(2) # Tugmalarni 2 qatordan teradi
    return builder.as_markup(resize_keyboard=True)

# 6. HANDLERLAR (BUYRUQLAR VA MATNLAR)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Assalomu alaykum! Maktab maslahatchisining avtomatlashtirilgan tizimiga xush kelibsiz.\n"
        "Kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard()
    )

# 6.1 O'quvchini qidirish (Ism bo'yicha)
@dp.message(F.text == "👤 O'quvchini qidirish")
async def start_search(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_name)
    await message.answer("Qidirilayotgan o'quvchining F.I.Sh. yoki ismini kiriting (Lotin yoki Krillda):")

@dp.message(BotStates.waiting_for_name)
async def process_search(message: types.Message, state: FSMContext):
    query = normalize_text(message.text)
    found = False
    
    # Bazadan qidirish
    for name_key, info in STUDENTS_DATA.items():
        if query in name_key: # To'liq yoki qisman mos kelishini tekshiradi
            await message.answer(f"🔍 Natija:\n\n{info}")
            found = True
            break
            
    if not found:
        await message.answer("❌ Afsuski, bunday ismli o'quvchi ma'lumotlar bazasida topilmadi.")
    
    await state.clear() # Qidiruv tugagach holatni tozalaymiz

# 6.2 Asosiy Vazifalar (Rasmda keltirilgan ma'lumotlar)
@dp.message(F.text == "📌 Asosiy vazifalar")
async def show_tasks(message: types.Message):
    tasks_text = (
        "<b>Maktab maslahatchisining asosiy vazifalari:</b>\n\n"
        "🔹 Prezident iqtidorli farzandlari loyihasini muvofiqlashtirish.\n"
        "🔹 Fan to'garaklari va sport seksiyalari faoliyatini nazorat qilish.\n"
        "🔹 O'quvchilar kengashi va ijtimoiy portfolioni yuritish.\n"
        "🔹 Ma'naviy-ma'rifiy ishlar va tarbiyaviy tadbirlarni tashkil etish."
    )
    await message.answer(tasks_text, parse_mode="HTML")

# 6.3 Asosiy Funksiyalar
@dp.message(F.text == "🛠 Asosiy funksiyalar")
async def show_functions(message: types.Message):
    functions_text = (
        "<b>Maslahatchining asosiy funksiyalari:</b>\n\n"
        "✅ O'quvchilarni kasb-hunarga yo'naltirish.\n"
        "✅ Iqtidorli yoshlarni aniqlash va metodik qo'llab-quvvatlash.\n"
        "✅ Grant va olimpiadalar haqida ma'lumot berish.\n"
        "✅ O'quvchilarning bo'sh vaqtini mazmunli tashkil etish."
    )
    await message.answer(functions_text, parse_mode="HTML")

# 6.4 Bot haqida ma'lumot
@dp.message(F.text == "ℹ️ Bot haqida")
async def show_info(message: types.Message):
    info_text = (
        "🤖 <b>Maktab Maslahatchisi Boti</b>\n\n"
        "Ushbu bot maktab o'quvchilari haqidagi ma'lumotlarni tezkor qidirish "
        "va maslahatchi ish faoliyatini raqamlashtirish uchun ishlab chiqilgan.\n\n"
        "Dasturchi: @SizningUsername"
    )
    await message.answer(info_text, parse_mode="HTML")

# 7. BOTNI ISHGA TUSHIRISH
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")

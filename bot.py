"""
Maktab Maslahatchisi Telegram Bot - v3
"""

import asyncio
import logging
import os
import sqlite3
from datetime import datetime

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from telegram.constants import ParseMode
import anthropic

# ─── SOZLAMALAR ────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

# ─── STATES ────────────────────────────────────────────────────────────────────
(
    MAIN_MENU,
    ADD_STUDENT_NAME, ADD_STUDENT_CLASS, ADD_STUDENT_DATA,
    SEARCH_STUDENT,
    PORTFOLIO_REQUEST,
    ADD_CLUB_NAME, ADD_CLUB_DIRECTION, ADD_CLUB_RESPONSIBLE,
    ADD_ACHIEVEMENT_STUDENT, ADD_ACHIEVEMENT_TITLE, ADD_ACHIEVEMENT_TYPE, ADD_ACHIEVEMENT_DATE,
    AI_CHAT,
) = range(14)

# ─── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─── DATABASE ──────────────────────────────────────────────────────────────────
DB_PATH = "maktab.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            class_name TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS student_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id),
            media_type TEXT,
            content TEXT,
            caption TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            direction TEXT,
            responsible TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS club_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id INTEGER REFERENCES clubs(id),
            student_id INTEGER REFERENCES students(id),
            joined_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id),
            title TEXT,
            achievement_type TEXT,
            date TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()
    logger.info("✅ Database tayyor")

def get_db():
    return sqlite3.connect(DB_PATH)

# ─── CLAUDE AI ─────────────────────────────────────────────────────────────────
def generate_portfolio(student_name: str, student_data: list) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    data_text = "\n".join([
        f"[{d['added_at'][:10]}] {d['media_type'].upper()}: {d['content']}"
        + (f" ({d['caption']})" if d['caption'] else "")
        for d in student_data
    ])
    prompt = f"""Siz maktab maslahatchisisiz. O'quvchi haqida professional IJTIMOIY PORTFEL tayyorlang.

O'quvchi: {student_name}
Ma'lumotlar:
{data_text}

Portfelni O'zbek tilida yozing:

📋 IJTIMOIY PORTFEL: {student_name}
━━━━━━━━━━━━━━━━━━━━━━━━
👤 UMUMIY MA'LUMOT
🏆 YUTUQLAR VA MUVAFFAQIYATLAR
🎭 TO'GARAKLAR VA FAOLIYATLAR
🎯 KELAJAK REJALARI
💡 SHAXSIY SIFATLAR
📊 MASLAHATCHI XULOSASI
━━━━━━━━━━━━━━━━━━━━━━━━"""
    message = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def ask_claude_guide(user_message: str, context_menu: str) -> str:
    """AI maslahat + botdan foydalanish qo'llanmasi"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    system = f"""Siz maktab maslahatchisi botining aqlli yordamchisisiz.

Sizning ikkita vazifangiz bor:
1. Maktab maslahatchisiga KASB YO'NALTIRISH, O'QUVCHILAR, TO'GARAKLAR, YUTUQLAR haqida maslahat bering
2. Bot funksiyalarini qanday ishlatishni O'ZBEK TILIDA tushuntiring

BOT BUYRUQLARI VA FUNKSIYALARI:
━━━━━━━━━━━━━━━━━━━━━━━━
👨‍🎓 O'QUVCHILAR BOSHQARUVI:
• "👨‍🎓 O'quvchilar boshqaruvi" tugmasi → o'quvchi qo'shish, qidirish menyu
• Yangi o'quvchi qo'shish: "➕ Yangi o'quvchi" → ism → sinf → ID beriladi
• Ma'lumot qo'shish: /add_media <ID> → matn/rasm/video yuboring → /done
• Misol: /add_media 5 → "Jasur matematika olimpiadasida 1-o'rin oldi" → /done

🏆 YUTUQLAR:
• "🏆 Yutuq va olimpiadalar" tugmasi → "➕ Yutuq qo'shish"
• O'quvchi ismini kiriting → yutuq nomini → turini → sanani

🎭 TO'GARAKLAR:
• "🎭 To'garaklar" tugmasi → "➕ To'garak qo'shish"
• YOKI /add_togarak <nom> → masalan: /add_togarak Robototexnika
• To'garak nomini → yo'nalishini → mas'ulini kiriting

🎯 KASB YO'NALTIRISH:
• "🎯 Kasb yo'naltirish" tugmasi → universitetlar, AI maslahat

📋 PORTFEL:
• "📋 Portfel yaratish" → o'quvchi ism yoki ID kiriting
• AI avtomatik professional portfel tayyorlaydi

━━━━━━━━━━━━━━━━━━━━━━━━
Hozirgi menyu konteksti: {context_menu}

Foydalanuvchi savoli yoki muammosiga qarab:
- Agar bot funksiyasi haqida so'rasa → aniq buyruq va qadamlarni ko'rsating
- Agar kasb/ta'lim haqida so'rasa → professional maslahat bering
- Har doim O'zbek tilida, qisqa va aniq javob bering
- Emoji ishlatib, chiroyli formatlang"""

    message = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": user_message}]
    )
    return message.content[0].text

# ─── KLAVIATURA ────────────────────────────────────────────────────────────────
def main_keyboard():
    keyboard = [
        [KeyboardButton("👨‍🎓 O'quvchilar boshqaruvi"), KeyboardButton("🏆 Yutuq va olimpiadalar")],
        [KeyboardButton("🎭 To'garaklar va yo'nalishlar"), KeyboardButton("🎯 Kasb yo'naltirish")],
        [KeyboardButton("📋 Portfel yaratish"), KeyboardButton("❓ Yordam va AI maslahat")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def check_admin(update: Update) -> bool:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Bu bot faqat maktab maslahatchisi uchun.")
        return False
    return True

# ─── AI MASLAHAT (barcha menyularda ishlaydi) ──────────────────────────────────
async def send_ai_help(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                        question: str, menu_name: str):
    """Istalgan menyudan AI ga savol yuborish"""
    msg = await update.message.reply_text("🤔 AI o'ylamoqda...")
    try:
        answer = ask_claude_guide(question, menu_name)
        await msg.edit_text(f"🤖 *AI Maslahat:*\n\n{answer}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Xato: {e}")

# ─── START ─────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    user = update.effective_user
    welcome = f"""🏫 *Maktab Maslahatchisi Bot* — v3

Assalomu alaykum, *{user.first_name}*! 👋

Quyidagi menyulardan foydalaning.
Har qanday savol uchun *❓ Yordam va AI maslahat* tugmasini bosing.

💡 _Tez boshlash uchun:_
• O'quvchi qo'shish → 👨‍🎓 tugma
• To'garak qo'shish → /add\\_togarak Robototexnika
• Portfel → 📋 tugma"""
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=main_keyboard())
    context.user_data.clear()
    return MAIN_MENU

# ─── MENYU 1: O'QUVCHILAR ──────────────────────────────────────────────────────
async def students_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Yangi o'quvchi qo'shish", callback_data="add_student")],
        [InlineKeyboardButton("🔍 O'quvchi qidirish", callback_data="search_student")],
        [InlineKeyboardButton("📋 Barcha o'quvchilar", callback_data="list_students")],
        [InlineKeyboardButton("❓ Bu menyudan qanday foydalanaman?", callback_data="ai_help_students")],
    ]
    await update.message.reply_text(
        "👨‍🎓 *O'QUVCHILAR BOSHQARUVI*\n\nNima qilmoqchisiz?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "➕ *Yangi o'quvchi qo'shish*\n\nO'quvchining to'liq ismini kiriting:\n_(Masalan: Karimov Jasur Aliyevich)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_STUDENT_NAME

async def add_student_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_student_name"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Ism: *{context.user_data['new_student_name']}*\n\nSinfini kiriting _(9-A, 11-B)_:",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_STUDENT_CLASS

async def add_student_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data["new_student_name"]
    class_name = update.message.text.strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO students (full_name, class_name) VALUES (?, ?)", (name, class_name))
    student_id = c.lastrowid
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ *{name}* ({class_name}) qo'shildi!\n"
        f"🆔 ID: `{student_id}`\n\n"
        f"📁 Ma'lumot qo'shish uchun:\n`/add_media {student_id}`\n\n"
        f"_Keyin matn, rasm yoki video yuboring, tugatgach /done_",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

async def search_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔍 O'quvchi ismini yoki sinfini kiriting:")
    return SEARCH_STUDENT

async def search_student_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search = update.message.text.strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, full_name, class_name FROM students WHERE full_name LIKE ? OR class_name LIKE ? LIMIT 10",
              (f"%{search}%", f"%{search}%"))
    results = c.fetchall()
    conn.close()
    if not results:
        await update.message.reply_text("❌ Topilmadi. Qayta urinib ko'ring.")
        return MAIN_MENU
    keyboard = [[InlineKeyboardButton(f"👤 {name} ({cls or '—'})", callback_data=f"student_profile_{sid}")]
                for sid, name, cls in results]
    await update.message.reply_text(f"🔍 *{len(results)} ta natija:*",
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    return MAIN_MENU

async def list_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, full_name, class_name FROM students ORDER BY class_name, full_name LIMIT 30")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await query.message.reply_text("📭 Hali o'quvchilar kiritilmagan.")
        return
    text = "📋 *BARCHA O'QUVCHILAR:*\n\n"
    for sid, name, cls in rows:
        text += f"`{sid}` | {name} | {cls or '—'}\n"
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def show_student_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    student_id = int(query.data.split("_")[-1])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT full_name, class_name, created_at FROM students WHERE id=?", (student_id,))
    student = c.fetchone()
    if not student:
        await query.message.reply_text("❌ Topilmadi.")
        conn.close()
        return
    name, cls, created = student
    c.execute("SELECT COUNT(*) FROM student_media WHERE student_id=?", (student_id,))
    media_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM achievements WHERE student_id=?", (student_id,))
    ach_count = c.fetchone()[0]
    conn.close()
    text = (f"👤 *{name}*\n📚 Sinf: {cls or '—'}\n"
            f"📅 Qo'shilgan: {created[:10]}\n"
            f"📁 Ma'lumotlar: {media_count} ta\n🏆 Yutuqlar: {ach_count} ta")
    keyboard = [
        [InlineKeyboardButton("📋 Portfel yaratish", callback_data=f"gen_portfolio_{student_id}")],
        [InlineKeyboardButton("📁 Ma'lumot qo'shish", callback_data=f"add_media_{student_id}")],
        [InlineKeyboardButton("🏆 Yutuq qo'shish", callback_data=f"add_ach_{student_id}")],
    ]
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(keyboard))

# ─── MEDIA QO'SHISH ────────────────────────────────────────────────────────────
async def add_media_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    if not context.args:
        await update.message.reply_text(
            "❗ *Ishlatilishi:* `/add_media <o'quvchi_ID>`\n\n"
            "Masalan: `/add_media 3`\n\n"
            "O'quvchi ID sini bilish uchun 👨‍🎓 menyusidan qidiring.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    try:
        student_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❗ ID raqam bo'lishi kerak. Masalan: /add_media 5")
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT full_name FROM students WHERE id=?", (student_id,))
    student = c.fetchone()
    conn.close()
    if not student:
        await update.message.reply_text(
            f"❌ ID={student_id} li o'quvchi topilmadi.\n"
            "👨‍🎓 menyusidan o'quvchilar ro'yxatini ko'ring."
        )
        return
    context.user_data["target_student_id"] = student_id
    context.user_data["target_student_name"] = student[0]
    await update.message.reply_text(
        f"📁 *{student[0]}* uchun ma'lumot qabul qilinmoqda\n\n"
        f"Istalgan narsani yuboring:\n"
        f"📝 *Matn* — yutuq, tavsif, izoh\n"
        f"🖼 *Rasm* — diplom, sertifikat, foto\n"
        f"🎥 *Video* — musobaqa, taqdimot\n"
        f"📄 *Hujjat* — PDF sertifikat\n\n"
        f"✅ Tugatish uchun: /done",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_STUDENT_DATA

async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    student_id = context.user_data.get("target_student_id")
    if not student_id:
        return MAIN_MENU
    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()
    if update.message.text and not update.message.text.startswith("/"):
        c.execute("INSERT INTO student_media (student_id, media_type, content, added_at) VALUES (?,?,?,?)",
                  (student_id, "text", update.message.text, now))
        await update.message.reply_text("✅ Matn saqlandi! Yana yuborishingiz mumkin.")
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        c.execute("INSERT INTO student_media (student_id, media_type, content, caption, added_at) VALUES (?,?,?,?,?)",
                  (student_id, "photo", file_id, update.message.caption or "", now))
        await update.message.reply_text("✅ Rasm saqlandi!")
    elif update.message.video:
        file_id = update.message.video.file_id
        c.execute("INSERT INTO student_media (student_id, media_type, content, caption, added_at) VALUES (?,?,?,?,?)",
                  (student_id, "video", file_id, update.message.caption or "", now))
        await update.message.reply_text("✅ Video saqlandi!")
    elif update.message.document:
        file_id = update.message.document.file_id
        c.execute("INSERT INTO student_media (student_id, media_type, content, caption, added_at) VALUES (?,?,?,?,?)",
                  (student_id, "document", file_id, update.message.caption or "", now))
        await update.message.reply_text("✅ Hujjat saqlandi!")
    conn.commit()
    conn.close()
    return ADD_STUDENT_DATA

async def done_adding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data.get("target_student_name", "O'quvchi")
    context.user_data.pop("target_student_id", None)
    context.user_data.pop("target_student_name", None)
    await update.message.reply_text(
        f"✅ *{name}* uchun ma'lumot saqlash yakunlandi!\n\n"
        f"📋 Portfel yaratish uchun tugmani bosing.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

# ─── MENYU 2: YUTUQLAR ─────────────────────────────────────────────────────────
async def achievements_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Yutuq qo'shish", callback_data="add_achievement")],
        [InlineKeyboardButton("📊 Barcha yutuqlar", callback_data="list_achievements")],
        [InlineKeyboardButton("❓ Bu menyudan qanday foydalanaman?", callback_data="ai_help_achievements")],
    ]
    await update.message.reply_text(
        "🏆 *YUTUQ VA OLIMPIADALAR*\n\nO'quvchilarning barcha yutuqlarini bu yerda boshqaring.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_achievement_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "🏆 *Yutuq qo'shish*\n\nO'quvchi ismini kiriting:",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_ACHIEVEMENT_STUDENT

async def add_achievement_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search = update.message.text.strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, full_name, class_name FROM students WHERE full_name LIKE ? LIMIT 5", (f"%{search}%",))
    results = c.fetchall()
    conn.close()
    if not results:
        await update.message.reply_text("❌ O'quvchi topilmadi. Ismini to'liqroq kiriting:")
        return ADD_ACHIEVEMENT_STUDENT
    if len(results) == 1:
        context.user_data["ach_student_id"] = results[0][0]
        context.user_data["ach_student_name"] = results[0][1]
        await update.message.reply_text(
            f"✅ *{results[0][1]}* tanlandi.\n\nYutuq nomini kiriting:\n_(Masalan: Viloyat matematika olimpiadasi 1-o'rin)_",
            parse_mode=ParseMode.MARKDOWN
        )
        return ADD_ACHIEVEMENT_TITLE
    keyboard = [[InlineKeyboardButton(f"{name} ({cls or '—'})", callback_data=f"ach_select_{sid}")]
                for sid, name, cls in results]
    await update.message.reply_text("Qaysi o'quvchi?", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_ACHIEVEMENT_STUDENT

async def ach_select_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    student_id = int(query.data.split("_")[-1])
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT full_name FROM students WHERE id=?", (student_id,))
    row = c.fetchone()
    conn.close()
    context.user_data["ach_student_id"] = student_id
    context.user_data["ach_student_name"] = row[0]
    await query.message.reply_text(
        f"✅ *{row[0]}* tanlandi.\n\nYutuq nomini kiriting:\n_(Masalan: Respublika matematika olimpiadasi 2-o'rin)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_ACHIEVEMENT_TITLE

async def add_achievement_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ach_title"] = update.message.text.strip()
    keyboard = [
        [InlineKeyboardButton("🧮 Olimpiada", callback_data="ach_type_olimpiada")],
        [InlineKeyboardButton("⚽ Sport", callback_data="ach_type_sport")],
        [InlineKeyboardButton("🎨 San'at/Madaniyat", callback_data="ach_type_sanat")],
        [InlineKeyboardButton("💻 Texnologiya", callback_data="ach_type_texnologiya")],
        [InlineKeyboardButton("📌 Boshqa", callback_data="ach_type_boshqa")],
    ]
    await update.message.reply_text("Yutuq turini tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_ACHIEVEMENT_TYPE

async def ach_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ach_type"] = query.data.replace("ach_type_", "")
    await query.message.reply_text(
        "📅 Sanani kiriting:\n_(Masalan: 2024-03-15 yoki 2024-yil mart)_"
    )
    return ADD_ACHIEVEMENT_DATE

async def add_achievement_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = update.message.text.strip()
    student_id = context.user_data["ach_student_id"]
    student_name = context.user_data["ach_student_name"]
    title = context.user_data["ach_title"]
    ach_type = context.user_data["ach_type"]
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO achievements (student_id, title, achievement_type, date) VALUES (?,?,?,?)",
              (student_id, title, ach_type, date))
    # O'quvchi mediasiga ham qo'shamiz
    c.execute("INSERT INTO student_media (student_id, media_type, content, added_at) VALUES (?,?,?,?)",
              (student_id, "text", f"YUTUQ: {title} ({ach_type}) — {date}", datetime.now().isoformat()))
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ *{student_name}* ning yutuqi saqlandi!\n\n"
        f"🏆 {title}\n📌 Tur: {ach_type}\n📅 Sana: {date}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

async def list_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT s.full_name, s.class_name, a.title, a.achievement_type, a.date
                 FROM achievements a JOIN students s ON a.student_id = s.id
                 ORDER BY a.added_at DESC LIMIT 20""")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await query.message.reply_text("📭 Hali yutuqlar kiritilmagan.\n➕ Yutuq qo'shish tugmasini bosing.")
        return
    icons = {"olimpiada": "🧮", "sport": "⚽", "sanat": "🎨", "texnologiya": "💻", "boshqa": "📌"}
    text = "🏆 *SO'NGGI YUTUQLAR:*\n\n"
    for name, cls, title, atype, date in rows:
        icon = icons.get(atype, "🏅")
        text += f"{icon} *{name}* ({cls or '—'})\n   {title} — {date or '—'}\n\n"
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─── MENYU 3: TO'GARAKLAR ─────────────────────────────────────────────────────
async def clubs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ To'garak qo'shish", callback_data="add_club_btn")],
        [InlineKeyboardButton("📋 Barcha to'garaklar", callback_data="list_clubs")],
        [InlineKeyboardButton("👥 O'quvchini to'garakka qo'shish", callback_data="add_club_member")],
        [InlineKeyboardButton("❓ Bu menyudan qanday foydalanaman?", callback_data="ai_help_clubs")],
    ]
    await update.message.reply_text(
        "🎭 *TO'GARAKLAR VA YO'NALISHLAR*\n\n"
        "Tez qo'shish: `/add_togarak <nom>`\n"
        "Masalan: `/add_togarak Robototexnika`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_togarak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buyruq: /add_togarak <nom>"""
    if not await check_admin(update):
        return
    if not context.args:
        await update.message.reply_text(
            "❗ *Ishlatilishi:* `/add_togarak <to'garak nomi>`\n\n"
            "Masalan:\n"
            "`/add_togarak Robototexnika`\n"
            "`/add_togarak Matematika klubi`\n"
            "`/add_togarak Futbol seksiyasi`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    club_name = " ".join(context.args)
    context.user_data["new_club_name"] = club_name
    keyboard = [
        [InlineKeyboardButton("🎨 Madaniyat", callback_data="club_dir_madaniyat"),
         InlineKeyboardButton("💻 Texnologiya", callback_data="club_dir_texnologiya")],
        [InlineKeyboardButton("⚽ Sport", callback_data="club_dir_sport"),
         InlineKeyboardButton("🎭 San'at", callback_data="club_dir_sanat")],
        [InlineKeyboardButton("🌿 Ekologiya", callback_data="club_dir_ekologiya"),
         InlineKeyboardButton("📌 Boshqa", callback_data="club_dir_boshqa")],
    ]
    await update.message.reply_text(
        f"✅ To'garak nomi: *{club_name}*\n\nYo'nalishini tanlang:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADD_CLUB_DIRECTION

async def add_club_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugma orqali to'garak qo'shish"""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "➕ *To'garak nomini kiriting:*\n_(Masalan: Robototexnika, Matematika klubi)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_CLUB_NAME

async def add_club_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    club_name = update.message.text.strip()
    context.user_data["new_club_name"] = club_name
    keyboard = [
        [InlineKeyboardButton("🎨 Madaniyat", callback_data="club_dir_madaniyat"),
         InlineKeyboardButton("💻 Texnologiya", callback_data="club_dir_texnologiya")],
        [InlineKeyboardButton("⚽ Sport", callback_data="club_dir_sport"),
         InlineKeyboardButton("🎭 San'at", callback_data="club_dir_sanat")],
        [InlineKeyboardButton("🌿 Ekologiya", callback_data="club_dir_ekologiya"),
         InlineKeyboardButton("📌 Boshqa", callback_data="club_dir_boshqa")],
    ]
    await update.message.reply_text(
        f"✅ Nom: *{club_name}*\n\nYo'nalishini tanlang:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADD_CLUB_DIRECTION

async def club_direction_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["new_club_direction"] = query.data.replace("club_dir_", "")
    await query.message.reply_text(
        "👤 Mas'ul o'qituvchi ismini kiriting:\n_(Masalan: Karimov Alisher)_"
    )
    return ADD_CLUB_RESPONSIBLE

async def add_club_responsible(update: Update, context: ContextTypes.DEFAULT_TYPE):
    responsible = update.message.text.strip()
    name = context.user_data["new_club_name"]
    direction = context.user_data["new_club_direction"]
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO clubs (name, direction, responsible) VALUES (?, ?, ?)",
              (name, direction, responsible))
    conn.commit()
    conn.close()
    icons = {"madaniyat": "🎨", "texnologiya": "💻", "sport": "⚽", 
             "sanat": "🎭", "ekologiya": "🌿", "boshqa": "📌"}
    icon = icons.get(direction, "📌")
    await update.message.reply_text(
        f"✅ *To'garak qo'shildi!*\n\n"
        f"{icon} *{name}*\n"
        f"📂 Yo'nalish: {direction}\n"
        f"👤 Mas'ul: {responsible}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

async def list_clubs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT cl.name, cl.direction, cl.responsible, COUNT(cm.id)
                 FROM clubs cl LEFT JOIN club_members cm ON cl.id = cm.club_id
                 GROUP BY cl.id ORDER BY cl.direction, cl.name""")
    rows = c.fetchall()
    conn.close()
    if not rows:
        await query.message.reply_text(
            "📭 Hali to'garaklar kiritilmagan.\n\n"
            "Qo'shish uchun: `/add_togarak Robototexnika`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    icons = {"madaniyat": "🎨", "texnologiya": "💻", "sport": "⚽",
             "sanat": "🎭", "ekologiya": "🌿", "boshqa": "📌"}
    text = "🎭 *TO'GARAKLAR RO'YXATI:*\n\n"
    current_dir = None
    for name, direction, responsible, count in rows:
        if direction != current_dir:
            icon = icons.get(direction, "📌")
            text += f"\n{icon} *{(direction or 'Boshqa').upper()}*\n"
            current_dir = direction
        text += f"  • {name} | 👤 {responsible or '—'} | 👥 {count} a'zo\n"
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def add_club_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM clubs ORDER BY name")
    clubs = c.fetchall()
    conn.close()
    if not clubs:
        await query.message.reply_text("📭 Avval to'garak qo'shing: /add_togarak <nom>")
        return
    keyboard = [[InlineKeyboardButton(name, callback_data=f"club_join_{cid}")]
                for cid, name in clubs]
    await query.message.reply_text("Qaysi to'garakka?", reply_markup=InlineKeyboardMarkup(keyboard))

# ─── MENYU 4: KASB YO'NALTIRISH ───────────────────────────────────────────────
async def career_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏫 Top universitetlar", callback_data="universities_info")],
        [InlineKeyboardButton("📝 MOCK imtihon ma'lumoti", callback_data="mock_info")],
        [InlineKeyboardButton("❓ Kasb tanlashda maslahat", callback_data="ai_help_career")],
    ]
    await update.message.reply_text(
        "🎯 *KASB YO'NALTIRISH*\n\nO'quvchilarning kelajak rejalari:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def universities_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = """🏫 *TOP UNIVERSITETLAR*

🇺🇿 *O'ZBEKISTON:*
• TDTU — Texnika
• NUU — Universitetlar
• INHA University — IT
• Westminster International — Biznes/Huquq
• TSUL — Yuridik

🌍 *XALQARO (Top-300):*
• MIT, Stanford, Harvard — AQSh
• Oxford, Cambridge — Britaniya
• KAIST, Yonsei — Koreya
• NUS, NTU — Singapur
• POSTECH — Koreya

📝 *Qabul talablari:*
• IELTS 6.0+ / TOEFL 80+
• SAT / ACT (AQSh uchun)
• Milliy sertifikat (O'zbekiston)

❓ Aniq kasb bo'yicha maslahat uchun AI ga yozing!"""
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def mock_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = """📝 *MOCK IMTIHON MA'LUMOTI*

MOCK imtihon — o'quvchilarga haqiqiy DTM/SAT imtihoniga tayyorgarlik uchun o'tkaziladigan sinov.

*Maktab maslahatchisi vazifalari:*
• PM bilan hamkorlikda MOCK tashkil etish
• Natijalarni tahlil qilish
• Zaif tomonlarni aniqlash
• Individual o'quv rejasi tuzish

*Foydali resurslar:*
• dtm.uz — rasmiy DTM sayti
• Khan Academy — bepul tayyorgarlik
• prep.uz — o'zbek test platformasi"""
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─── PORTFEL ───────────────────────────────────────────────────────────────────
async def portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *IJTIMOIY PORTFEL YARATISH*\n\n"
        "O'quvchi ismini yoki ID sini kiriting:\n"
        "_(Masalan: Karimov yoki 5)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return PORTFOLIO_REQUEST

async def generate_portfolio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search = update.message.text.strip()
    conn = get_db()
    c = conn.cursor()
    if search.isdigit():
        c.execute("SELECT id, full_name FROM students WHERE id=?", (int(search),))
    else:
        c.execute("SELECT id, full_name FROM students WHERE full_name LIKE ? LIMIT 1", (f"%{search}%",))
    student = c.fetchone()
    if not student:
        await update.message.reply_text(
            "❌ Topilmadi. Ismni to'liqroq kiriting yoki ID raqamini ishlating.\n"
            "👨‍🎓 menyusidan o'quvchilar ro'yxatini ko'ring."
        )
        conn.close()
        return MAIN_MENU
    student_id, student_name = student
    c.execute("SELECT media_type, content, caption, added_at FROM student_media WHERE student_id=? ORDER BY added_at",
              (student_id,))
    media_rows = c.fetchall()
    conn.close()
    if not media_rows:
        await update.message.reply_text(
            f"⚠️ *{student_name}* haqida ma'lumot yo'q.\n\n"
            f"Avval ma'lumot qo'shing:\n`/add_media {student_id}`",
            parse_mode=ParseMode.MARKDOWN
        )
        return MAIN_MENU
    msg = await update.message.reply_text(f"⏳ *{student_name}* portfeli tayyorlanmoqda...", parse_mode=ParseMode.MARKDOWN)
    media_data = [{"media_type": r[0], "content": r[1], "caption": r[2], "added_at": r[3]} for r in media_rows]
    try:
        portfolio_text = generate_portfolio(student_name, media_data)
        await msg.delete()
        await update.message.reply_text(portfolio_text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard())
    except Exception as e:
        await msg.edit_text(f"❌ Xato: {e}")
    return MAIN_MENU

# ─── YORDAM VA AI MASLAHAT ─────────────────────────────────────────────────────
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👨‍🎓 O'quvchi qo'shishni o'rgat", callback_data="ai_teach_student")],
        [InlineKeyboardButton("🎭 To'garak qo'shishni o'rgat", callback_data="ai_teach_club")],
        [InlineKeyboardButton("🏆 Yutuq qo'shishni o'rgat", callback_data="ai_teach_achievement")],
        [InlineKeyboardButton("📋 Portfel yaratishni o'rgat", callback_data="ai_teach_portfolio")],
        [InlineKeyboardButton("💬 O'z savolimni yozaman", callback_data="ai_free_chat")],
    ]
    await update.message.reply_text(
        "❓ *YORDAM VA AI MASLAHAT*\n\n"
        "Quyidagi mavzulardan birini tanlang yoki o'z savolingizni yozing:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ai_free_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["ai_chat_mode"] = True
    await query.message.reply_text(
        "💬 Savolingizni yozing — AI javob beradi:\n"
        "_(Botdan foydalanish, kasb maslahat, o'quvchi bilan ishlash...)_\n\n"
        "Chiqish uchun: /done"
    )
    return AI_CHAT

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text.strip()
    if question.startswith("/"):
        return MAIN_MENU
    await send_ai_help(update, context, question, "Umumiy yordam")
    return AI_CHAT

# ─── CALLBACK DISPATCHER ──────────────────────────────────────────────────────
AI_TEACH_TEXTS = {
    "ai_teach_student": "O'quvchi qo'shish va ma'lumot yuklash jarayonini qadam-qadam tushuntir",
    "ai_teach_club":    "To'garak qo'shish jarayonini buyruqlar bilan tushuntir",
    "ai_teach_achievement": "O'quvchiga yutuq qo'shish jarayonini tushuntir",
    "ai_teach_portfolio": "O'quvchi uchun ijtimoiy portfel yaratish jarayonini tushuntir",
    "ai_help_students": "O'quvchilar boshqaruvi menyusidagi barcha imkoniyatlarni tushuntir",
    "ai_help_achievements": "Yutuq va olimpiadalar menyusidagi barcha imkoniyatlarni tushuntir",
    "ai_help_clubs": "To'garaklar va yo'nalishlar menyusidagi barcha imkoniyatlarni tushuntir",
    "ai_help_career": "Kasb yo'naltirish bo'yicha maslahat ber va menyudagi imkoniyatlarni tushuntir",
}

async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # AI o'rgatish callbacklari
    if data in AI_TEACH_TEXTS:
        await query.answer()
        msg = await query.message.reply_text("🤔 AI o'ylamoqda...")
        try:
            answer = ask_claude_guide(AI_TEACH_TEXTS[data], data)
            await msg.edit_text(f"🤖 *AI Qo'llanma:*\n\n{answer}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ Xato: {e}")
        return

    if data == "ai_free_chat":
        return await ai_free_chat_start(update, context)
    elif data == "add_student":
        return await add_student_start(update, context)
    elif data == "search_student":
        return await search_student_start(update, context)
    elif data == "list_students":
        return await list_students(update, context)
    elif data == "add_achievement":
        return await add_achievement_start(update, context)
    elif data == "list_achievements":
        return await list_achievements(update, context)
    elif data == "add_club_btn":
        return await add_club_btn(update, context)
    elif data == "list_clubs":
        return await list_clubs(update, context)
    elif data == "add_club_member":
        return await add_club_member(update, context)
    elif data == "universities_info":
        return await universities_info(update, context)
    elif data == "mock_info":
        return await mock_info(update, context)
    elif data.startswith("club_dir_"):
        return await club_direction_selected(update, context)
    elif data.startswith("student_profile_"):
        return await show_student_profile(update, context)
    elif data.startswith("ach_select_"):
        return await ach_select_student(update, context)
    elif data.startswith("ach_type_"):
        return await ach_select_type(update, context)
    elif data.startswith("gen_portfolio_"):
        student_id = int(data.split("_")[-1])
        await query.answer()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT full_name FROM students WHERE id=?", (student_id,))
        row = c.fetchone()
        if row:
            msg = await query.message.reply_text(f"⏳ *{row[0]}* portfeli...", parse_mode=ParseMode.MARKDOWN)
            c.execute("SELECT media_type, content, caption, added_at FROM student_media WHERE student_id=?", (student_id,))
            media_rows = c.fetchall()
            conn.close()
            if media_rows:
                media_data = [{"media_type": r[0], "content": r[1], "caption": r[2], "added_at": r[3]} for r in media_rows]
                try:
                    portfolio_text = generate_portfolio(row[0], media_data)
                    await msg.edit_text(portfolio_text, parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    await msg.edit_text(f"❌ Xato: {e}")
            else:
                await msg.edit_text(f"⚠️ Ma'lumot yo'q. /add_media {student_id} ishlating.")
        else:
            conn.close()
    elif data.startswith("add_media_"):
        student_id = int(data.split("_")[-1])
        await query.answer()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT full_name FROM students WHERE id=?", (student_id,))
        row = c.fetchone()
        conn.close()
        if row:
            context.user_data["target_student_id"] = student_id
            context.user_data["target_student_name"] = row[0]
            await query.message.reply_text(
                f"📁 *{row[0]}* uchun ma'lumot yuboring:\n📝 Matn | 🖼 Rasm | 🎥 Video\n\nTugatish: /done",
                parse_mode=ParseMode.MARKDOWN
            )
    elif data.startswith("add_ach_"):
        student_id = int(data.split("_")[-1])
        await query.answer()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT full_name FROM students WHERE id=?", (student_id,))
        row = c.fetchone()
        conn.close()
        if row:
            context.user_data["ach_student_id"] = student_id
            context.user_data["ach_student_name"] = row[0]
            await query.message.reply_text(
                f"🏆 *{row[0]}* uchun yutuq nomini kiriting:",
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        await query.answer("⚙️ Tez orada...")

# ─── ASOSIY MENYU ROUTER ──────────────────────────────────────────────────────
async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return
    text = update.message.text
    routes = {
        "👨‍🎓 O'quvchilar boshqaruvi": students_menu,
        "🏆 Yutuq va olimpiadalar": achievements_menu,
        "🎭 To'garaklar va yo'nalishlar": clubs_menu,
        "🎯 Kasb yo'naltirish": career_menu,
        "📋 Portfel yaratish": portfolio_menu,
        "❓ Yordam va AI maslahat": help_menu,
        "🏠 Bosh menyu": start,
    }
    if text in routes:
        result = await routes[text](update, context)
        if result in (PORTFOLIO_REQUEST,):
            return result
        return MAIN_MENU
    # Media qo'shish rejimida
    if context.user_data.get("target_student_id"):
        return await receive_media(update, context)
    # AI chat rejimida
    if context.user_data.get("ai_chat_mode"):
        return await ai_chat_handler(update, context)
    return MAIN_MENU

# ─── MAIN ──────────────────────────────────────────────────────────────────────
async def main():
    init_db()
    logger.info("🚀 Bot ishga tushmoqda...")
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.ALL & ~filters.COMMAND, main_menu_router),
                CallbackQueryHandler(callback_dispatcher),
            ],
            ADD_STUDENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_name)],
            ADD_STUDENT_CLASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_class)],
            ADD_STUDENT_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_media),
                MessageHandler(filters.PHOTO, receive_media),
                MessageHandler(filters.VIDEO, receive_media),
                MessageHandler(filters.Document.ALL, receive_media),
                CommandHandler("done", done_adding),
            ],
            SEARCH_STUDENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_student_result)],
            PORTFOLIO_REQUEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_portfolio_handler)],
            ADD_CLUB_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_club_name)],
            ADD_CLUB_DIRECTION: [CallbackQueryHandler(club_direction_selected, pattern="^club_dir_")],
            ADD_CLUB_RESPONSIBLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_club_responsible)],
            ADD_ACHIEVEMENT_STUDENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_achievement_student),
                CallbackQueryHandler(ach_select_student, pattern="^ach_select_"),
            ],
            ADD_ACHIEVEMENT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_achievement_title)],
            ADD_ACHIEVEMENT_TYPE: [CallbackQueryHandler(ach_select_type, pattern="^ach_type_")],
            ADD_ACHIEVEMENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_achievement_date)],
            AI_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handler),
                CommandHandler("done", done_adding),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🏠 Bosh menyu$"), start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("add_media", add_media_cmd))
    app.add_handler(CommandHandler("add_togarak", add_togarak_cmd))
    app.add_handler(CallbackQueryHandler(callback_dispatcher))

    logger.info("✅ Bot tayyor!")
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        logger.info("✅ Bot ishlayapti!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

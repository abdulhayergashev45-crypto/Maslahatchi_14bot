"""
Maktab Maslahatchisi Bot - v4
Tuzatishlar:
- State muammosi hal qilindi
- To'garakka o'quvchi qo'shish ishlaydi
- Sinf kiritish to'g'ri ishlaydi
- proxies xatosi yo'q (yangi anthropic)
- Hisobot funksiyasi qo'shildi
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
    ADD_MEMBER_SEARCH, ADD_MEMBER_CLUB,
) = range(16)

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
            joined_at TEXT DEFAULT (datetime('now')),
            UNIQUE(club_id, student_id)
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
def get_claude():
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_portfolio(student_name: str, cls: str, student_data: list) -> str:
    client = get_claude()
    data_text = "\n".join([
        f"[{d['added_at'][:10]}] {d['media_type'].upper()}: {d['content']}"
        + (f" | Izoh: {d['caption']}" if d['caption'] else "")
        for d in student_data
    ])
    prompt = f"""Siz tajribali maktab maslahatchisisiz. Quyidagi o'quvchi haqida to'plangan ma'lumotlar asosida professional IJTIMOIY PORTFEL tayyorlang.

O'quvchi: {student_name}
Sinfi: {cls or "Noma'lum"}

To'plangan ma'lumotlar:
{data_text}

Portfelni O'zbek tilida professional tarzda yozing:

📋 IJTIMOIY PORTFEL
👤 Ism: {student_name} | Sinf: {cls or "—"}
📅 Sana: {datetime.now().strftime("%Y-%m-%d")}
━━━━━━━━━━━━━━━━━━━━━━━━

👤 UMUMIY MA'LUMOT
[O'quvchi haqida 2-3 jumla]

🏆 YUTUQLAR VA MUVAFFAQIYATLAR
[Barcha yutuqlar ro'yxati]

🎭 TO'GARAKLAR VA FAOLIYATLAR
[Qaysi to'garaklarda]

🎯 KELAJAK REJALARI
[Kasb va universitet]

💡 SHAXSIY SIFATLAR
[Ma'lumotlardan kelib chiqqan holda]

📊 MASLAHATCHI XULOSASI
[Professional baho]
━━━━━━━━━━━━━━━━━━━━━━━━"""
    message = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def generate_report(report_type: str, data: dict) -> str:
    client = get_claude()
    prompt = f"""Siz maktab maslahatchisisiz. Quyidagi ma'lumotlar asosida {report_type} hisobotini O'zbek tilida tayyorlang.

Ma'lumotlar:
{data}

Hisobotni professional va tartibli qiling. Statistika, tahlil va tavsiyalar bering."""
    message = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def ask_claude_guide(question: str, context_menu: str) -> str:
    client = get_claude()
    system = f"""Siz maktab maslahatchisi botining aqlli yordamchisisiz. O'zbek tilida aniq va foydali javob bering.

BOT BUYRUQLARI:
• /start — botni ishga tushirish
• /add_media <ID> — o'quvchiga ma'lumot qo'shish, keyin /done
• /add_togarak <nom> — to'garak qo'shish
• /hisobot — umumiy hisobot

MENYULAR:
👨‍🎓 O'quvchilar → qo'shish, qidirish, ro'yxat
🏆 Yutuqlar → qo'shish, ko'rish
🎭 To'garaklar → qo'shish, a'zo, ro'yxat
🎯 Kasb → universitetlar, maslahat
📋 Portfel → ism yoki ID kiriting
❓ Yordam → o'rgatish, AI suhbat
📊 Hisobot → umumiy/o'quvchi/to'garak hisobot

Hozirgi menyu: {context_menu}
Qisqa, aniq, emoji bilan javob bering."""
    message = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": question}]
    )
    return message.content[0].text

# ─── KLAVIATURA ────────────────────────────────────────────────────────────────
def main_keyboard():
    keyboard = [
        [KeyboardButton("👨‍🎓 O'quvchilar boshqaruvi"), KeyboardButton("🏆 Yutuq va olimpiadalar")],
        [KeyboardButton("🎭 To'garaklar va yo'nalishlar"), KeyboardButton("🎯 Kasb yo'naltirish")],
        [KeyboardButton("📋 Portfel yaratish"), KeyboardButton("❓ Yordam va AI maslahat")],
        [KeyboardButton("📊 Hisobot")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def is_admin(uid): return uid in ADMIN_IDS

async def check_admin(update):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Faqat maktab maslahatchisi uchun.")
        return False
    return True

# ─── START ─────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    context.user_data.clear()
    user = update.effective_user
    await update.message.reply_text(
        f"🏫 *Maktab Maslahatchisi Bot* v4\n\n"
        f"Assalomu alaykum, *{user.first_name}*! 👋\n\n"
        f"*Tez foydalanish:*\n"
        f"• O'quvchi qo'shish → 👨‍🎓\n"
        f"• To'garak → `/add_togarak Robototexnika`\n"
        f"• Ma'lumot → `/add_media <ID>`\n"
        f"• Portfel → 📋\n"
        f"• Hisobot → 📊",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

# ─── O'QUVCHILAR ───────────────────────────────────────────────────────────────
async def students_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Yangi o'quvchi qo'shish", callback_data="add_student")],
        [InlineKeyboardButton("🔍 O'quvchi qidirish", callback_data="search_student")],
        [InlineKeyboardButton("📋 Barcha o'quvchilar", callback_data="list_students")],
        [InlineKeyboardButton("❓ Qanday foydalanaman?", callback_data="ai_help_students")],
    ]
    await update.message.reply_text(
        "👨‍🎓 *O'QUVCHILAR BOSHQARUVI*", parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text("➕ O'quvchining *to'liq ismini* kiriting:\n_(Karimov Jasur Aliyevich)_",
                                parse_mode=ParseMode.MARKDOWN)
    return ADD_STUDENT_NAME

async def add_student_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_student_name"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Ism: *{context.user_data['new_student_name']}*\n\n"
        f"Sinfini kiriting:\n_(9-A, 10-B, 11-V ...)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_STUDENT_CLASS

async def add_student_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data["new_student_name"]
    class_name = update.message.text.strip()
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO students (full_name, class_name) VALUES (?, ?)", (name, class_name))
    sid = c.lastrowid; conn.commit(); conn.close()
    await update.message.reply_text(
        f"✅ *{name}* ({class_name}) qo'shildi!\n🆔 ID: `{sid}`\n\n"
        f"📁 Ma'lumot qo'shish:\n`/add_media {sid}`\n"
        f"_Keyin matn/rasm/video yuboring, /done bilan tugating_",
        parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard()
    )
    return MAIN_MENU

async def search_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text("🔍 Ism yoki sinf kiriting:")
    return SEARCH_STUDENT

async def search_student_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search = update.message.text.strip()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT id, full_name, class_name FROM students WHERE full_name LIKE ? OR class_name LIKE ? LIMIT 10",
              (f"%{search}%", f"%{search}%"))
    results = c.fetchall(); conn.close()
    if not results:
        await update.message.reply_text("❌ Topilmadi.", reply_markup=main_keyboard())
        return MAIN_MENU
    keyboard = [[InlineKeyboardButton(f"👤 {n} ({cls or '—'})", callback_data=f"student_profile_{sid}")]
                for sid, n, cls in results]
    await update.message.reply_text(f"🔍 *{len(results)} natija:*",
                                     parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    return MAIN_MENU

async def list_students_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT id, full_name, class_name FROM students ORDER BY class_name, full_name LIMIT 50")
    rows = c.fetchall(); conn.close()
    if not rows:
        await q.message.reply_text("📭 Hali o'quvchilar yo'q."); return
    text = "📋 *BARCHA O'QUVCHILAR:*\n\n"
    for sid, n, cls in rows:
        text += f"`{sid}` | {n} | {cls or '—'}\n"
    await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def show_student_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    sid = int(q.data.split("_")[-1])
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT full_name, class_name, created_at FROM students WHERE id=?", (sid,))
    s = c.fetchone()
    if not s: await q.message.reply_text("❌ Topilmadi."); conn.close(); return
    name, cls, created = s
    c.execute("SELECT COUNT(*) FROM student_media WHERE student_id=?", (sid,))
    mc = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM achievements WHERE student_id=?", (sid,))
    ac = c.fetchone()[0]
    c.execute("""SELECT cl.name FROM clubs cl 
                 JOIN club_members cm ON cl.id=cm.club_id WHERE cm.student_id=?""", (sid,))
    clubs = [r[0] for r in c.fetchall()]
    conn.close()
    clubs_text = ", ".join(clubs) if clubs else "—"
    text = (f"👤 *{name}*\n📚 Sinf: {cls or '—'}\n"
            f"📅 Qo'shilgan: {created[:10]}\n"
            f"📁 Ma'lumotlar: {mc} ta | 🏆 Yutuqlar: {ac} ta\n"
            f"🎭 To'garaklar: {clubs_text}")
    keyboard = [
        [InlineKeyboardButton("📋 Portfel yaratish", callback_data=f"gen_portfolio_{sid}")],
        [InlineKeyboardButton("📁 Ma'lumot qo'shish", callback_data=f"add_media_{sid}")],
        [InlineKeyboardButton("🏆 Yutuq qo'shish", callback_data=f"add_ach_{sid}")],
    ]
    await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                reply_markup=InlineKeyboardMarkup(keyboard))

# ─── MEDIA ─────────────────────────────────────────────────────────────────────
async def add_media_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    if not context.args:
        await update.message.reply_text(
            "❗ *Ishlatilishi:* `/add_media <ID>`\n\nMasalan: `/add_media 3`\n\n"
            "O'quvchi ID sini bilish → 👨‍🎓 → Barcha o'quvchilar",
            parse_mode=ParseMode.MARKDOWN); return
    try: sid = int(context.args[0])
    except: await update.message.reply_text("❗ ID raqam bo'lishi kerak."); return
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT full_name FROM students WHERE id=?", (sid,))
    s = c.fetchone(); conn.close()
    if not s:
        await update.message.reply_text(f"❌ ID={sid} topilmadi."); return
    context.user_data["target_student_id"] = sid
    context.user_data["target_student_name"] = s[0]
    await update.message.reply_text(
        f"📁 *{s[0]}* uchun ma'lumot qabul qilinmoqda\n\n"
        f"Yuboring: 📝 Matn | 🖼 Rasm | 🎥 Video | 📄 Hujjat\n\n✅ Tugash: /done",
        parse_mode=ParseMode.MARKDOWN)
    return ADD_STUDENT_DATA

async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = context.user_data.get("target_student_id")
    if not sid: return MAIN_MENU
    conn = get_db(); c = conn.cursor(); now = datetime.now().isoformat()
    msg = update.message
    if msg.text and not msg.text.startswith("/"):
        c.execute("INSERT INTO student_media (student_id,media_type,content,added_at) VALUES(?,?,?,?)",
                  (sid,"text",msg.text,now))
        await msg.reply_text("✅ Matn saqlandi!")
    elif msg.photo:
        fid = msg.photo[-1].file_id
        c.execute("INSERT INTO student_media (student_id,media_type,content,caption,added_at) VALUES(?,?,?,?,?)",
                  (sid,"photo",fid,msg.caption or "",now))
        await msg.reply_text("✅ Rasm saqlandi!")
    elif msg.video:
        fid = msg.video.file_id
        c.execute("INSERT INTO student_media (student_id,media_type,content,caption,added_at) VALUES(?,?,?,?,?)",
                  (sid,"video",fid,msg.caption or "",now))
        await msg.reply_text("✅ Video saqlandi!")
    elif msg.document:
        fid = msg.document.file_id
        c.execute("INSERT INTO student_media (student_id,media_type,content,caption,added_at) VALUES(?,?,?,?,?)",
                  (sid,"document",fid,msg.caption or "",now))
        await msg.reply_text("✅ Hujjat saqlandi!")
    conn.commit(); conn.close()
    return ADD_STUDENT_DATA

async def done_adding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data.pop("target_student_name", "O'quvchi")
    context.user_data.pop("target_student_id", None)
    context.user_data.pop("ai_chat_mode", None)
    await update.message.reply_text(
        f"✅ *{name}* uchun saqlash yakunlandi!\n📋 Portfel uchun tugmani bosing.",
        parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard())
    return MAIN_MENU

# ─── YUTUQLAR ──────────────────────────────────────────────────────────────────
async def achievements_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Yutuq qo'shish", callback_data="add_achievement")],
        [InlineKeyboardButton("📊 Barcha yutuqlar", callback_data="list_achievements")],
        [InlineKeyboardButton("❓ Qanday foydalanaman?", callback_data="ai_help_achievements")],
    ]
    await update.message.reply_text("🏆 *YUTUQ VA OLIMPIADALAR*", parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(keyboard))

async def add_achievement_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text("🏆 O'quvchi ismini kiriting:")
    return ADD_ACHIEVEMENT_STUDENT

async def add_achievement_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search = update.message.text.strip()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT id,full_name,class_name FROM students WHERE full_name LIKE ? LIMIT 5", (f"%{search}%",))
    results = c.fetchall(); conn.close()
    if not results:
        await update.message.reply_text("❌ Topilmadi. Ismni to'liqroq kiriting:"); return ADD_ACHIEVEMENT_STUDENT
    if len(results) == 1:
        context.user_data.update({"ach_sid": results[0][0], "ach_name": results[0][1]})
        await update.message.reply_text(
            f"✅ *{results[0][1]}* tanlandi.\n\nYutuq nomini kiriting:\n_(Viloyat matematika olimpiadasi 1-o'rin)_",
            parse_mode=ParseMode.MARKDOWN)
        return ADD_ACHIEVEMENT_TITLE
    kb = [[InlineKeyboardButton(f"{n} ({cls or '—'})", callback_data=f"ach_sel_{sid}")]
          for sid, n, cls in results]
    await update.message.reply_text("Qaysi o'quvchi?", reply_markup=InlineKeyboardMarkup(kb))
    return ADD_ACHIEVEMENT_STUDENT

async def ach_sel_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    sid = int(q.data.split("_")[-1])
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT full_name FROM students WHERE id=?", (sid,))
    row = c.fetchone(); conn.close()
    context.user_data.update({"ach_sid": sid, "ach_name": row[0]})
    await q.message.reply_text(
        f"✅ *{row[0]}* tanlandi.\n\nYutuq nomini kiriting:",
        parse_mode=ParseMode.MARKDOWN)
    return ADD_ACHIEVEMENT_TITLE

async def add_achievement_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["ach_title"] = update.message.text.strip()
    kb = [
        [InlineKeyboardButton("🧮 Olimpiada", callback_data="acht_olimpiada"),
         InlineKeyboardButton("⚽ Sport", callback_data="acht_sport")],
        [InlineKeyboardButton("🎨 San'at", callback_data="acht_sanat"),
         InlineKeyboardButton("💻 Texnologiya", callback_data="acht_texnologiya")],
        [InlineKeyboardButton("📌 Boshqa", callback_data="acht_boshqa")],
    ]
    await update.message.reply_text("Tur tanlang:", reply_markup=InlineKeyboardMarkup(kb))
    return ADD_ACHIEVEMENT_TYPE

async def ach_sel_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    context.user_data["ach_type"] = q.data.replace("acht_", "")
    await q.message.reply_text("📅 Sanani kiriting:\n_(Masalan: 2024-03-15)_")
    return ADD_ACHIEVEMENT_DATE

async def add_achievement_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = update.message.text.strip()
    sid = context.user_data["ach_sid"]
    name = context.user_data["ach_name"]
    title = context.user_data["ach_title"]
    atype = context.user_data["ach_type"]
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO achievements (student_id,title,achievement_type,date) VALUES(?,?,?,?)",
              (sid, title, atype, date))
    c.execute("INSERT INTO student_media (student_id,media_type,content,added_at) VALUES(?,?,?,?)",
              (sid, "text", f"YUTUQ: {title} ({atype}) — {date}", datetime.now().isoformat()))
    conn.commit(); conn.close()
    await update.message.reply_text(
        f"✅ *{name}* ning yutuqi saqlandi!\n🏆 {title}\n📌 {atype} | 📅 {date}",
        parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard())
    return MAIN_MENU

async def list_achievements_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    conn = get_db(); c = conn.cursor()
    c.execute("""SELECT s.full_name,s.class_name,a.title,a.achievement_type,a.date
                 FROM achievements a JOIN students s ON a.student_id=s.id
                 ORDER BY a.added_at DESC LIMIT 20""")
    rows = c.fetchall(); conn.close()
    if not rows:
        await q.message.reply_text("📭 Hali yutuqlar yo'q."); return
    icons = {"olimpiada":"🧮","sport":"⚽","sanat":"🎨","texnologiya":"💻","boshqa":"📌"}
    text = "🏆 *SO'NGGI YUTUQLAR:*\n\n"
    for n, cls, title, atype, date in rows:
        icon = icons.get(atype, "🏅")
        text += f"{icon} *{n}* ({cls or '—'})\n   {title} — {date or '—'}\n\n"
    await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─── TO'GARAKLAR ───────────────────────────────────────────────────────────────
async def clubs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ To'garak qo'shish", callback_data="add_club_btn")],
        [InlineKeyboardButton("📋 Barcha to'garaklar", callback_data="list_clubs")],
        [InlineKeyboardButton("👥 O'quvchini to'garakka qo'shish", callback_data="add_member_start")],
        [InlineKeyboardButton("❓ Qanday foydalanaman?", callback_data="ai_help_clubs")],
    ]
    await update.message.reply_text(
        "🎭 *TO'GARAKLAR VA YO'NALISHLAR*\n\n"
        "Tez qo'shish: `/add_togarak <nom>`",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

DIR_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🎨 Madaniyat", callback_data="cdir_madaniyat"),
     InlineKeyboardButton("💻 Texnologiya", callback_data="cdir_texnologiya")],
    [InlineKeyboardButton("⚽ Sport", callback_data="cdir_sport"),
     InlineKeyboardButton("🎭 San'at", callback_data="cdir_sanat")],
    [InlineKeyboardButton("🌿 Ekologiya", callback_data="cdir_ekologiya"),
     InlineKeyboardButton("📌 Boshqa", callback_data="cdir_boshqa")],
])

async def add_togarak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    if not context.args:
        await update.message.reply_text(
            "❗ *Ishlatilishi:* `/add_togarak <nom>`\n\nMasalan:\n"
            "`/add_togarak Robototexnika`\n`/add_togarak Matematika klubi`",
            parse_mode=ParseMode.MARKDOWN); return
    name = " ".join(context.args)
    context.user_data["new_club_name"] = name
    await update.message.reply_text(
        f"✅ To'garak: *{name}*\n\nYo'nalishini tanlang:",
        parse_mode=ParseMode.MARKDOWN, reply_markup=DIR_KEYBOARD)
    return ADD_CLUB_DIRECTION

async def add_club_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text("➕ To'garak nomini kiriting:")
    return ADD_CLUB_NAME

async def add_club_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["new_club_name"] = update.message.text.strip()
    await update.message.reply_text(
        f"✅ Nom: *{context.user_data['new_club_name']}*\n\nYo'nalish:",
        parse_mode=ParseMode.MARKDOWN, reply_markup=DIR_KEYBOARD)
    return ADD_CLUB_DIRECTION

async def club_dir_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    context.user_data["new_club_dir"] = q.data.replace("cdir_", "")
    await q.message.reply_text("👤 Mas'ul o'qituvchi ismini kiriting:")
    return ADD_CLUB_RESPONSIBLE

async def add_club_responsible(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resp = update.message.text.strip()
    name = context.user_data["new_club_name"]
    direction = context.user_data["new_club_dir"]
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO clubs (name,direction,responsible) VALUES(?,?,?)", (name,direction,resp))
    conn.commit(); conn.close()
    icons = {"madaniyat":"🎨","texnologiya":"💻","sport":"⚽","sanat":"🎭","ekologiya":"🌿","boshqa":"📌"}
    icon = icons.get(direction, "📌")
    await update.message.reply_text(
        f"✅ *To'garak qo'shildi!*\n\n{icon} *{name}*\n📂 {direction}\n👤 {resp}",
        parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard())
    return MAIN_MENU

async def list_clubs_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    conn = get_db(); c = conn.cursor()
    c.execute("""SELECT cl.name,cl.direction,cl.responsible,COUNT(cm.id)
                 FROM clubs cl LEFT JOIN club_members cm ON cl.id=cm.club_id
                 GROUP BY cl.id ORDER BY cl.direction,cl.name""")
    rows = c.fetchall(); conn.close()
    if not rows:
        await q.message.reply_text("📭 To'garaklar yo'q.\n`/add_togarak <nom>`", parse_mode=ParseMode.MARKDOWN); return
    icons = {"madaniyat":"🎨","texnologiya":"💻","sport":"⚽","sanat":"🎭","ekologiya":"🌿","boshqa":"📌"}
    text = "🎭 *TO'GARAKLAR:*\n\n"; cur_dir = None
    for n, d, resp, cnt in rows:
        if d != cur_dir:
            text += f"\n{icons.get(d,'📌')} *{(d or 'Boshqa').upper()}*\n"; cur_dir = d
        text += f"  • {n} | 👤 {resp or '—'} | 👥 {cnt}\n"
    await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─── TO'GARAKKA A'ZO QO'SHISH ──────────────────────────────────────────────────
async def add_member_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text("👥 O'quvchi ismini kiriting:")
    return ADD_MEMBER_SEARCH

async def add_member_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search = update.message.text.strip()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT id,full_name,class_name FROM students WHERE full_name LIKE ? LIMIT 8", (f"%{search}%",))
    results = c.fetchall(); conn.close()
    if not results:
        await update.message.reply_text("❌ Topilmadi. Qayta kiriting:"); return ADD_MEMBER_SEARCH
    if len(results) == 1:
        context.user_data["member_sid"] = results[0][0]
        context.user_data["member_name"] = results[0][1]
        return await show_clubs_for_member(update, context)
    kb = [[InlineKeyboardButton(f"{n} ({cls or '—'})", callback_data=f"msel_{sid}")]
          for sid, n, cls in results]
    await update.message.reply_text("Qaysi o'quvchi?", reply_markup=InlineKeyboardMarkup(kb))
    return ADD_MEMBER_SEARCH

async def member_sel_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    sid = int(q.data.split("_")[-1])
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT full_name FROM students WHERE id=?", (sid,))
    row = c.fetchone(); conn.close()
    context.user_data["member_sid"] = sid
    context.user_data["member_name"] = row[0]
    # Fake update for show_clubs
    return await show_clubs_for_member_cb(q, context)

async def show_clubs_for_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT id,name FROM clubs ORDER BY name")
    clubs = c.fetchall(); conn.close()
    if not clubs:
        await update.message.reply_text("📭 To'garaklar yo'q. Avval `/add_togarak <nom>`",
                                         parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    name = context.user_data["member_name"]
    kb = [[InlineKeyboardButton(cn, callback_data=f"mjoin_{cid}")] for cid, cn in clubs]
    await update.message.reply_text(
        f"👤 *{name}*\n\nQaysi to'garakka qo'shamiz?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))
    return ADD_MEMBER_CLUB

async def show_clubs_for_member_cb(query, context: ContextTypes.DEFAULT_TYPE):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT id,name FROM clubs ORDER BY name")
    clubs = c.fetchall(); conn.close()
    if not clubs:
        await query.message.reply_text("📭 To'garaklar yo'q."); return MAIN_MENU
    name = context.user_data["member_name"]
    kb = [[InlineKeyboardButton(cn, callback_data=f"mjoin_{cid}")] for cid, cn in clubs]
    await query.message.reply_text(
        f"👤 *{name}*\n\nQaysi to'garakka?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb))
    return ADD_MEMBER_CLUB

async def join_club(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    cid = int(q.data.split("_")[-1])
    sid = context.user_data["member_sid"]
    sname = context.user_data["member_name"]
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM clubs WHERE id=?", (cid,))
    club = c.fetchone()
    try:
        c.execute("INSERT INTO club_members (club_id,student_id) VALUES(?,?)", (cid, sid))
        c.execute("INSERT INTO student_media (student_id,media_type,content,added_at) VALUES(?,?,?,?)",
                  (sid,"text",f"TO'GARAK: {club[0]} ga a'zo bo'ldi",datetime.now().isoformat()))
        conn.commit()
        await q.message.reply_text(
            f"✅ *{sname}* → *{club[0]}* to'garakka qo'shildi!",
            parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard())
    except Exception:
        await q.message.reply_text(f"⚠️ *{sname}* allaqachon bu to'garakda.",
                                    parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard())
    conn.close()
    return MAIN_MENU

# ─── KASB YO'NALTIRISH ─────────────────────────────────────────────────────────
async def career_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏫 Top universitetlar", callback_data="universities_info")],
        [InlineKeyboardButton("📝 MOCK imtihon", callback_data="mock_info")],
        [InlineKeyboardButton("❓ Kasb tanlashda maslahat", callback_data="ai_help_career")],
    ]
    await update.message.reply_text("🎯 *KASB YO'NALTIRISH*", parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(keyboard))

async def universities_info_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text(
        "🏫 *TOP UNIVERSITETLAR*\n\n"
        "🇺🇿 *O'ZBEKISTON:*\nTDTU | NUU | INHA | Westminster | TSUL\n\n"
        "🌍 *XALQARO:*\nMIT, Stanford (AQSh) | Oxford (UK) | KAIST (Koreya) | NUS (Singapur)\n\n"
        "📝 *Talab:* IELTS 6.0+ | SAT | Milliy sertifikat",
        parse_mode=ParseMode.MARKDOWN)

async def mock_info_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.message.reply_text(
        "📝 *MOCK IMTIHON*\n\nDTM/SAT ga tayyorgarlik sinovi.\n\n"
        "Resurslar: dtm.uz | prep.uz | Khan Academy",
        parse_mode=ParseMode.MARKDOWN)

# ─── PORTFEL ───────────────────────────────────────────────────────────────────
async def portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *PORTFEL YARATISH*\n\nO'quvchi ismini yoki ID sini kiriting:",
        parse_mode=ParseMode.MARKDOWN)
    return PORTFOLIO_REQUEST

async def generate_portfolio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Agar menyu tugmasi bosilsa — state dan chiqamiz
    text = update.message.text.strip()
    menu_buttons = ["👨‍🎓 O'quvchilar boshqaruvi","🏆 Yutuq va olimpiadalar",
                    "🎭 To'garaklar va yo'nalishlar","🎯 Kasb yo'naltirish",
                    "❓ Yordam va AI maslahat","📊 Hisobot","🏠 Bosh menyu"]
    if text in menu_buttons:
        return await main_menu_router(update, context)

    conn = get_db(); c = conn.cursor()
    if text.isdigit():
        c.execute("SELECT id,full_name,class_name FROM students WHERE id=?", (int(text),))
    else:
        c.execute("SELECT id,full_name,class_name FROM students WHERE full_name LIKE ? LIMIT 1", (f"%{text}%",))
    s = c.fetchone()
    if not s:
        await update.message.reply_text("❌ Topilmadi. Ismni to'liqroq kiriting yoki ID dan foydalaning.")
        conn.close(); return PORTFOLIO_REQUEST
    sid, sname, cls = s
    c.execute("SELECT media_type,content,caption,added_at FROM student_media WHERE student_id=? ORDER BY added_at", (sid,))
    media = c.fetchall(); conn.close()
    if not media:
        await update.message.reply_text(
            f"⚠️ *{sname}* haqida ma'lumot yo'q.\n`/add_media {sid}` orqali qo'shing.",
            parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    msg = await update.message.reply_text(f"⏳ *{sname}* portfeli tayyorlanmoqda...", parse_mode=ParseMode.MARKDOWN)
    data = [{"media_type":r[0],"content":r[1],"caption":r[2],"added_at":r[3]} for r in media]
    try:
        pt = generate_portfolio(sname, cls, data)
        await msg.delete()
        await update.message.reply_text(pt, parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard())
    except Exception as e:
        await msg.edit_text(f"❌ Xato: {e}")
    return MAIN_MENU

# ─── HISOBOT ───────────────────────────────────────────────────────────────────
async def report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Umumiy hisobot", callback_data="report_general")],
        [InlineKeyboardButton("👨‍🎓 O'quvchi hisoboti", callback_data="report_student")],
        [InlineKeyboardButton("🎭 To'garaklar hisoboti", callback_data="report_clubs")],
        [InlineKeyboardButton("🏆 Yutuqlar hisoboti", callback_data="report_achievements")],
    ]
    await update.message.reply_text(
        "📊 *HISOBOT*\n\nQaysi hisobotni tayyorlayin?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def report_general(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM students"); total_students = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM clubs"); total_clubs = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM achievements"); total_ach = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM club_members"); total_members = c.fetchone()[0]
    c.execute("SELECT class_name, COUNT(*) as cnt FROM students GROUP BY class_name ORDER BY cnt DESC LIMIT 5")
    top_classes = c.fetchall()
    c.execute("""SELECT s.full_name, COUNT(a.id) as cnt FROM students s 
                 JOIN achievements a ON s.id=a.student_id GROUP BY s.id ORDER BY cnt DESC LIMIT 5""")
    top_students = c.fetchall()
    conn.close()

    classes_text = "\n".join([f"  {cls or '—'}: {cnt} o'quvchi" for cls, cnt in top_classes])
    top_text = "\n".join([f"  {n}: {cnt} yutuq" for n, cnt in top_students])

    data = {
        "Jami o'quvchilar": total_students,
        "Jami to'garaklar": total_clubs,
        "Jami yutuqlar": total_ach,
        "To'garak a'zolari": total_members,
        "Sinflar bo'yicha": classes_text,
        "Top o'quvchilar (yutuq)": top_text,
        "Sana": datetime.now().strftime("%Y-%m-%d")
    }

    msg = await q.message.reply_text("⏳ Hisobot tayyorlanmoqda...")
    try:
        report = generate_report("UMUMIY MAKTAB", str(data))
        await msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Xato: {e}")

async def report_clubs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    conn = get_db(); c = conn.cursor()
    c.execute("""SELECT cl.name, cl.direction, cl.responsible, COUNT(cm.id) as cnt
                 FROM clubs cl LEFT JOIN club_members cm ON cl.id=cm.club_id
                 GROUP BY cl.id ORDER BY cnt DESC""")
    rows = c.fetchall(); conn.close()
    if not rows:
        await q.message.reply_text("📭 To'garaklar yo'q."); return
    data = {r[0]: {"yo'nalish": r[1], "mas'ul": r[2], "a'zolar": r[3]} for r in rows}
    msg = await q.message.reply_text("⏳ Hisobot tayyorlanmoqda...")
    try:
        report = generate_report("TO'GARAKLAR", str(data))
        await msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Xato: {e}")

async def report_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    conn = get_db(); c = conn.cursor()
    c.execute("""SELECT s.full_name, s.class_name, a.title, a.achievement_type, a.date
                 FROM achievements a JOIN students s ON a.student_id=s.id ORDER BY a.date DESC""")
    rows = c.fetchall(); conn.close()
    if not rows:
        await q.message.reply_text("📭 Yutuqlar yo'q."); return
    data = [{"o'quvchi": r[0], "sinf": r[1], "yutuq": r[2], "tur": r[3], "sana": r[4]} for r in rows]
    msg = await q.message.reply_text("⏳ Hisobot tayyorlanmoqda...")
    try:
        report = generate_report("YUTUQLAR", str(data))
        await msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Xato: {e}")

async def report_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    context.user_data["report_mode"] = "student"
    await q.message.reply_text("👨‍🎓 O'quvchi ismini kiriting:")
    return SEARCH_STUDENT

# ─── YORDAM VA AI ───────────────────────────────────────────────────────────────
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👨‍🎓 O'quvchi qo'shishni o'rgat", callback_data="teach_student")],
        [InlineKeyboardButton("🎭 To'garak qo'shishni o'rgat", callback_data="teach_club")],
        [InlineKeyboardButton("🏆 Yutuq qo'shishni o'rgat", callback_data="teach_achievement")],
        [InlineKeyboardButton("📋 Portfel yaratishni o'rgat", callback_data="teach_portfolio")],
        [InlineKeyboardButton("📊 Hisobot olishni o'rgat", callback_data="teach_report")],
        [InlineKeyboardButton("💬 O'z savolimni yozaman", callback_data="ai_free")],
    ]
    await update.message.reply_text(
        "❓ *YORDAM VA AI MASLAHAT*\n\nNima haqida yordam kerak?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))

async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    menu_buttons = ["👨‍🎓 O'quvchilar boshqaruvi","🏆 Yutuq va olimpiadalar",
                    "🎭 To'garaklar va yo'nalishlar","🎯 Kasb yo'naltirish",
                    "❓ Yordam va AI maslahat","📊 Hisobot","🏠 Bosh menyu"]
    if text in menu_buttons:
        context.user_data.pop("ai_chat_mode", None)
        return await main_menu_router(update, context)
    msg = await update.message.reply_text("🤔 AI o'ylamoqda...")
    try:
        answer = ask_claude_guide(text, "AI suhbat")
        await msg.edit_text(f"🤖 *AI:*\n\n{answer}", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Xato: {e}")
    return AI_CHAT

# ─── CALLBACK DISPATCHER ──────────────────────────────────────────────────────
TEACH_TEXTS = {
    "teach_student": "O'quvchi qo'shish jarayonini bosqichma-bosqich tushuntir: tugma, ism, sinf, /add_media, /done",
    "teach_club": "To'garak qo'shish: /add_togarak buyrug'i va tugma orqali jarayonni tushuntir",
    "teach_achievement": "Yutuq qo'shish jarayonini tushuntir: menyu, o'quvchi tanlash, nom, tur, sana",
    "teach_portfolio": "Portfel yaratish jarayonini tushuntir: avval /add_media, keyin 📋 Portfel",
    "teach_report": "Hisobot olish jarayonini tushuntir: 📊 tugmasi, hisobot turlari",
    "ai_help_students": "O'quvchilar boshqaruvi menyusini to'liq tushuntir",
    "ai_help_achievements": "Yutuqlar menyusini to'liq tushuntir",
    "ai_help_clubs": "To'garaklar menyusini tushuntir, /add_togarak misollari bilan",
    "ai_help_career": "Kasb yo'naltirish bo'yicha maslahat ber",
}

async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data

    # AI o'rgatish
    if data in TEACH_TEXTS:
        await q.answer()
        msg = await q.message.reply_text("🤔 AI o'ylamoqda...")
        try:
            answer = ask_claude_guide(TEACH_TEXTS[data], data)
            await msg.edit_text(f"🤖 *AI Qo'llanma:*\n\n{answer}", parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            await msg.edit_text(f"❌ Xato: {e}")
        return

    handlers = {
        "add_student": add_student_start,
        "search_student": search_student_start,
        "list_students": list_students_cb,
        "add_achievement": add_achievement_start,
        "list_achievements": list_achievements_cb,
        "add_club_btn": add_club_btn,
        "list_clubs": list_clubs_cb,
        "add_member_start": add_member_start,
        "universities_info": universities_info_cb,
        "mock_info": mock_info_cb,
        "report_general": report_general,
        "report_clubs": report_clubs,
        "report_achievements": report_achievements,
        "report_student": report_student_start,
    }

    if data == "ai_free":
        await q.answer()
        context.user_data["ai_chat_mode"] = True
        await q.message.reply_text("💬 Savolingizni yozing. Menyuga qaytish uchun istalgan tugmani bosing.")
        return

    if data in handlers:
        return await handlers[data](update, context)

    if data.startswith("cdir_"):
        return await club_dir_selected(update, context)
    if data.startswith("student_profile_"):
        return await show_student_profile(update, context)
    if data.startswith("ach_sel_"):
        return await ach_sel_student(update, context)
    if data.startswith("acht_"):
        return await ach_sel_type(update, context)
    if data.startswith("msel_"):
        return await member_sel_student(update, context)
    if data.startswith("mjoin_"):
        return await join_club(update, context)

    if data.startswith("gen_portfolio_"):
        sid = int(data.split("_")[-1])
        await q.answer()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT full_name,class_name FROM students WHERE id=?", (sid,))
        row = c.fetchone()
        if row:
            msg = await q.message.reply_text(f"⏳ *{row[0]}* portfeli...", parse_mode=ParseMode.MARKDOWN)
            c.execute("SELECT media_type,content,caption,added_at FROM student_media WHERE student_id=?", (sid,))
            media = c.fetchall(); conn.close()
            if media:
                d = [{"media_type":r[0],"content":r[1],"caption":r[2],"added_at":r[3]} for r in media]
                try:
                    pt = generate_portfolio(row[0], row[1], d)
                    await msg.edit_text(pt, parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    await msg.edit_text(f"❌ Xato: {e}")
            else:
                await msg.edit_text(f"⚠️ Ma'lumot yo'q. /add_media {sid}")
        else:
            conn.close(); await q.answer("❌ Topilmadi")

    elif data.startswith("add_media_"):
        sid = int(data.split("_")[-1])
        await q.answer()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT full_name FROM students WHERE id=?", (sid,))
        row = c.fetchone(); conn.close()
        if row:
            context.user_data["target_student_id"] = sid
            context.user_data["target_student_name"] = row[0]
            await q.message.reply_text(
                f"📁 *{row[0]}* uchun yuboring:\n📝 Matn | 🖼 Rasm | 🎥 Video\n\nTugash: /done",
                parse_mode=ParseMode.MARKDOWN)

    elif data.startswith("add_ach_"):
        sid = int(data.split("_")[-1])
        await q.answer()
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT full_name FROM students WHERE id=?", (sid,))
        row = c.fetchone(); conn.close()
        if row:
            context.user_data.update({"ach_sid": sid, "ach_name": row[0]})
            await q.message.reply_text(f"🏆 *{row[0]}* yutuq nomi:", parse_mode=ParseMode.MARKDOWN)
    else:
        await q.answer("⚙️")

# ─── ASOSIY ROUTER ─────────────────────────────────────────────────────────────
async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update): return
    text = update.message.text

    # Agar media qo'shish rejimida bo'lsa
    if context.user_data.get("target_student_id") and not text.startswith("/"):
        return await receive_media(update, context)

    # Agar AI chat rejimida bo'lsa
    if context.user_data.get("ai_chat_mode") and not text.startswith("/"):
        return await ai_chat_handler(update, context)

    routes = {
        "👨‍🎓 O'quvchilar boshqaruvi": students_menu,
        "🏆 Yutuq va olimpiadalar": achievements_menu,
        "🎭 To'garaklar va yo'nalishlar": clubs_menu,
        "🎯 Kasb yo'naltirish": career_menu,
        "📋 Portfel yaratish": portfolio_menu,
        "❓ Yordam va AI maslahat": help_menu,
        "📊 Hisobot": report_menu,
        "🏠 Bosh menyu": start,
    }
    if text in routes:
        context.user_data.pop("target_student_id", None)
        context.user_data.pop("target_student_name", None)
        context.user_data.pop("ai_chat_mode", None)
        result = await routes[text](update, context)
        if result == PORTFOLIO_REQUEST:
            return PORTFOLIO_REQUEST
        return MAIN_MENU
    return MAIN_MENU

# ─── MAIN ──────────────────────────────────────────────────────────────────────
async def main():
    init_db()
    logger.info("🚀 Bot v4 ishga tushmoqda...")
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.ALL & ~filters.COMMAND, main_menu_router),
                CallbackQueryHandler(callback_dispatcher),
            ],
            ADD_STUDENT_NAME:       [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_name)],
            ADD_STUDENT_CLASS:      [MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_class)],
            ADD_STUDENT_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_media),
                MessageHandler(filters.PHOTO, receive_media),
                MessageHandler(filters.VIDEO, receive_media),
                MessageHandler(filters.Document.ALL, receive_media),
                CommandHandler("done", done_adding),
            ],
            SEARCH_STUDENT:         [MessageHandler(filters.TEXT & ~filters.COMMAND, search_student_result)],
            PORTFOLIO_REQUEST:      [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_portfolio_handler)],
            ADD_CLUB_NAME:          [MessageHandler(filters.TEXT & ~filters.COMMAND, add_club_name)],
            ADD_CLUB_DIRECTION:     [CallbackQueryHandler(club_dir_selected, pattern="^cdir_")],
            ADD_CLUB_RESPONSIBLE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_club_responsible)],
            ADD_ACHIEVEMENT_STUDENT:[
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_achievement_student),
                CallbackQueryHandler(ach_sel_student, pattern="^ach_sel_"),
            ],
            ADD_ACHIEVEMENT_TITLE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_achievement_title)],
            ADD_ACHIEVEMENT_TYPE:   [CallbackQueryHandler(ach_sel_type, pattern="^acht_")],
            ADD_ACHIEVEMENT_DATE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_achievement_date)],
            AI_CHAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handler),
                CommandHandler("done", done_adding),
            ],
            ADD_MEMBER_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_member_search),
                CallbackQueryHandler(member_sel_student, pattern="^msel_"),
            ],
            ADD_MEMBER_CLUB: [CallbackQueryHandler(join_club, pattern="^mjoin_")],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^🏠 Bosh menyu$"), start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("add_media", add_media_cmd))
    app.add_handler(CommandHandler("add_togarak", add_togarak_cmd))
    app.add_handler(CommandHandler("hisobot", lambda u, c: report_menu(u, c)))
    app.add_handler(CallbackQueryHandler(callback_dispatcher))

    logger.info("✅ Bot v4 tayyor!")
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        logger.info("✅ Bot ishlayapti!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

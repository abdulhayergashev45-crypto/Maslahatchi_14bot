import asyncio
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

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
BOT_TOKEN = "8834151202:AAGCOWr4FswvIGIWQJbmGHcYRTwVerSvxkA"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY")
ADMIN_IDS = "1396115927"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")

# ─── CONVERSATION STATES ───────────────────────────────────────────────────────
(
    MAIN_MENU,
    ADD_STUDENT_NAME, ADD_STUDENT_CLASS, ADD_STUDENT_DATA,
    SEARCH_STUDENT,
    PORTFOLIO_REQUEST,
    CLUBS_MENU, MONITORING_MENU,
) = range(8)

# ─── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
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
            media_type TEXT,  -- 'text', 'photo', 'video', 'document'
            content TEXT,     -- matn yoki file_id
            caption TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            direction TEXT,   -- madaniyat, texnologiya, sport, san'at
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
            description TEXT,
            achievement_type TEXT,  -- olimpiada, sport, san'at, boshqa
            date TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS career_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES students(id),
            interest TEXT,
            university TEXT,
            profession TEXT,
            notes TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()
    logger.info("✅ Database tayyor")

def get_db():
    return sqlite3.connect(DB_PATH)

# ─── GOOGLE SHEETS (ixtiyoriy) ─────────────────────────────────────────────────
def sync_to_sheets(student_data: dict):
    """Google Sheets ga sinxronlashtirish"""
    if not GOOGLE_SHEET_ID:
        return
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        row = [
            student_data.get("id"),
            student_data.get("full_name"),
            student_data.get("class_name"),
            student_data.get("created_at"),
        ]
        sheet.append_row(row)
        logger.info(f"✅ Google Sheets ga yuborildi: {student_data['full_name']}")
    except Exception as e:
        logger.warning(f"⚠️ Google Sheets xatosi: {e}")

# ─── CLAUDE AI ─────────────────────────────────────────────────────────────────
def generate_portfolio(student_name: str, student_data: list) -> str:
    """Claude AI orqali ijtimoiy portfel yaratish"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    data_text = "\n".join([
        f"[{d['added_at'][:10]}] {d['media_type'].upper()}: {d['content']}"
        + (f" ({d['caption']})" if d['caption'] else "")
        for d in student_data
    ])

    prompt = f"""Siz maktab maslahatchisisiz. Quyidagi o'quvchi haqida to'plangan ma'lumotlar asosida professional IJTIMOIY PORTFEL tayyorlang.

O'quvchi ismi: {student_name}

To'plangan ma'lumotlar:
{data_text}

Portfelni quyidagi tuzilmada yozing (O'zbek tilida):

📋 IJTIMOIY PORTFEL: {student_name}
━━━━━━━━━━━━━━━━━━━━━━━━

👤 UMUMIY MA'LUMOT
[O'quvchi haqida qisqacha]

🏆 YUTUQLAR VA MUVAFFAQIYATLAR
[Barcha yutuqlarini sanab o'ting]

🎭 TO'GARAKLAR VA FAOLIYATLAR
[Qaysi to'garaklarda ishtirok etishi]

🎯 KELAJAK REJALARI
[Kasb tanlash, universitet istiqbollari]

💡 SHAXSIY SIFATLAR
[Ma'lumotlardan kelib chiqqan holda]

📊 MASLAHATCHI XULOSASI
[Umumiy baho va tavsiyalar]

━━━━━━━━━━━━━━━━━━━━━━━━
Sanalar, faktlar va aniq ma'lumotlarga asoslanib yozing. Portfel rasmiy va professional bo'lishi kerak."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def ask_claude(question: str, context: str = "") -> str:
    """Umumiy savollarga Claude AI javob beradi"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    system = """Siz maktab maslahatchisisining yordamchisisiz. 
O'zbek tilida qisqa, aniq va foydali javoblar bering.
Kasb yo'naltirish, o'quvchi rivojlanishi, to'garaklar haqida maslahat bering."""

    messages_list = []
    if context:
        messages_list.append({"role": "user", "content": f"Kontekst: {context}"})
        messages_list.append({"role": "assistant", "content": "Tushundim."})
    messages_list.append({"role": "user", "content": question})

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system,
        messages=messages_list
    )
    return message.content[0].text

# ─── KLAVIATURA YORDAMCHILAR ───────────────────────────────────────────────────
def main_keyboard():
    keyboard = [
        [KeyboardButton("👨‍🎓 O'quvchilar boshqaruvi"), KeyboardButton("🏆 Yutuq va olimpiadalar")],
        [KeyboardButton("🎭 To'garaklar va yo'nalishlar"), KeyboardButton("🎯 Kasb yo'naltirish")],
        [KeyboardButton("📋 Portfel yaratish"), KeyboardButton("❓ AI maslahat")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, persistent=True)

def back_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("🏠 Bosh menyu")]], resize_keyboard=True)

# ─── ADMIN TEKSHIRISH ──────────────────────────────────────────────────────────
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def check_admin(update: Update) -> bool:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Kechirasiz, bu bot faqat maktab maslahatchisi uchun.")
        return False
    return True

# ─── START ─────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_admin(update):
        return

    user = update.effective_user
    welcome = f"""🏫 *Maktab Maslahatchisi Bot*

Assalomu alaykum, {user.first_name}! 

Bu bot sizga quyidagilarda yordam beradi:
• 👨‍🎓 O'quvchilar profilini boshqarish
• 🏆 Yutuq va olimpiadalarni kuzatish  
• 🎭 To'garaklar faoliyatini tashkil etish
• 🎯 Kasb yo'naltirishda maslahat
• 📋 Ijtimoiy portfel avtomatik tayyorlash

Quyidagi menyudan foydalaning:"""

    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=main_keyboard())
    return MAIN_MENU

# ─── MENYU 1: O'QUVCHILAR BOSHQARUVI ──────────────────────────────────────────
async def students_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Yangi o'quvchi qo'shish", callback_data="add_student")],
        [InlineKeyboardButton("🔍 O'quvchi qidirish", callback_data="search_student")],
        [InlineKeyboardButton("📁 Ma'lumot qo'shish (matn/rasm/video)", callback_data="add_media")],
        [InlineKeyboardButton("📋 Barcha o'quvchilar ro'yxati", callback_data="list_students")],
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
        f"✅ Ism: *{context.user_data['new_student_name']}*\n\nSinfini kiriting:\n_(Masalan: 9-A, 11-B)_",
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

    # Google Sheets ga sinxronlashtirish
    sync_to_sheets({"id": student_id, "full_name": name,
                    "class_name": class_name, "created_at": datetime.now().isoformat()})
    conn.close()

    context.user_data["current_student_id"] = student_id
    context.user_data["current_student_name"] = name

    await update.message.reply_text(
        f"✅ *{name}* ({class_name}) muvaffaqiyatli qo'shildi!\n\n"
        f"🆔 ID: `{student_id}`\n\n"
        f"Endi bu o'quvchi haqida ma'lumot (matn, rasm, video) yubora boshlashingiz mumkin.\n"
        f"Yuborish uchun /add\\_media {student_id} buyrug'ini ishlating.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

async def search_student_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "🔍 *O'quvchi qidirish*\n\nIsm yoki sinfni kiriting:",
        parse_mode=ParseMode.MARKDOWN
    )
    return SEARCH_STUDENT

async def search_student_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search = update.message.text.strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, full_name, class_name, created_at 
        FROM students 
        WHERE full_name LIKE ? OR class_name LIKE ?
        ORDER BY full_name
        LIMIT 10
    """, (f"%{search}%", f"%{search}%"))
    results = c.fetchall()
    conn.close()

    if not results:
        await update.message.reply_text("❌ Hech narsa topilmadi. Qayta urinib ko'ring.")
        return MAIN_MENU

    text = f"🔍 *Natijalar ({len(results)} ta):*\n\n"
    keyboard = []
    for sid, name, cls, created in results:
        text += f"• `{sid}` | {name} | {cls or '—'}\n"
        keyboard.append([
            InlineKeyboardButton(f"📋 {name}", callback_data=f"student_profile_{sid}"),
        ])

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(keyboard))
    return MAIN_MENU

async def show_student_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    student_id = int(query.data.split("_")[-1])

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT full_name, class_name, created_at FROM students WHERE id=?", (student_id,))
    student = c.fetchone()
    if not student:
        await query.message.reply_text("❌ O'quvchi topilmadi.")
        conn.close()
        return

    name, cls, created = student
    c.execute("SELECT COUNT(*) FROM student_media WHERE student_id=?", (student_id,))
    media_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM achievements WHERE student_id=?", (student_id,))
    ach_count = c.fetchone()[0]
    conn.close()

    text = f"""👤 *{name}*

📚 Sinf: {cls or 'Kiritilmagan'}
📅 Qo'shilgan: {created[:10]}
📁 Media/ma'lumotlar: {media_count} ta
🏆 Yutuqlar: {ach_count} ta"""

    keyboard = [
        [InlineKeyboardButton("📋 Portfel ko'rish", callback_data=f"gen_portfolio_{student_id}")],
        [InlineKeyboardButton("📁 Ma'lumot qo'shish", callback_data=f"add_media_{student_id}")],
        [InlineKeyboardButton("🏆 Yutuq qo'shish", callback_data=f"add_achievement_{student_id}")],
    ]
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=InlineKeyboardMarkup(keyboard))

# ─── MEDIA QO'SHISH ────────────────────────────────────────────────────────────
async def add_media_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buyruq orqali: /add_media <student_id>"""
    if not await check_admin(update):
        return
    if not context.args:
        await update.message.reply_text("❗ Ishlatilishi: /add_media <o'quvchi_id>")
        return
    try:
        student_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❗ ID raqam bo'lishi kerak.")
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT full_name FROM students WHERE id=?", (student_id,))
    student = c.fetchone()
    conn.close()

    if not student:
        await update.message.reply_text("❌ Bunday ID'li o'quvchi topilmadi.")
        return

    context.user_data["target_student_id"] = student_id
    context.user_data["target_student_name"] = student[0]
    await update.message.reply_text(
        f"📁 *{student[0]}* uchun ma'lumot yubormoqchisiz.\n\n"
        f"Istalgan narsa yuboring:\n"
        f"• 📝 Matn (yutuq, tavsif, eslatma)\n"
        f"• 🖼 Rasm (diplom, sertifikat, faoliyat)\n"
        f"• 🎥 Video (taqdimot, musobaqa)\n\n"
        f"Tugatish uchun: /done",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_STUDENT_DATA

async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matn, rasm, video qabul qilish"""
    student_id = context.user_data.get("target_student_id")
    if not student_id:
        return MAIN_MENU

    conn = get_db()
    c = conn.cursor()
    now = datetime.now().isoformat()

    if update.message.text and not update.message.text.startswith("/"):
        c.execute("INSERT INTO student_media (student_id, media_type, content, added_at) VALUES (?,?,?,?)",
                  (student_id, "text", update.message.text, now))
        await update.message.reply_text("✅ Matn saqlandi!")

    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        caption = update.message.caption or ""
        c.execute("INSERT INTO student_media (student_id, media_type, content, caption, added_at) VALUES (?,?,?,?,?)",
                  (student_id, "photo", file_id, caption, now))
        await update.message.reply_text("✅ Rasm saqlandi!")

    elif update.message.video:
        file_id = update.message.video.file_id
        caption = update.message.caption or ""
        c.execute("INSERT INTO student_media (student_id, media_type, content, caption, added_at) VALUES (?,?,?,?,?)",
                  (student_id, "video", file_id, caption, now))
        await update.message.reply_text("✅ Video saqlandi!")

    elif update.message.document:
        file_id = update.message.document.file_id
        caption = update.message.caption or ""
        c.execute("INSERT INTO student_media (student_id, media_type, content, caption, added_at) VALUES (?,?,?,?,?)",
                  (student_id, "document", file_id, caption, now))
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
        f"Portfel yaratish uchun 📋 *Portfel yaratish* tugmasini bosing.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard()
    )
    return MAIN_MENU

# ─── MENYU 2: YUTUQ VA OLIMPIADALAR ───────────────────────────────────────────
async def achievements_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Yutuq qo'shish", callback_data="add_ach_manual")],
        [InlineKeyboardButton("📊 Barcha yutuqlar", callback_data="list_achievements")],
        [InlineKeyboardButton("🥇 Top o'quvchilar", callback_data="top_students")],
    ]
    await update.message.reply_text(
        "🏆 *YUTUQ VA OLIMPIADALAR*\n\nMaktab o'quvchilarining barcha yutuqlarini bu yerda boshqaring.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def list_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT s.full_name, s.class_name, a.title, a.achievement_type, a.date
        FROM achievements a JOIN students s ON a.student_id = s.id
        ORDER BY a.added_at DESC LIMIT 20
    """)
    rows = c.fetchall()
    conn.close()

    if not rows:
        await query.message.reply_text("📭 Hali yutuqlar kiritilmagan.")
        return

    text = "🏆 *SO'NGGI YUTUQLAR:*\n\n"
    for name, cls, title, atype, date in rows:
        text += f"🥇 *{name}* ({cls or '—'})\n   {title} | {atype or '—'} | {date or '—'}\n\n"

    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─── MENYU 3: TO'GARAKLAR ─────────────────────────────────────────────────────
async def clubs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ To'garak qo'shish", callback_data="add_club")],
        [InlineKeyboardButton("📋 Barcha to'garaklar", callback_data="list_clubs")],
        [InlineKeyboardButton("👥 A'zo qo'shish", callback_data="add_club_member")],
    ]
    await update.message.reply_text(
        "🎭 *TO'GARAKLAR VA YO'NALISHLAR*\n\n"
        "Madaniyat, San'at, Texnologiya, Sport yo'nalishlari:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def list_clubs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT cl.name, cl.direction, cl.responsible,
               COUNT(cm.id) as member_count
        FROM clubs cl
        LEFT JOIN club_members cm ON cl.id = cm.club_id
        GROUP BY cl.id ORDER BY cl.direction, cl.name
    """)
    rows = c.fetchall()
    conn.close()

    if not rows:
        await query.message.reply_text("📭 Hali to'garaklar kiritilmagan.\n/add_club buyrug'i bilan qo'shing.")
        return

    icons = {"madaniyat": "🎨", "texnologiya": "💻", "sport": "⚽", "san'at": "🎭"}
    text = "🎭 *TO'GARAKLAR RO'YXATI:*\n\n"
    current_dir = None
    for name, direction, responsible, count in rows:
        if direction != current_dir:
            icon = icons.get(direction, "📌")
            text += f"\n{icon} *{(direction or 'Boshqa').upper()}*\n"
            current_dir = direction
        text += f"  • {name} ({count} a'zo) — {responsible or '—'}\n"

    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─── MENYU 4: KASB YO'NALTIRISH ───────────────────────────────────────────────
async def career_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 Kasb ma'lumoti qo'shish", callback_data="add_career")],
        [InlineKeyboardButton("🏫 Top-300 universitetlar", callback_data="universities_info")],
        [InlineKeyboardButton("📋 MOCK imtihon natijalar", callback_data="mock_results")],
        [InlineKeyboardButton("🤖 AI maslahat", callback_data="ai_career_advice")],
    ]
    await update.message.reply_text(
        "🎯 *KASB YO'NALTIRISH*\n\nO'quvchilarning kelajak rejalari va kasb tanlashda yordam bering:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def universities_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = """🏫 *TOP UNIVERSITETLAR MA'LUMOTI*

🇺🇿 *O'ZBEKISTON:*
• Toshkent Davlat Texnika Universiteti
• O'zbekiston Milliy Universiteti
• INHA University in Tashkent
• Westminster International University

🌍 *XALQARO:*
• MIT, Stanford, Harvard (AQSh)
• Oxford, Cambridge (Buyuk Britaniya)
• KAIST, Yonsei (Janubiy Koreya)
• NUS, NTU (Singapur)

📝 *Qabul uchun:*
SAT, IELTS/TOEFL, milliy sertifikat

Batafsil ma'lumot uchun AI maslahat tugmasini bosing."""
    await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─── PORTFEL YARATISH ─────────────────────────────────────────────────────────
async def portfolio_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *IJTIMOIY PORTFEL YARATISH*\n\nO'quvchi ismini yoki ID sini kiriting:\n_(Masalan: Karimov yoki 5)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return PORTFOLIO_REQUEST

async def generate_portfolio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search = update.message.text.strip()

    conn = get_db()
    c = conn.cursor()

    # ID yoki ism bilan qidirish
    if search.isdigit():
        c.execute("SELECT id, full_name FROM students WHERE id=?", (int(search),))
    else:
        c.execute("SELECT id, full_name FROM students WHERE full_name LIKE ? LIMIT 1",
                  (f"%{search}%",))
    student = c.fetchone()

    if not student:
        await update.message.reply_text("❌ O'quvchi topilmadi. Qayta urinib ko'ring.")
        conn.close()
        return MAIN_MENU

    student_id, student_name = student
    c.execute("""
        SELECT media_type, content, caption, added_at
        FROM student_media WHERE student_id=?
        ORDER BY added_at ASC
    """, (student_id,))
    media_rows = c.fetchall()
    conn.close()

    if not media_rows:
        await update.message.reply_text(
            f"⚠️ *{student_name}* haqida hali ma'lumot kiritilmagan.\n"
            f"Avval /add\\_media {student_id} orqali ma'lumot qo'shing.",
            parse_mode=ParseMode.MARKDOWN
        )
        return MAIN_MENU

    await update.message.reply_text(
        f"⏳ *{student_name}* uchun portfel tayyorlanmoqda...\nBu 10-15 soniya olishi mumkin.",
        parse_mode=ParseMode.MARKDOWN
    )

    media_data = [{"media_type": r[0], "content": r[1],
                   "caption": r[2], "added_at": r[3]} for r in media_rows]

    try:
        portfolio_text = generate_portfolio(student_name, media_data)
        await update.message.reply_text(portfolio_text, parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=main_keyboard())
    except Exception as e:
        logger.error(f"Portfolio xatosi: {e}")
        await update.message.reply_text(
            f"❌ Portfel yaratishda xato: {str(e)}\nQayta urinib ko'ring.",
            reply_markup=main_keyboard()
        )
    return MAIN_MENU

# ─── AI MASLAHAT ───────────────────────────────────────────────────────────────
async def ai_advice_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *AI MASLAHAT*\n\nMenga istalgan savol bering:\n"
        "• O'quvchini qanday kasb tanlashiga yordam berish\n"
        "• To'garak tashkil etish maslahatlar\n"
        "• Olimpiadaga tayyorlash usullari\n"
        "• Ota-ona bilan ishlash\n\n"
        "Savolingizni yozing:",
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data["ai_mode"] = True

async def handle_ai_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("ai_mode"):
        return
    question = update.message.text
    await update.message.reply_text("🤔 O'ylamoqdaman...")
    try:
        answer = ask_claude(question)
        context.user_data["ai_mode"] = False
        await update.message.reply_text(f"🤖 *AI Maslahat:*\n\n{answer}",
                                         parse_mode=ParseMode.MARKDOWN,
                                         reply_markup=main_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ Xato: {e}", reply_markup=main_keyboard())

# ─── CALLBACK DISPATCHER ──────────────────────────────────────────────────────
async def callback_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    handlers = {
        "add_student": add_student_start,
        "search_student": search_student_start,
        "list_achievements": list_achievements,
        "list_clubs": list_clubs,
        "universities_info": universities_info,
        "top_students": lambda u, c: u.callback_query.message.reply_text("🔄 Tayyorlanmoqda..."),
    }

    if data in handlers:
        return await handlers[data](update, context)
    elif data.startswith("student_profile_"):
        return await show_student_profile(update, context)
    elif data.startswith("gen_portfolio_"):
        student_id = int(data.split("_")[-1])
        await query.answer()
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT full_name FROM students WHERE id=?", (student_id,))
        row = c.fetchone()
        if row:
            context.user_data["target_student_id"] = student_id
            await query.message.reply_text(f"⏳ *{row[0]}* portfeli tayyorlanmoqda...",
                                            parse_mode=ParseMode.MARKDOWN)
            c.execute("SELECT media_type, content, caption, added_at FROM student_media WHERE student_id=?",
                      (student_id,))
            media_rows = c.fetchall()
            conn.close()
            if media_rows:
                media_data = [{"media_type": r[0], "content": r[1], "caption": r[2], "added_at": r[3]}
                               for r in media_rows]
                portfolio_text = generate_portfolio(row[0], media_data)
                await query.message.reply_text(portfolio_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await query.message.reply_text(f"⚠️ Ma'lumot yo'q. Avval /add_media {student_id} ishlating.")
        else:
            conn.close()
    else:
        await query.answer("⚙️ Tez orada...")

# ─── ASOSIY MENYU HANDLER ─────────────────────────────────────────────────────
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
        "❓ AI maslahat": ai_advice_menu,
        "🏠 Bosh menyu": start,
    }

    if text in routes:
        result = await routes[text](update, context)
        if result == PORTFOLIO_REQUEST:
            return PORTFOLIO_REQUEST
        return MAIN_MENU

    # AI mode aktiv bo'lsa
    if context.user_data.get("ai_mode"):
        await handle_ai_question(update, context)
        return MAIN_MENU

    # Media qo'shish mode
    if context.user_data.get("target_student_id"):
        return await receive_media(update, context)

    return MAIN_MENU

# ─── BOTNI ISHGA TUSHIRISH ─────────────────────────────────────────────────────
def main():
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
            ADD_STUDENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_name),
            ],
            ADD_STUDENT_CLASS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_student_class),
            ],
            ADD_STUDENT_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_media),
                MessageHandler(filters.PHOTO, receive_media),
                MessageHandler(filters.VIDEO, receive_media),
                MessageHandler(filters.Document.ALL, receive_media),
                CommandHandler("done", done_adding),
            ],
            SEARCH_STUDENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_student_result),
            ],
            PORTFOLIO_REQUEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, generate_portfolio_handler),
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
    app.add_handler(CallbackQueryHandler(callback_dispatcher))

    logger.info("✅ Bot tayyor! Polling boshlandi...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()

import asyncio
import logging
import os
import sqlite3
import json
from datetime import datetime

import google.generativeai as genai
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from telegram.constants import ParseMode

# ─── SOZLAMALAR ────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_KEY")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "123456789").split(",")))

genai.configure(api_key=GEMINI_API_KEY)

# ─── STATES ────────────────────────────────────────────────────────────────────
(
    MAIN_MENU,
    S_NAME, S_CLASS, S_DATA,
    S_SEARCH,
    PORTFOLIO,
    C_NAME, C_DIR, C_RESP,
    A_STUDENT, A_TITLE, A_TYPE, A_DATE,
    AI_CHAT,
    M_SEARCH, M_CLUB,
    # MOCK states
    MOCK_TITLE, MOCK_CLASS, MOCK_SUBJECT, MOCK_TYPE,
    MOCK_Q_TEXT, MOCK_Q_OPTIONS, MOCK_Q_ANSWER, MOCK_Q_MORE,
    MOCK_TAKE_ANS,
) = range(24)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO,
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ─── O'ZBEKISTON OTM MA'LUMOT BAZASI ──────────────────────────────────────────
OTM_DATA = {
    "texnika_texnologiya": {
        "icon": "⚙️",
        "nom": "Texnika va Texnologiya",
        "universitetlar": [
            {
                "nom": "Toshkent Davlat Texnika Universiteti (TDTU)",
                "qisqacha": "O'zbekistondagi eng yirik texnika universiteti",
                "joylashuv": "Toshkent",
                "yonalishlar": "Mexanika, Elektrotexnika, IT, Qurilish, Kimyo texnologiyasi",
                "ball": "160-220 ball (DTM)",
                "grant": "Ha, mavjud",
                "veb": "tdtu.uz",
                "afzallik": "Kuchli texnik ta'lim, ishlab chiqarish bilan bog'liqlik"
            },
            {
                "nom": "Toshkent Axborot Texnologiyalari Universiteti (TATU)",
                "qisqacha": "IT va telekommunikatsiya yo'nalishidagi yetakchi OTM",
                "joylashuv": "Toshkent (filiallar: Nukus, Farg'ona, Samarqand)",
                "yonalishlar": "Dasturiy injiniring, Kiberhavfsizlik, AI, Telekommunikatsiya",
                "ball": "170-230 ball",
                "grant": "Ha, mavjud",
                "veb": "tuit.uz",
                "afzallik": "IT sohasida eng kuchli OTM, xalqaro hamkorlik"
            },
            {
                "nom": "INHA University in Tashkent",
                "qisqacha": "Janubiy Koreya INHA universiteti filiali",
                "joylashuv": "Toshkent",
                "yonalishlar": "Kompyuter fanlari, Elektr elektronika, Sanoat muhandisligi",
                "ball": "IELTS 5.5+ yoki kirish imtihoni",
                "grant": "Qisman (merit scholarship)",
                "veb": "inha.uz",
                "afzallik": "Xalqaro diplom, Koreya tili imkoniyati, kuchli IT ta'lim"
            },
            {
                "nom": "Toshkent Kimyo-Texnologiya Instituti (TKTI)",
                "qisqacha": "Kimyo va texnologiya sohasining yetakchi OTMi",
                "joylashuv": "Toshkent",
                "yonalishlar": "Kimyo texnologiyasi, Oziq-ovqat texnologiyasi, Ekologiya",
                "ball": "150-200 ball",
                "grant": "Ha",
                "veb": "tkti.uz",
                "afzallik": "Sanoat va kimyo sohasida kuchli amaliy ta'lim"
            },
        ]
    },
    "tibbiyot": {
        "icon": "🏥",
        "nom": "Tibbiyot va Sog'liqni saqlash",
        "universitetlar": [
            {
                "nom": "Toshkent Tibbiyot Akademiyasi (TTA)",
                "qisqacha": "O'zbekistondagi eng nufuzli tibbiyot OTMi",
                "joylashuv": "Toshkent",
                "yonalishlar": "Davolash ishi, Pediatriya, Stomatologiya, Tibbiy biologiya",
                "ball": "200-240 ball",
                "grant": "Ha, cheklangan",
                "veb": "tma.uz",
                "afzallik": "Eng yaxshi tibbiyot ta'limi, kuchli klinik amaliyot"
            },
            {
                "nom": "Samarqand Davlat Tibbiyot Universiteti (SamDTU)",
                "qisqacha": "Markaziy Osiyo miqyosidagi nufuzli tibbiyot OTMi",
                "joylashuv": "Samarqand",
                "yonalishlar": "Davolash, Pediatriya, Stomatologiya, Farmatsiya",
                "ball": "190-230 ball",
                "grant": "Ha",
                "veb": "sammi.uz",
                "afzallik": "Arzonroq narx, xalqaro talabalar ko'p, yaxshi amaliyot"
            },
            {
                "nom": "Toshkent Farmatsevtika Instituti (TFI)",
                "qisqacha": "Farmatsevtika sohasining yagona ixtisoslashgan OTMi",
                "joylashuv": "Toshkent",
                "yonalishlar": "Farmatsiya, Sanoat farmatsiyasi, Bioximiya",
                "ball": "165-210 ball",
                "grant": "Ha",
                "veb": "pharmi.uz",
                "afzallik": "Farmatsiya sohasida yagona, dori-darmon sanoati bilan bog'liq"
            },
        ]
    },
    "iqtisodiyot_biznes": {
        "icon": "💼",
        "nom": "Iqtisodiyot va Biznes",
        "universitetlar": [
            {
                "nom": "Westminster International University in Tashkent (WIUT)",
                "qisqacha": "Britaniya Westminster universiteti filiali",
                "joylashuv": "Toshkent",
                "yonalishlar": "Biznes boshqaruvi, Moliya, Marketing, Menejment",
                "ball": "IELTS 5.5+ yoki SAT",
                "grant": "Merit scholarship (50-100%)",
                "veb": "wiut.uz",
                "afzallik": "Britaniya diplomi, ingliz tilida ta'lim, xalqaro imkoniyat"
            },
            {
                "nom": "Toshkent Davlat Iqtisodiyot Universiteti (TDIU)",
                "qisqacha": "Iqtisodiyot sohasining yetakchi davlat OTMi",
                "joylashuv": "Toshkent",
                "yonalishlar": "Iqtisodiyot, Moliya, Bank ishi, Buxgalteriya, Statistika",
                "ball": "155-210 ball",
                "grant": "Ha",
                "veb": "tdiu.uz",
                "afzallik": "Eng ko'p grant, moliya sektoriga yo'llash kuchli"
            },
            {
                "nom": "O'zbekiston Milliy Universiteti (NUU) — Iqtisodiyot",
                "qisqacha": "Mamlakatning eng yirik klassik universiteti",
                "joylashuv": "Toshkent",
                "yonalishlar": "Iqtisodiyot, Menejment, Matematik iqtisodiyot",
                "ball": "160-220 ball",
                "grant": "Ha",
                "veb": "nuu.uz",
                "afzallik": "Keng yo'nalishlar, ilmiy tadqiqot imkoniyati"
            },
            {
                "nom": "Turin Politexnika Universiteti (TTPU)",
                "qisqacha": "Italiya Turin Politexnika universiteti filiali",
                "joylashuv": "Toshkent",
                "yonalishlar": "Sanoat muhandisligi, Arxitektura, Kompyuter muhandisligi",
                "ball": "Kirish imtihoni + ingliz tili",
                "grant": "Qisman",
                "veb": "polito.uz",
                "afzallik": "Italiya diplomi, Yevropa standartlari"
            },
        ]
    },
    "huquq_ijtimoiy": {
        "icon": "⚖️",
        "nom": "Huquq va Ijtimoiy fanlar",
        "universitetlar": [
            {
                "nom": "Toshkent Davlat Yuridik Universiteti (TDYU)",
                "qisqacha": "Huquq sohasidagi yagona ixtisoslashgan OTM",
                "joylashuv": "Toshkent",
                "yonalishlar": "Huquqshunoslik, Xalqaro huquq, Jinoyat huquqi",
                "ball": "170-230 ball",
                "grant": "Ha, cheklangan",
                "veb": "tsul.uz",
                "afzallik": "Sud va prokuratura tizimiga eng yaxshi yo'l"
            },
            {
                "nom": "O'zbekiston Xalqaro Islom Akademiyasi",
                "qisqacha": "Islom ilmlari va xalqaro munosabatlar",
                "joylashuv": "Toshkent",
                "yonalishlar": "Islom iqtisodiyoti, Xalqaro munosabatlar, Tafsir",
                "ball": "Arab tili + kirish imtihoni",
                "grant": "Ha",
                "veb": "iiau.uz",
                "afzallik": "Xalqaro islamiy ta'lim, Arab va Ingliz tili"
            },
        ]
    },
    "pedagogika": {
        "icon": "📚",
        "nom": "Pedagogika va Ta'lim",
        "universitetlar": [
            {
                "nom": "O'zbekiston Milliy Universiteti (NUU)",
                "qisqacha": "Eng katta klassik universiteti — barcha yo'nalishlar",
                "joylashuv": "Toshkent",
                "yonalishlar": "Fizika, Matematika, Kimyo, Biologiya, Filologiya, Tarix",
                "ball": "150-220 ball (yo'nalishga qarab)",
                "grant": "Ha, ko'p miqdorda",
                "veb": "nuu.uz",
                "afzallik": "Eng ko'p yo'nalish, ilmiy tadqiqot, aspirantura"
            },
            {
                "nom": "O'zbekiston Davlat Jahon Tillari Universiteti (UZSWLU)",
                "qisqacha": "Xorijiy tillar sohasining yetakchi OTMi",
                "joylashuv": "Toshkent",
                "yonalishlar": "Ingliz, Nemis, Fransuz, Xitoy, Arab, Yapon tillari",
                "ball": "165-215 ball",
                "grant": "Ha",
                "veb": "uzswlu.uz",
                "afzallik": "Til bilish + tarjimonlik, diplomatiya yo'li"
            },
            {
                "nom": "Nizomiy nomidagi TDPU",
                "qisqacha": "Pedagogika sohasining yetakchi OTMi",
                "joylashuv": "Toshkent",
                "yonalishlar": "Boshlang'ich ta'lim, Maktabgacha ta'lim, Maxsus pedagogika",
                "ball": "145-195 ball",
                "grant": "Ha, ko'p",
                "veb": "tdpu.uz",
                "afzallik": "O'qituvchilik kasbi uchun eng yaxshi OTM"
            },
        ]
    },
    "qishloq_xojaligi": {
        "icon": "🌾",
        "nom": "Qishloq xo'jaligi va Ekologiya",
        "universitetlar": [
            {
                "nom": "O'zbekiston Milliy Agrar Universiteti (OMAU)",
                "qisqacha": "Qishloq xo'jaligi sohasining yetakchi OTMi",
                "joylashuv": "Toshkent",
                "yonalishlar": "Agronomy, Veterinariya, Oziq-ovqat, Melioratsiya",
                "ball": "140-190 ball",
                "grant": "Ha, ko'p",
                "veb": "agro.uz",
                "afzallik": "Qishloq xo'jaligi texnologiyalari, amaliy ta'lim"
            },
        ]
    }
}

# ─── DATABASE ──────────────────────────────────────────────────────────────────
DB_PATH = "maktab.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL, class_name TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS student_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, media_type TEXT,
            content TEXT, caption TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, direction TEXT, responsible TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS club_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id INTEGER, student_id INTEGER,
            joined_at TEXT DEFAULT (datetime('now')),
            UNIQUE(club_id, student_id)
        );
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, title TEXT,
            achievement_type TEXT, date TEXT,
            added_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS mock_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT,
            class_name TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            is_active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS mock_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER REFERENCES mock_tests(id),
            question_text TEXT NOT NULL,
            question_type TEXT DEFAULT 'mcq',
            options TEXT,
            correct_answer TEXT NOT NULL,
            order_num INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS mock_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id INTEGER REFERENCES mock_tests(id),
            student_id INTEGER REFERENCES students(id),
            score INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            percentage REAL DEFAULT 0,
            answers TEXT,
            taken_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit(); conn.close()
    logger.info("✅ Database tayyor")

def db(): return sqlite3.connect(DB_PATH)

# ─── GEMINI AI ─────────────────────────────────────────────────────────────────
def gemini(prompt: str, system: str = "") -> str:
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system if system else None
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini xato: {e}")
        return f"❌ AI xatosi: {e}"

def ai_portfolio(name, cls, data):
    items = "\n".join([f"[{d['added_at'][:10]}] {d['media_type'].upper()}: {d['content']}"
                       + (f" | {d['caption']}" if d['caption'] else "") for d in data])
    return gemini(
        f"O'quvchi: {name} | Sinf: {cls or '—'}\nMa'lumotlar:\n{items}\n\n"
        f"Sana: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        f"Quyidagi tuzilmada O'ZBEK TILIDA professional ijtimoiy portfel yozing:\n\n"
        f"📋 IJTIMOIY PORTFEL: {name}\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 UMUMIY MA'LUMOT\n🏆 YUTUQLAR VA MUVAFFAQIYATLAR\n"
        f"🎭 TO'GARAKLAR VA FAOLIYATLAR\n🎯 KELAJAK REJALARI\n"
        f"💡 SHAXSIY SIFATLAR\n📊 MASLAHATCHI XULOSASI\n━━━━━━━━━━━━━━━━━━━━━━━━",
        "Siz tajribali maktab maslahatchisisiz. Professional portfel tayyorlang."
    )

def ai_report(rtype, data):
    return gemini(
        f"{rtype} hisoboti:\n\n{data}\n\nProfessional hisobot, statistika va tavsiyalar. O'zbek tilida.",
        "Siz maktab maslahatchisisiz."
    )

def ai_guide(question, menu):
    return gemini(question,
        f"""Maktab maslahatchisi bot yordamchisi. O'zbek tilida javob.
BUYRUQLAR: /start /add_media ID /add_togarak nom /hisobot /mock_test /mock_natija
MENYULAR: 👨‍🎓O'quvchilar 🏆Yutuqlar 🎭To'garaklar 🎯Kasb 📋Portfel ❓Yordam 📊Hisobot
MOCK: Maslahatchi test yaratadi → o'quvchilar yechadi → natijalar saqlanadi
Hozirgi: {menu}""")

def ai_otm_maslahat(question, student_info=""):
    return gemini(
        f"O'quvchi haqida: {student_info}\n\nSavol: {question}\n\n"
        f"O'zbekiston universitetlari haqida aniq, foydali maslahat ber. O'zbek tilida.",
        "Siz O'zbekiston ta'lim tizimini yaxshi biladigan maktab maslahatchisisiz."
    )

# ─── KLAVIATURA ────────────────────────────────────────────────────────────────
def mkb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👨‍🎓 O'quvchilar boshqaruvi"), KeyboardButton("🏆 Yutuq va olimpiadalar")],
        [KeyboardButton("🎭 To'garaklar va yo'nalishlar"), KeyboardButton("🎯 Kasb yo'naltirish")],
        [KeyboardButton("📋 Portfel yaratish"), KeyboardButton("❓ Yordam va AI maslahat")],
        [KeyboardButton("📊 Hisobot"), KeyboardButton("📝 MOCK Imtihon")]
    ], resize_keyboard=True, is_persistent=True)

MENU_ITEMS = {
    "👨‍🎓 O'quvchilar boshqaruvi", "🏆 Yutuq va olimpiadalar",
    "🎭 To'garaklar va yo'nalishlar", "🎯 Kasb yo'naltirish",
    "📋 Portfel yaratish", "❓ Yordam va AI maslahat",
    "📊 Hisobot", "📝 MOCK Imtihon", "🏠 Bosh menyu"
}

DIR_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("🎨 Madaniyat", callback_data="cd_madaniyat"),
     InlineKeyboardButton("💻 Texnologiya", callback_data="cd_texnologiya")],
    [InlineKeyboardButton("⚽ Sport", callback_data="cd_sport"),
     InlineKeyboardButton("🎭 San'at", callback_data="cd_sanat")],
    [InlineKeyboardButton("🌿 Ekologiya", callback_data="cd_ekologiya"),
     InlineKeyboardButton("📌 Boshqa", callback_data="cd_boshqa")],
])
DIR_ICONS = {"madaniyat":"🎨","texnologiya":"💻","sport":"⚽","sanat":"🎭","ekologiya":"🌿","boshqa":"📌"}
ACH_ICONS = {"olimpiada":"🧮","sport":"⚽","sanat":"🎨","texnologiya":"💻","boshqa":"📌"}

def is_admin(uid): return uid in ADMIN_IDS
async def chk(update):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Faqat maslahatchi uchun."); return False
    return True

# ─── HANDLE MENU HELPER ────────────────────────────────────────────────────────
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    context.user_data.clear()
    routes = {
        "👨‍🎓 O'quvchilar boshqaruvi": students_menu,
        "🏆 Yutuq va olimpiadalar": achievements_menu,
        "🎭 To'garaklar va yo'nalishlar": clubs_menu,
        "🎯 Kasb yo'naltirish": career_menu,
        "📋 Portfel yaratish": portfolio_start,
        "❓ Yordam va AI maslahat": help_menu,
        "📊 Hisobot": report_menu,
        "📝 MOCK Imtihon": mock_menu,
        "🏠 Bosh menyu": start,
    }
    if text in routes:
        result = await routes[text](update, context)
        return result if result else MAIN_MENU
    return MAIN_MENU

# ─── START ─────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await chk(update): return ConversationHandler.END
    context.user_data.clear()
    await update.message.reply_text(
        f"🏫 *Maktab Maslahatchisi Bot* v6\n\n"
        f"Assalomu alaykum, *{update.effective_user.first_name}*! 👋\n\n"
        f"*Yangiliklar:*\n"
        f"🎯 O'zbekiston OTM lari ma'lumot bazasi\n"
        f"📝 MOCK imtihon tizimi\n\n"
        f"*Tez boshlash:*\n"
        f"• O'quvchi → 👨‍🎓\n"
        f"• Test yaratish → 📝 MOCK yoki `/mock_test`\n"
        f"• Natijalar → `/mock_natija`",
        parse_mode=ParseMode.MARKDOWN, reply_markup=mkb())
    return MAIN_MENU

# ─── O'QUVCHILAR ───────────────────────────────────────────────────────────────
async def students_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Yangi o'quvchi", callback_data="add_student")],
        [InlineKeyboardButton("🔍 Qidirish", callback_data="srch_student")],
        [InlineKeyboardButton("📋 Barcha o'quvchilar", callback_data="list_students")],
        [InlineKeyboardButton("❓ Qanday foydalanaman?", callback_data="teach_students")],
    ])
    await update.message.reply_text("👨‍🎓 *O'QUVCHILAR BOSHQARUVI*",
                                     parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

async def cb_add_student(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "➕ O'quvchining *to'liq ismini* kiriting:\n_(Karimov Jasur Aliyevich)_",
        parse_mode=ParseMode.MARKDOWN)
    return S_NAME

async def s_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    context.user_data["sname"] = update.message.text.strip()
    await update.message.reply_text(f"✅ *{context.user_data['sname']}*\n\nSinfini kiriting _(9-A, 10-B)_:",
                                     parse_mode=ParseMode.MARKDOWN)
    return S_CLASS

async def s_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    name = context.user_data["sname"]; cls = update.message.text.strip()
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO students(full_name,class_name)VALUES(?,?)", (name, cls))
    sid = c.lastrowid; conn.commit(); conn.close()
    await update.message.reply_text(
        f"✅ *{name}* ({cls}) qo'shildi! 🆔 `{sid}`\n\n📁 Ma'lumot: `/add_media {sid}`",
        parse_mode=ParseMode.MARKDOWN, reply_markup=mkb())
    return MAIN_MENU

async def cb_srch_student(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🔍 Ism yoki sinf kiriting:")
    return S_SEARCH

async def s_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    search = update.message.text.strip()
    conn = db()
    rows = conn.execute("SELECT id,full_name,class_name FROM students WHERE full_name LIKE ? OR class_name LIKE ? LIMIT 10",
                        (f"%{search}%", f"%{search}%")).fetchall()
    conn.close()
    if not rows: await update.message.reply_text("❌ Topilmadi.", reply_markup=mkb()); return MAIN_MENU
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"👤 {n} ({cls or '—'})", callback_data=f"sp_{sid}")]
                                for sid, n, cls in rows])
    await update.message.reply_text(f"🔍 *{len(rows)} natija:*", parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

async def cb_list_students(update, context):
    await update.callback_query.answer()
    conn = db()
    rows = conn.execute("SELECT id,full_name,class_name FROM students ORDER BY class_name,full_name LIMIT 50").fetchall()
    conn.close()
    if not rows: await update.callback_query.message.reply_text("📭 O'quvchilar yo'q."); return MAIN_MENU
    text = "📋 *BARCHA O'QUVCHILAR:*\n\n"
    for sid, n, cls in rows: text += f"`{sid}` | {n} | {cls or '—'}\n"
    await update.callback_query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return MAIN_MENU

async def cb_student_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    sid = int(q.data.split("_")[-1])
    conn = db()
    s = conn.execute("SELECT full_name,class_name,created_at FROM students WHERE id=?", (sid,)).fetchone()
    if not s: await q.message.reply_text("❌ Topilmadi."); conn.close(); return MAIN_MENU
    name, cls, created = s
    mc = conn.execute("SELECT COUNT(*) FROM student_media WHERE student_id=?", (sid,)).fetchone()[0]
    ac = conn.execute("SELECT COUNT(*) FROM achievements WHERE student_id=?", (sid,)).fetchone()[0]
    clubs = [r[0] for r in conn.execute(
        "SELECT cl.name FROM clubs cl JOIN club_members cm ON cl.id=cm.club_id WHERE cm.student_id=?", (sid,)).fetchall()]
    mock_res = conn.execute(
        "SELECT t.title, r.score, r.total, r.percentage FROM mock_results r JOIN mock_tests t ON r.test_id=t.id WHERE r.student_id=? ORDER BY r.taken_at DESC LIMIT 3",
        (sid,)).fetchall()
    conn.close()
    text = (f"👤 *{name}* | 📚 {cls or '—'}\n📅 {created[:10]}\n"
            f"📁 {mc} ta | 🏆 {ac} ta\n🎭 {', '.join(clubs) if clubs else '—'}\n")
    if mock_res:
        text += "\n📝 *MOCK natijalar:*\n"
        for title, score, total, pct in mock_res:
            emoji = "🟢" if pct >= 70 else "🟡" if pct >= 50 else "🔴"
            text += f"{emoji} {title}: {score}/{total} ({pct:.0f}%)\n"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Portfel", callback_data=f"pf_{sid}"),
         InlineKeyboardButton("📁 Ma'lumot", callback_data=f"am_{sid}")],
        [InlineKeyboardButton("🏆 Yutuq", callback_data=f"aa_{sid}"),
         InlineKeyboardButton("📝 MOCK berish", callback_data=f"mock_take_{sid}")],
    ])
    await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

# ─── MEDIA ─────────────────────────────────────────────────────────────────────
async def add_media_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await chk(update): return
    if not context.args:
        await update.message.reply_text("❗ `/add_media <ID>`", parse_mode=ParseMode.MARKDOWN); return
    try: sid = int(context.args[0])
    except: await update.message.reply_text("❗ ID raqam bo'lishi kerak."); return
    conn = db()
    s = conn.execute("SELECT full_name FROM students WHERE id=?", (sid,)).fetchone()
    conn.close()
    if not s: await update.message.reply_text(f"❌ ID={sid} topilmadi."); return
    context.user_data["tsid"] = sid; context.user_data["tsname"] = s[0]
    await update.message.reply_text(
        f"📁 *{s[0]}* uchun yuboring:\n📝 Matn | 🖼 Rasm | 🎥 Video | 📄 Hujjat\n\n✅ Tugash: /done",
        parse_mode=ParseMode.MARKDOWN)
    return S_DATA

async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    sid = context.user_data.get("tsid")
    if not sid: return MAIN_MENU
    conn = db(); c = conn.cursor(); now = datetime.now().isoformat(); m = update.message
    if m.text and not m.text.startswith("/"):
        c.execute("INSERT INTO student_media(student_id,media_type,content,added_at)VALUES(?,?,?,?)", (sid,"text",m.text,now))
        await m.reply_text("✅ Matn saqlandi!")
    elif m.photo:
        c.execute("INSERT INTO student_media(student_id,media_type,content,caption,added_at)VALUES(?,?,?,?,?)",
                  (sid,"photo",m.photo[-1].file_id,m.caption or "",now)); await m.reply_text("✅ Rasm saqlandi!")
    elif m.video:
        c.execute("INSERT INTO student_media(student_id,media_type,content,caption,added_at)VALUES(?,?,?,?,?)",
                  (sid,"video",m.video.file_id,m.caption or "",now)); await m.reply_text("✅ Video saqlandi!")
    elif m.document:
        c.execute("INSERT INTO student_media(student_id,media_type,content,caption,added_at)VALUES(?,?,?,?,?)",
                  (sid,"document",m.document.file_id,m.caption or "",now)); await m.reply_text("✅ Hujjat saqlandi!")
    conn.commit(); conn.close()
    return S_DATA

async def done_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data.pop("tsname", "O'quvchi")
    context.user_data.pop("tsid", None); context.user_data.pop("ai_mode", None)
    await update.message.reply_text(f"✅ *{name}* uchun saqlash yakunlandi!",
                                     parse_mode=ParseMode.MARKDOWN, reply_markup=mkb())
    return MAIN_MENU

# ─── YUTUQLAR ──────────────────────────────────────────────────────────────────
async def achievements_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Yutuq qo'shish", callback_data="add_ach")],
        [InlineKeyboardButton("📊 Barcha yutuqlar", callback_data="list_ach")],
        [InlineKeyboardButton("❓ Qanday foydalanaman?", callback_data="teach_ach")],
    ])
    await update.message.reply_text("🏆 *YUTUQ VA OLIMPIADALAR*",
                                     parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

async def cb_add_ach(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("🏆 O'quvchi ismini kiriting:")
    return A_STUDENT

async def a_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    search = update.message.text.strip()
    conn = db()
    rows = conn.execute("SELECT id,full_name,class_name FROM students WHERE full_name LIKE ? LIMIT 5", (f"%{search}%",)).fetchall()
    conn.close()
    if not rows: await update.message.reply_text("❌ Topilmadi. Qayta:"); return A_STUDENT
    if len(rows) == 1:
        context.user_data.update({"asid": rows[0][0], "asname": rows[0][1]})
        await update.message.reply_text(f"✅ *{rows[0][1]}*\n\nYutuq nomini kiriting:", parse_mode=ParseMode.MARKDOWN)
        return A_TITLE
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"{n} ({cls or '—'})", callback_data=f"asel_{sid}")]
                                for sid, n, cls in rows])
    await update.message.reply_text("Qaysi o'quvchi?", reply_markup=kb)
    return A_STUDENT

async def cb_asel(update, context):
    q = update.callback_query; await q.answer()
    sid = int(q.data.split("_")[-1])
    row = db().execute("SELECT full_name FROM students WHERE id=?", (sid,)).fetchone()
    context.user_data.update({"asid": sid, "asname": row[0]})
    await q.message.reply_text(f"✅ *{row[0]}*\n\nYutuq nomini kiriting:", parse_mode=ParseMode.MARKDOWN)
    return A_TITLE

async def a_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    context.user_data["atitle"] = update.message.text.strip()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🧮 Olimpiada", callback_data="at_olimpiada"),
         InlineKeyboardButton("⚽ Sport", callback_data="at_sport")],
        [InlineKeyboardButton("🎨 San'at", callback_data="at_sanat"),
         InlineKeyboardButton("💻 Texnologiya", callback_data="at_texnologiya")],
        [InlineKeyboardButton("📌 Boshqa", callback_data="at_boshqa")],
    ])
    await update.message.reply_text("Tur:", reply_markup=kb)
    return A_TYPE

async def cb_atype(update, context):
    q = update.callback_query; await q.answer()
    context.user_data["atype"] = q.data.replace("at_", "")
    await q.message.reply_text("📅 Sana _(2024-03-15)_:", parse_mode=ParseMode.MARKDOWN)
    return A_DATE

async def a_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    date = update.message.text.strip()
    sid = context.user_data["asid"]; name = context.user_data["asname"]
    title = context.user_data["atitle"]; atype = context.user_data["atype"]
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO achievements(student_id,title,achievement_type,date)VALUES(?,?,?,?)", (sid,title,atype,date))
    c.execute("INSERT INTO student_media(student_id,media_type,content,added_at)VALUES(?,?,?,?)",
              (sid,"text",f"YUTUQ: {title} ({atype}) — {date}",datetime.now().isoformat()))
    conn.commit(); conn.close()
    await update.message.reply_text(f"✅ *{name}* | 🏆 {title} | {atype} | {date}",
                                     parse_mode=ParseMode.MARKDOWN, reply_markup=mkb())
    return MAIN_MENU

async def cb_list_ach(update, context):
    q = update.callback_query; await q.answer()
    rows = db().execute("""SELECT s.full_name,s.class_name,a.title,a.achievement_type,a.date
                           FROM achievements a JOIN students s ON a.student_id=s.id
                           ORDER BY a.added_at DESC LIMIT 20""").fetchall()
    if not rows: await q.message.reply_text("📭 Yutuqlar yo'q."); return MAIN_MENU
    text = "🏆 *SO'NGGI YUTUQLAR:*\n\n"
    for n, cls, title, atype, date in rows:
        text += f"{ACH_ICONS.get(atype,'🏅')} *{n}* ({cls or '—'})\n   {title} — {date or '—'}\n\n"
    await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return MAIN_MENU

# ─── TO'GARAKLAR ───────────────────────────────────────────────────────────────
async def clubs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ To'garak qo'shish", callback_data="add_club")],
        [InlineKeyboardButton("📋 Barcha to'garaklar", callback_data="list_clubs")],
        [InlineKeyboardButton("👥 A'zo qo'shish", callback_data="add_member")],
        [InlineKeyboardButton("❓ Qanday foydalanaman?", callback_data="teach_clubs")],
    ])
    await update.message.reply_text(
        "🎭 *TO'GARAKLAR*\n\nTez: `/add_togarak Robototexnika`",
        parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

async def add_togarak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await chk(update): return
    if not context.args:
        await update.message.reply_text("❗ `/add_togarak <nom>`", parse_mode=ParseMode.MARKDOWN); return
    context.user_data["cname"] = " ".join(context.args)
    await update.message.reply_text(f"✅ *{context.user_data['cname']}*\n\nYo'nalish:",
                                     parse_mode=ParseMode.MARKDOWN, reply_markup=DIR_KB)
    return C_DIR

async def cb_add_club(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("➕ To'garak nomini kiriting:")
    return C_NAME

async def c_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    context.user_data["cname"] = update.message.text.strip()
    await update.message.reply_text(f"✅ *{context.user_data['cname']}*\n\nYo'nalish:",
                                     parse_mode=ParseMode.MARKDOWN, reply_markup=DIR_KB)
    return C_DIR

async def cb_cdir(update, context):
    q = update.callback_query; await q.answer()
    context.user_data["cdir"] = q.data.replace("cd_", "")
    await q.message.reply_text("👤 Mas'ul o'qituvchi:")
    return C_RESP

async def c_resp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    resp = update.message.text.strip()
    name = context.user_data["cname"]; direction = context.user_data["cdir"]
    conn = db(); conn.execute("INSERT INTO clubs(name,direction,responsible)VALUES(?,?,?)", (name,direction,resp))
    conn.commit(); conn.close()
    await update.message.reply_text(
        f"✅ *{DIR_ICONS.get(direction,'📌')} {name}* qo'shildi!\n📂 {direction} | 👤 {resp}",
        parse_mode=ParseMode.MARKDOWN, reply_markup=mkb())
    return MAIN_MENU

async def cb_list_clubs(update, context):
    q = update.callback_query; await q.answer()
    rows = db().execute("""SELECT cl.name,cl.direction,cl.responsible,COUNT(cm.id)
                           FROM clubs cl LEFT JOIN club_members cm ON cl.id=cm.club_id
                           GROUP BY cl.id ORDER BY cl.direction,cl.name""").fetchall()
    if not rows:
        await q.message.reply_text("📭 To'garaklar yo'q.\n`/add_togarak <nom>`", parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    text = "🎭 *TO'GARAKLAR:*\n\n"; cur = None
    for n, d, resp, cnt in rows:
        if d != cur: text += f"\n{DIR_ICONS.get(d,'📌')} *{(d or 'Boshqa').upper()}*\n"; cur = d
        text += f"  • {n} | 👤 {resp or '—'} | 👥 {cnt}\n"
    await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return MAIN_MENU

async def cb_add_member(update, context):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("👥 O'quvchi ismini kiriting:")
    return M_SEARCH

async def m_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    search = update.message.text.strip()
    rows = db().execute("SELECT id,full_name,class_name FROM students WHERE full_name LIKE ? LIMIT 8",
                        (f"%{search}%",)).fetchall()
    if not rows: await update.message.reply_text("❌ Topilmadi."); return M_SEARCH
    if len(rows) == 1:
        context.user_data.update({"msid": rows[0][0], "msname": rows[0][1]})
        return await show_clubs_for_member(update.message, context)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"{n} ({cls or '—'})", callback_data=f"msel_{sid}")]
                                for sid, n, cls in rows])
    await update.message.reply_text("Qaysi o'quvchi?", reply_markup=kb)
    return M_SEARCH

async def cb_msel(update, context):
    q = update.callback_query; await q.answer()
    sid = int(q.data.split("_")[-1])
    row = db().execute("SELECT full_name FROM students WHERE id=?", (sid,)).fetchone()
    context.user_data.update({"msid": sid, "msname": row[0]})
    return await show_clubs_for_member(q.message, context)

async def show_clubs_for_member(message, context):
    clubs = db().execute("SELECT id,name FROM clubs ORDER BY name").fetchall()
    if not clubs:
        await message.reply_text("📭 To'garaklar yo'q. `/add_togarak <nom>`", parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(cn, callback_data=f"mjoin_{cid}")] for cid, cn in clubs])
    await message.reply_text(f"👤 *{context.user_data['msname']}*\n\nQaysi to'garak?",
                              parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return M_CLUB

async def cb_mjoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    cid = int(q.data.split("_")[-1])
    sid = context.user_data["msid"]; sname = context.user_data["msname"]
    conn = db(); c = conn.cursor()
    club = conn.execute("SELECT name FROM clubs WHERE id=?", (cid,)).fetchone()
    try:
        c.execute("INSERT INTO club_members(club_id,student_id)VALUES(?,?)", (cid, sid))
        c.execute("INSERT INTO student_media(student_id,media_type,content,added_at)VALUES(?,?,?,?)",
                  (sid,"text",f"TO'GARAK: {club[0]} ga a'zo bo'ldi",datetime.now().isoformat()))
        conn.commit()
        await q.message.reply_text(f"✅ *{sname}* → *{club[0]}* ga qo'shildi!",
                                    parse_mode=ParseMode.MARKDOWN, reply_markup=mkb())
    except:
        await q.message.reply_text(f"⚠️ *{sname}* allaqachon bu to'garakda.",
                                    parse_mode=ParseMode.MARKDOWN, reply_markup=mkb())
    conn.close()
    return MAIN_MENU

# ─── KASB YO'NALTIRISH (YANGILANGAN) ──────────────────────────────────────────
async def career_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Texnika va IT", callback_data="otm_texnika_texnologiya")],
        [InlineKeyboardButton("🏥 Tibbiyot", callback_data="otm_tibbiyot")],
        [InlineKeyboardButton("💼 Iqtisodiyot va Biznes", callback_data="otm_iqtisodiyot_biznes")],
        [InlineKeyboardButton("⚖️ Huquq va Ijtimoiy", callback_data="otm_huquq_ijtimoiy")],
        [InlineKeyboardButton("📚 Pedagogika va Tillar", callback_data="otm_pedagogika")],
        [InlineKeyboardButton("🌾 Qishloq xo'jaligi", callback_data="otm_qishloq_xojaligi")],
        [InlineKeyboardButton("🤖 AI kasb maslahat", callback_data="ai_career_maslahat")],
    ])
    await update.message.reply_text(
        "🎯 *KASB YO'NALTIRISH*\n\n🏛 *O'zbekiston OTM lari*\nQaysi yo'nalish qiziqtiradi?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

async def cb_otm_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    category = q.data.replace("otm_", "")
    data = OTM_DATA.get(category)
    if not data:
        await q.message.reply_text("❌ Ma'lumot topilmadi."); return MAIN_MENU

    text = f"{data['icon']} *{data['nom']} yo'nalishi*\n\nO'zbekistondagi top universitetlar:\n\n"
    for i, u in enumerate(data['universitetlar'], 1):
        text += (f"{'━'*25}\n"
                 f"*{i}. {u['nom']}*\n"
                 f"📍 {u['joylashuv']}\n"
                 f"📖 {u['qisqacha']}\n"
                 f"🎓 Yo'nalishlar: {u['yonalishlar']}\n"
                 f"📊 Qabul balli: {u['ball']}\n"
                 f"🎁 Grant: {u['grant']}\n"
                 f"🌐 {u['veb']}\n"
                 f"✨ {u['afzallik']}\n\n")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Bu yo'nalish bo'yicha AI maslahat", callback_data=f"ai_otm_{category}")],
        [InlineKeyboardButton("◀️ Orqaga", callback_data="back_career")],
    ])
    # Agar xabar uzun bo'lsa bo'lib yuboramiz
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for part in parts[:-1]:
            await q.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
        await q.message.reply_text(parts[-1], parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

async def cb_ai_otm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    category = q.data.replace("ai_otm_", "")
    data = OTM_DATA.get(category, {})
    nom = data.get("nom", category)
    context.user_data["ai_mode"] = True
    context.user_data["ai_context"] = f"{nom} yo'nalishi"
    await q.message.reply_text(
        f"🤖 *{nom} bo'yicha AI maslahat*\n\n"
        f"Savolingizni yozing:\n"
        f"_(Masalan: Qaysi OTM tanlayman? Ball yetmasa nima qilaman?)_\n\n"
        f"Chiqish: istalgan menyu tugmasini bosing",
        parse_mode=ParseMode.MARKDOWN)
    return AI_CHAT

async def cb_ai_career(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    context.user_data["ai_mode"] = True
    context.user_data["ai_context"] = "Umumiy kasb yo'naltirish"
    await q.message.reply_text(
        "🤖 *AI Kasb Maslahat*\n\n"
        "O'quvchi haqida yozing yoki savol bering:\n"
        "_(Masalan: O'quvchi matematikani yaxshi ko'radi, qaysi OTM tavsiya qilasiz?)_",
        parse_mode=ParseMode.MARKDOWN)
    return AI_CHAT

# ─── PORTFEL ───────────────────────────────────────────────────────────────────
async def portfolio_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 O'quvchi ismi yoki ID:", parse_mode=ParseMode.MARKDOWN)
    return PORTFOLIO

async def portfolio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in MENU_ITEMS: return await handle_menu(update, context, text)
    conn = db(); c = conn.cursor()
    if text.isdigit():
        c.execute("SELECT id,full_name,class_name FROM students WHERE id=?", (int(text),))
    else:
        c.execute("SELECT id,full_name,class_name FROM students WHERE full_name LIKE ? LIMIT 1", (f"%{text}%",))
    s = c.fetchone()
    if not s: await update.message.reply_text("❌ Topilmadi."); conn.close(); return PORTFOLIO
    sid, sname, cls = s
    media = conn.execute("SELECT media_type,content,caption,added_at FROM student_media WHERE student_id=? ORDER BY added_at", (sid,)).fetchall()
    conn.close()
    if not media:
        await update.message.reply_text(f"⚠️ Ma'lumot yo'q. `/add_media {sid}`", parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU
    msg = await update.message.reply_text(f"⏳ *{sname}* portfeli...", parse_mode=ParseMode.MARKDOWN)
    data = [{"media_type":r[0],"content":r[1],"caption":r[2],"added_at":r[3]} for r in media]
    pt = ai_portfolio(sname, cls, data)
    await msg.delete()
    await update.message.reply_text(pt, reply_markup=mkb())
    return MAIN_MENU

# ─── MOCK IMTIHON TIZIMI ───────────────────────────────────────────────────────
async def mock_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db()
    tests = conn.execute("SELECT id,title,class_name,subject,created_at FROM mock_tests WHERE is_active=1 ORDER BY created_at DESC LIMIT 10").fetchall()
    conn.close()
    kb_rows = [
        [InlineKeyboardButton("➕ Yangi test yaratish", callback_data="mock_create")],
        [InlineKeyboardButton("📊 Barcha natijalar", callback_data="mock_all_results")],
        [InlineKeyboardButton("🗑 Testni o'chirish", callback_data="mock_delete_menu")],
    ]
    text = "📝 *MOCK IMTIHON TIZIMI*\n\n"
    if tests:
        text += "*Faol testlar:*\n"
        for tid, title, cls, subj, created in tests:
            text += f"📌 *{title}* | {cls or 'Barcha'} | {subj or '—'}\n"
            kb_rows.append([InlineKeyboardButton(f"📊 {title} — natijalar", callback_data=f"mock_res_{tid}")])
    else:
        text += "_Hali testlar yo'q_\n"
    text += "\n💡 O'quvchiga test berish uchun: 👨‍🎓 → o'quvchi → 📝 MOCK berish"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=InlineKeyboardMarkup(kb_rows))
    return MAIN_MENU

async def mock_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    context.user_data["mock"] = {"questions": []}
    await q.message.reply_text(
        "📝 *YANGI TEST YARATISH*\n\nTest nomini kiriting:\n_(Masalan: Matematika MOCK #1)_",
        parse_mode=ParseMode.MARKDOWN)
    return MOCK_TITLE

async def mock_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    context.user_data["mock"]["title"] = update.message.text.strip()
    await update.message.reply_text(
        "📚 Fan nomini kiriting:\n_(Matematika, Fizika, Ingliz tili...)_")
    return MOCK_SUBJECT

async def mock_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    context.user_data["mock"]["subject"] = update.message.text.strip()
    await update.message.reply_text(
        "🏫 Qaysi sinf uchun?\n_(9-A, 10-B, 11 yoki barcha sinflar uchun 'Hammasi' deb yozing)_")
    return MOCK_CLASS

async def mock_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    cls = update.message.text.strip()
    context.user_data["mock"]["class_name"] = cls if cls.lower() != "hammasi" else None
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔤 A/B/C/D variantli savol", callback_data="mqtype_mcq")],
        [InlineKeyboardButton("✅ To'g'ri/Noto'g'ri savol", callback_data="mqtype_tf")],
    ])
    await update.message.reply_text(
        f"✅ Sinf: *{cls}*\n\nSavol turini tanlang:",
        parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MOCK_TYPE

async def mock_qtype(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    qtype = q.data.replace("mqtype_", "")
    context.user_data["mock"]["current_qtype"] = qtype
    n = len(context.user_data["mock"]["questions"]) + 1
    if qtype == "mcq":
        await q.message.reply_text(f"📝 *{n}-savol matni:*\n_(Savolni kiriting)_",
                                    parse_mode=ParseMode.MARKDOWN)
        return MOCK_Q_TEXT
    else:
        await q.message.reply_text(f"📝 *{n}-savol matni:* _(To'g'ri/Noto'g'ri)_\n_(Savolni kiriting)_",
                                    parse_mode=ParseMode.MARKDOWN)
        return MOCK_Q_TEXT

async def mock_q_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    context.user_data["mock"]["current_q"] = update.message.text.strip()
    qtype = context.user_data["mock"].get("current_qtype", "mcq")
    if qtype == "mcq":
        await update.message.reply_text(
            "📋 4 ta variant kiriting (har biri yangi qatorda):\n\n"
            "_A) ...\nB) ...\nC) ...\nD) ..._",
            parse_mode=ParseMode.MARKDOWN)
        return MOCK_Q_OPTIONS
    else:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ To'g'ri", callback_data="mqa_togri"),
             InlineKeyboardButton("❌ Noto'g'ri", callback_data="mqa_notogri")],
        ])
        await update.message.reply_text("To'g'ri javob:", reply_markup=kb)
        return MOCK_Q_ANSWER

async def mock_q_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text in MENU_ITEMS: return await handle_menu(update, context, update.message.text)
    options_text = update.message.text.strip()
    lines = [l.strip() for l in options_text.split("\n") if l.strip()]
    if len(lines) < 2:
        await update.message.reply_text("❗ Kamida 2 ta variant kiriting!")
        return MOCK_Q_OPTIONS
    context.user_data["mock"]["current_options"] = lines
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{chr(65+i)}) {l[:30]}", callback_data=f"mqa_{chr(65+i)}")]
        for i, l in enumerate(lines[:4])
    ])
    await update.message.reply_text("To'g'ri javobni tanlang:", reply_markup=kb)
    return MOCK_Q_ANSWER

async def mock_q_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    answer = q.data.replace("mqa_", "")
    mock = context.user_data["mock"]
    qtype = mock.get("current_qtype", "mcq")
    question = {
        "text": mock["current_q"],
        "type": qtype,
        "options": mock.get("current_options", ["To'g'ri", "Noto'g'ri"]),
        "answer": answer
    }
    mock["questions"].append(question)
    n = len(mock["questions"])
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ A/B/C/D savol qo'shish", callback_data="mqtype_mcq")],
        [InlineKeyboardButton("➕ To'g'ri/Noto'g'ri qo'shish", callback_data="mqtype_tf")],
        [InlineKeyboardButton(f"✅ Saqlash ({n} savol bilan)", callback_data="mock_save")],
    ])
    await q.message.reply_text(
        f"✅ *{n}-savol* saqlandi!\n\nJavob: *{answer}*\n\nYana savol qo'shasizmi?",
        parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MOCK_Q_MORE

async def mock_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    mock = context.user_data["mock"]
    if not mock.get("questions"):
        await q.message.reply_text("❗ Kamida 1 ta savol kiriting!")
        return MOCK_Q_MORE
    conn = db(); c = conn.cursor()
    c.execute("INSERT INTO mock_tests(title,subject,class_name)VALUES(?,?,?)",
              (mock["title"], mock.get("subject"), mock.get("class_name")))
    test_id = c.lastrowid
    for i, question in enumerate(mock["questions"]):
        c.execute("INSERT INTO mock_questions(test_id,question_text,question_type,options,correct_answer,order_num)VALUES(?,?,?,?,?,?)",
                  (test_id, question["text"], question["type"],
                   json.dumps(question["options"], ensure_ascii=False),
                   question["answer"], i+1))
    conn.commit(); conn.close()
    await q.message.reply_text(
        f"✅ *{mock['title']}* yaratildi!\n\n"
        f"📌 Sinf: {mock.get('class_name') or 'Barcha'}\n"
        f"📚 Fan: {mock.get('subject', '—')}\n"
        f"❓ Savollar: {len(mock['questions'])} ta\n\n"
        f"O'quvchiga berish uchun:\n👨‍🎓 → o'quvchi → 📝 MOCK berish",
        parse_mode=ParseMode.MARKDOWN, reply_markup=mkb())
    context.user_data.pop("mock", None)
    return MAIN_MENU

# ─── MOCK NATIJALAR ────────────────────────────────────────────────────────────
async def cb_mock_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    tid = int(q.data.split("_")[-1])
    conn = db()
    test = conn.execute("SELECT title,subject,class_name FROM mock_tests WHERE id=?", (tid,)).fetchone()
    results = conn.execute("""
        SELECT s.full_name, s.class_name, r.score, r.total, r.percentage, r.taken_at
        FROM mock_results r JOIN students s ON r.student_id=s.id
        WHERE r.test_id=? ORDER BY r.percentage DESC
    """, (tid,)).fetchall()
    conn.close()
    if not test: await q.message.reply_text("❌ Test topilmadi."); return MAIN_MENU
    text = f"📊 *{test[0]}* natijalari\n📚 {test[1] or '—'} | 🏫 {test[2] or 'Barcha'}\n\n"
    if not results:
        text += "_Hali hech kim test yechmagan_"
    else:
        text += f"*Jami: {len(results)} o'quvchi*\n\n"
        for i, (name, cls, score, total, pct, taken) in enumerate(results, 1):
            emoji = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else ("🟢" if pct>=70 else "🟡" if pct>=50 else "🔴")
            text += f"{emoji} *{name}* ({cls or '—'}): {score}/{total} — *{pct:.0f}%*\n"
    await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return MAIN_MENU

async def cb_mock_all_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    conn = db()
    rows = conn.execute("""
        SELECT t.title, COUNT(r.id), AVG(r.percentage)
        FROM mock_tests t LEFT JOIN mock_results r ON t.id=r.test_id
        WHERE t.is_active=1 GROUP BY t.id ORDER BY t.created_at DESC
    """).fetchall()
    conn.close()
    if not rows: await q.message.reply_text("📭 Hali natijalar yo'q."); return MAIN_MENU
    text = "📊 *BARCHA TEST NATIJALARI:*\n\n"
    for title, cnt, avg_pct in rows:
        text += f"📝 *{title}*\n   👥 {cnt or 0} o'quvchi | ⌀ {avg_pct or 0:.0f}%\n\n"
    await q.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return MAIN_MENU

# ─── MOCK BERISH (O'QUVCHIGA) ─────────────────────────────────────────────────
async def cb_mock_take(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    sid = int(q.data.split("_")[-1])
    conn = db()
    student = conn.execute("SELECT full_name,class_name FROM students WHERE id=?", (sid,)).fetchone()
    cls = student[1] if student else None
    tests = conn.execute("""
        SELECT id,title,subject FROM mock_tests WHERE is_active=1
        AND (class_name IS NULL OR class_name=? OR class_name LIKE ?)
        ORDER BY created_at DESC
    """, (cls, f"{cls[:-1] if cls else ''}%")).fetchall()
    conn.close()
    if not tests:
        await q.message.reply_text("📭 Ushbu sinf uchun aktiv testlar yo'q."); return MAIN_MENU
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"📝 {title} — {subj or '—'}", callback_data=f"mock_start_{sid}_{tid}")]
                                for tid, title, subj in tests])
    await q.message.reply_text(f"📝 *{student[0]}* uchun test tanlang:",
                                parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

async def cb_mock_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    parts = q.data.split("_")
    sid = int(parts[2]); tid = int(parts[3])
    conn = db()
    questions = conn.execute(
        "SELECT id,question_text,question_type,options,correct_answer FROM mock_questions WHERE test_id=? ORDER BY order_num",
        (tid,)).fetchall()
    conn.close()
    if not questions: await q.message.reply_text("❌ Savollar yo'q."); return MAIN_MENU
    context.user_data["mock_take"] = {
        "sid": sid, "tid": tid,
        "questions": [{"id":r[0],"text":r[1],"type":r[2],
                       "options":json.loads(r[3]) if r[3] else ["To'g'ri","Noto'g'ri"],
                       "answer":r[4]} for r in questions],
        "current": 0, "score": 0, "answers": []
    }
    await send_question(q.message, context)
    return MOCK_TAKE_ANS

async def send_question(message, context: ContextTypes.DEFAULT_TYPE):
    mt = context.user_data["mock_take"]
    idx = mt["current"]
    questions = mt["questions"]
    if idx >= len(questions):
        await finish_mock(message, context); return
    q_data = questions[idx]
    total = len(questions)
    text = f"📝 *{idx+1}/{total}-savol:*\n\n{q_data['text']}"
    if q_data["type"] == "mcq":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(opt, callback_data=f"mktake_{chr(65+i)}")]
            for i, opt in enumerate(q_data["options"][:4])
        ])
    else:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ To'g'ri", callback_data="mktake_togri"),
             InlineKeyboardButton("❌ Noto'g'ri", callback_data="mktake_notogri")]
        ])
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def cb_mock_take_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    if "mock_take" not in context.user_data: return MAIN_MENU
    mt = context.user_data["mock_take"]
    given = q.data.replace("mktake_", "")
    current_q = mt["questions"][mt["current"]]
    correct = current_q["answer"]
    is_correct = given.upper() == correct.upper()
    if is_correct: mt["score"] += 1
    mt["answers"].append({"q": current_q["text"], "given": given, "correct": correct, "ok": is_correct})
    mt["current"] += 1
    emoji = "✅" if is_correct else "❌"
    await q.message.reply_text(f"{emoji} {'To\'g\'ri!' if is_correct else f'Noto\'g\'ri. To\'g\'ri: {correct}'}")
    await send_question(q.message, context)
    return MOCK_TAKE_ANS

async def finish_mock(message, context: ContextTypes.DEFAULT_TYPE):
    mt = context.user_data["mock_take"]
    sid = mt["sid"]; tid = mt["tid"]
    score = mt["score"]; total = len(mt["questions"])
    pct = (score / total * 100) if total > 0 else 0
    conn = db(); c = conn.cursor()
    # Eski natijani yangilash yoki yangi qo'shish
    existing = conn.execute("SELECT id FROM mock_results WHERE test_id=? AND student_id=?", (tid, sid)).fetchone()
    if existing:
        c.execute("UPDATE mock_results SET score=?,total=?,percentage=?,answers=?,taken_at=? WHERE id=?",
                  (score, total, pct, json.dumps(mt["answers"], ensure_ascii=False), datetime.now().isoformat(), existing[0]))
    else:
        c.execute("INSERT INTO mock_results(test_id,student_id,score,total,percentage,answers)VALUES(?,?,?,?,?,?)",
                  (tid, sid, score, total, pct, json.dumps(mt["answers"], ensure_ascii=False)))
    # O'quvchi mediasiga ham qo'shamiz
    test_title = conn.execute("SELECT title FROM mock_tests WHERE id=?", (tid,)).fetchone()[0]
    student_name = conn.execute("SELECT full_name FROM students WHERE id=?", (sid,)).fetchone()[0]
    c.execute("INSERT INTO student_media(student_id,media_type,content,added_at)VALUES(?,?,?,?)",
              (sid,"text",f"MOCK IMTIHON: {test_title} — {score}/{total} ({pct:.0f}%)",datetime.now().isoformat()))
    conn.commit(); conn.close()

    emoji = "🟢" if pct >= 70 else "🟡" if pct >= 50 else "🔴"
    baho = "A'lo" if pct >= 90 else "Yaxshi" if pct >= 70 else "Qoniqarli" if pct >= 50 else "Qoniqarsiz"
    await message.reply_text(
        f"🏁 *{student_name} — Test yakunlandi!*\n\n"
        f"📝 {test_title}\n\n"
        f"{emoji} Natija: *{score}/{total}* ({pct:.0f}%)\n"
        f"📊 Baho: *{baho}*\n\n"
        f"{'✅ Tabriklaymiz!' if pct >= 70 else '📚 Ko\'proq o\'qish zarur.'}",
        parse_mode=ParseMode.MARKDOWN, reply_markup=mkb())
    context.user_data.pop("mock_take", None)
    return MAIN_MENU

# ─── HISOBOT ───────────────────────────────────────────────────────────────────
async def report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Umumiy hisobot", callback_data="rep_general")],
        [InlineKeyboardButton("🎭 To'garaklar", callback_data="rep_clubs")],
        [InlineKeyboardButton("🏆 Yutuqlar", callback_data="rep_ach")],
        [InlineKeyboardButton("📝 MOCK natijalari", callback_data="mock_all_results")],
    ])
    await update.message.reply_text("📊 *HISOBOT*", parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

async def cb_rep_general(update, context):
    q = update.callback_query; await q.answer()
    conn = db()
    ts = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    tc = conn.execute("SELECT COUNT(*) FROM clubs").fetchone()[0]
    ta = conn.execute("SELECT COUNT(*) FROM achievements").fetchone()[0]
    tm = conn.execute("SELECT COUNT(DISTINCT test_id) FROM mock_results").fetchone()[0]
    top = conn.execute("""SELECT s.full_name,COUNT(a.id) FROM students s
                          JOIN achievements a ON s.id=a.student_id
                          GROUP BY s.id ORDER BY COUNT(a.id) DESC LIMIT 5""").fetchall()
    conn.close()
    data = f"O'quvchilar: {ts}, To'garaklar: {tc}, Yutuqlar: {ta}, MOCK testlar: {tm}, Top: {top}"
    msg = await q.message.reply_text("⏳ Hisobot tayyorlanmoqda...")
    report = ai_report("UMUMIY MAKTAB", data)
    await msg.edit_text(report)
    return MAIN_MENU

async def cb_rep_clubs(update, context):
    q = update.callback_query; await q.answer()
    rows = db().execute("""SELECT cl.name,cl.direction,cl.responsible,COUNT(cm.id)
                           FROM clubs cl LEFT JOIN club_members cm ON cl.id=cm.club_id
                           GROUP BY cl.id ORDER BY COUNT(cm.id) DESC""").fetchall()
    if not rows: await q.message.reply_text("📭 To'garaklar yo'q."); return MAIN_MENU
    data = "\n".join([f"{r[0]}: {r[1]}, {r[2]}, {r[3]} a'zo" for r in rows])
    msg = await q.message.reply_text("⏳ Hisobot...")
    await msg.edit_text(ai_report("TO'GARAKLAR", data))
    return MAIN_MENU

async def cb_rep_ach(update, context):
    q = update.callback_query; await q.answer()
    rows = db().execute("""SELECT s.full_name,s.class_name,a.title,a.achievement_type,a.date
                           FROM achievements a JOIN students s ON a.student_id=s.id ORDER BY a.date DESC""").fetchall()
    if not rows: await q.message.reply_text("📭 Yutuqlar yo'q."); return MAIN_MENU
    data = "\n".join([f"{r[0]}({r[1]}): {r[2]}, {r[3]}, {r[4]}" for r in rows])
    msg = await q.message.reply_text("⏳ Hisobot...")
    await msg.edit_text(ai_report("YUTUQLAR", data))
    return MAIN_MENU

# ─── YORDAM ────────────────────────────────────────────────────────────────────
async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨‍🎓 O'quvchi qo'shishni o'rgat", callback_data="teach_students")],
        [InlineKeyboardButton("🎭 To'garak qo'shishni o'rgat", callback_data="teach_clubs")],
        [InlineKeyboardButton("📝 MOCK test yaratishni o'rgat", callback_data="teach_mock")],
        [InlineKeyboardButton("📋 Portfel yaratishni o'rgat", callback_data="teach_portfolio")],
        [InlineKeyboardButton("💬 O'z savolimni yozaman", callback_data="ai_free")],
    ])
    await update.message.reply_text("❓ *YORDAM VA AI MASLAHAT*",
                                     parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    return MAIN_MENU

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text in MENU_ITEMS:
        context.user_data.pop("ai_mode", None)
        return await handle_menu(update, context, text)
    ai_ctx = context.user_data.get("ai_context", "AI suhbat")
    msg = await update.message.reply_text("🤔 AI o'ylamoqda...")
    answer = ai_guide(text, ai_ctx)
    await msg.edit_text(f"🤖 *AI:*\n\n{answer}", parse_mode=ParseMode.MARKDOWN)
    return AI_CHAT

TEACH_Q = {
    "teach_students": "O'quvchi qo'shish: 👨‍🎓 tugma → ➕ Yangi → ism → sinf → ID beriladi → /add_media ID → ma'lumot yubor → /done. Batafsil tushuntir.",
    "teach_clubs": "To'garak qo'shish: /add_togarak Robototexnika yoki 🎭 → ➕ → nom → yo'nalish → mas'ul. A'zo qo'shish ham tushuntir.",
    "teach_mock": "MOCK test yaratish: 📝 MOCK → ➕ Yangi → nom → fan → sinf → savol qo'sh → saqlash. Keyin o'quvchiga berish: 👨‍🎓 → o'quvchi → 📝 MOCK berish. Batafsil tushuntir.",
    "teach_portfolio": "Portfel: avval /add_media ID bilan ma'lumot qo'sh → keyin 📋 Portfel → ism yoki ID kiriting → AI avtomatik tayyorlaydi.",
    "teach_ach": "Yutuq qo'shish: 🏆 → ➕ → o'quvchi ism → yutuq nomi → tur → sana.",
    "teach_career": "Kasb yo'naltirish: 🎯 tugmasi → yo'nalish tanlang → OTM ma'lumotlari ko'rinsiz → AI maslahat so'rang.",
}

# ─── CALLBACK DISPATCHER ──────────────────────────────────────────────────────
async def cb_dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; d = q.data

    if d in TEACH_Q:
        await q.answer()
        msg = await q.message.reply_text("🤔 AI o'ylamoqda...")
        await msg.edit_text(f"🤖 *AI Qo'llanma:*\n\n{ai_guide(TEACH_Q[d], d)}", parse_mode=ParseMode.MARKDOWN)
        return MAIN_MENU

    if d == "ai_free":
        await q.answer(); context.user_data["ai_mode"] = True
        await q.message.reply_text("💬 Savolingizni yozing:"); return AI_CHAT

    if d == "back_career":
        await q.answer()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ Texnika va IT", callback_data="otm_texnika_texnologiya")],
            [InlineKeyboardButton("🏥 Tibbiyot", callback_data="otm_tibbiyot")],
            [InlineKeyboardButton("💼 Iqtisodiyot va Biznes", callback_data="otm_iqtisodiyot_biznes")],
            [InlineKeyboardButton("⚖️ Huquq va Ijtimoiy", callback_data="otm_huquq_ijtimoiy")],
            [InlineKeyboardButton("📚 Pedagogika va Tillar", callback_data="otm_pedagogika")],
            [InlineKeyboardButton("🌾 Qishloq xo'jaligi", callback_data="otm_qishloq_xojaligi")],
            [InlineKeyboardButton("🤖 AI kasb maslahat", callback_data="ai_career_maslahat")],
        ])
        await q.message.reply_text("🎯 *KASB YO'NALTIRISH*", parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
        return MAIN_MENU

    simple = {
        "add_student": cb_add_student, "srch_student": cb_srch_student,
        "list_students": cb_list_students, "add_ach": cb_add_ach,
        "list_ach": cb_list_ach, "add_club": cb_add_club,
        "list_clubs": cb_list_clubs, "add_member": cb_add_member,
        "rep_general": cb_rep_general, "rep_clubs": cb_rep_clubs,
        "rep_ach": cb_rep_ach, "mock_create": mock_create_start,
        "mock_all_results": cb_mock_all_results,
        "ai_career_maslahat": cb_ai_career,
    }
    for key, handler in simple.items():
        if d == key: return await handler(update, context)

    if d.startswith("otm_"): return await cb_otm_category(update, context)
    if d.startswith("ai_otm_"): return await cb_ai_otm(update, context)
    if d.startswith("sp_"): return await cb_student_profile(update, context)
    if d.startswith("asel_"): return await cb_asel(update, context)
    if d.startswith("msel_"): return await cb_msel(update, context)
    if d.startswith("mjoin_"): return await cb_mjoin(update, context)
    if d.startswith("cd_"): return await cb_cdir(update, context)
    if d.startswith("at_"): return await cb_atype(update, context)
    if d.startswith("mqtype_"): return await mock_qtype(update, context)
    if d.startswith("mqa_"): return await mock_q_answer(update, context)
    if d == "mock_save": return await mock_save(update, context)
    if d.startswith("mock_res_"): return await cb_mock_results(update, context)
    if d.startswith("mock_take_") and len(d.split("_")) == 3: return await cb_mock_take(update, context)
    if d.startswith("mock_start_"): return await cb_mock_start(update, context)
    if d.startswith("mktake_"): return await cb_mock_take_answer(update, context)

    if d.startswith("pf_"):
        sid = int(d.split("_")[-1]); await q.answer()
        conn = db()
        s = conn.execute("SELECT full_name,class_name FROM students WHERE id=?", (sid,)).fetchone()
        media = conn.execute("SELECT media_type,content,caption,added_at FROM student_media WHERE student_id=? ORDER BY added_at", (sid,)).fetchall()
        conn.close()
        if not s: return MAIN_MENU
        if not media:
            await q.message.reply_text(f"⚠️ Ma'lumot yo'q. `/add_media {sid}`", parse_mode=ParseMode.MARKDOWN)
            return MAIN_MENU
        msg = await q.message.reply_text(f"⏳ *{s[0]}* portfeli...", parse_mode=ParseMode.MARKDOWN)
        data = [{"media_type":r[0],"content":r[1],"caption":r[2],"added_at":r[3]} for r in media]
        await msg.edit_text(ai_portfolio(s[0], s[1], data))
        return MAIN_MENU

    if d.startswith("am_"):
        sid = int(d.split("_")[-1]); await q.answer()
        row = db().execute("SELECT full_name FROM students WHERE id=?", (sid,)).fetchone()
        if row:
            context.user_data["tsid"] = sid; context.user_data["tsname"] = row[0]
            await q.message.reply_text(f"📁 *{row[0]}* uchun yuboring:\n📝 Matn | 🖼 Rasm | 🎥 Video\n\n/done",
                                        parse_mode=ParseMode.MARKDOWN)
        return S_DATA

    if d.startswith("aa_"):
        sid = int(d.split("_")[-1]); await q.answer()
        row = db().execute("SELECT full_name FROM students WHERE id=?", (sid,)).fetchone()
        if row:
            context.user_data.update({"asid": sid, "asname": row[0]})
            await q.message.reply_text(f"🏆 *{row[0]}* yutuq nomi:", parse_mode=ParseMode.MARKDOWN)
        return A_TITLE

    await q.answer("⚙️")
    return MAIN_MENU

# ─── ASOSIY ROUTER ─────────────────────────────────────────────────────────────
async def main_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await chk(update): return MAIN_MENU
    text = update.message.text
    if text in MENU_ITEMS:
        context.user_data.pop("tsid", None); context.user_data.pop("tsname", None)
        context.user_data.pop("ai_mode", None); context.user_data.pop("mock_take", None)
        return await handle_menu(update, context, text)
    if context.user_data.get("tsid"): return await receive_media(update, context)
    if context.user_data.get("ai_mode"): return await ai_chat(update, context)
    return MAIN_MENU

# ─── MAIN ──────────────────────────────────────────────────────────────────────
async def main():
    init_db()
    logger.info("🚀 Bot v6 ishga tushmoqda...")
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU:      [MessageHandler(filters.ALL & ~filters.COMMAND, main_router),
                             CallbackQueryHandler(cb_dispatch)],
            S_NAME:         [MessageHandler(filters.TEXT & ~filters.COMMAND, s_name)],
            S_CLASS:        [MessageHandler(filters.TEXT & ~filters.COMMAND, s_class)],
            S_DATA:         [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_media),
                             MessageHandler(filters.PHOTO, receive_media),
                             MessageHandler(filters.VIDEO, receive_media),
                             MessageHandler(filters.Document.ALL, receive_media),
                             CommandHandler("done", done_cmd)],
            S_SEARCH:       [MessageHandler(filters.TEXT & ~filters.COMMAND, s_search)],
            PORTFOLIO:      [MessageHandler(filters.TEXT & ~filters.COMMAND, portfolio_handler)],
            C_NAME:         [MessageHandler(filters.TEXT & ~filters.COMMAND, c_name)],
            C_DIR:          [CallbackQueryHandler(cb_cdir, pattern="^cd_")],
            C_RESP:         [MessageHandler(filters.TEXT & ~filters.COMMAND, c_resp)],
            A_STUDENT:      [MessageHandler(filters.TEXT & ~filters.COMMAND, a_student),
                             CallbackQueryHandler(cb_asel, pattern="^asel_")],
            A_TITLE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, a_title)],
            A_TYPE:         [CallbackQueryHandler(cb_atype, pattern="^at_")],
            A_DATE:         [MessageHandler(filters.TEXT & ~filters.COMMAND, a_date)],
            AI_CHAT:        [MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat),
                             CommandHandler("done", done_cmd)],
            M_SEARCH:       [MessageHandler(filters.TEXT & ~filters.COMMAND, m_search),
                             CallbackQueryHandler(cb_msel, pattern="^msel_")],
            M_CLUB:         [CallbackQueryHandler(cb_mjoin, pattern="^mjoin_")],
            MOCK_TITLE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, mock_title)],
            MOCK_SUBJECT:   [MessageHandler(filters.TEXT & ~filters.COMMAND, mock_subject)],
            MOCK_CLASS:     [MessageHandler(filters.TEXT & ~filters.COMMAND, mock_class)],
            MOCK_TYPE:      [CallbackQueryHandler(mock_qtype, pattern="^mqtype_")],
            MOCK_Q_TEXT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, mock_q_text)],
            MOCK_Q_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, mock_q_options)],
            MOCK_Q_ANSWER:  [CallbackQueryHandler(mock_q_answer, pattern="^mqa_")],
            MOCK_Q_MORE:    [CallbackQueryHandler(cb_dispatch)],
            MOCK_TAKE_ANS:  [CallbackQueryHandler(cb_mock_take_answer, pattern="^mktake_")],
        },
        fallbacks=[CommandHandler("start", start),
                   MessageHandler(filters.Regex("^🏠 Bosh menyu$"), start)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("add_media", add_media_cmd))
    app.add_handler(CommandHandler("add_togarak", add_togarak_cmd))
    app.add_handler(CommandHandler("hisobot", report_menu))
    app.add_handler(CommandHandler("mock_test", mock_menu))
    app.add_handler(CommandHandler("mock_natija", lambda u,c: mock_menu(u,c)))
    app.add_handler(CallbackQueryHandler(cb_dispatch))
    logger.info("✅ Bot v6 tayyor!")
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
        logger.info("✅ Ishlayapti!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

# 🏫 Maktab Maslahatchisi Telegram Bot

## 📋 UMUMIY MA'LUMOT

Bu bot maktab maslahatchisi uchun yaratilgan bo'lib, quyidagi imkoniyatlarni beradi:

- 👨‍🎓 O'quvchilar profilini boshqarish
- 📁 Matn, rasm, video orqali ma'lumot yig'ish
- 🤖 Claude AI orqali avtomatik ijtimoiy portfel yaratish
- 🏆 Yutuq va olimpiadalarni kuzatish
- 🎭 To'garaklar va yo'nalishlarni boshqarish
- 🎯 Kasb yo'naltirish ma'lumotlari
- 💾 SQLite + Google Sheets ikki tomonlama saqlash
- 🔄 24/7 to'xtovsiz ishlash

---

## 🚀 O'RNATISH (QADAM BA QADAM)

### 1-QADAM: Telegram Bot Token olish

1. Telegramda `@BotFather` ga o'ting
2. `/newbot` yozing
3. Bot nomini kiriting: `Maktab Maslahatchisi`
4. Bot username kiriting: `maktab_maslahatchi_bot`
5. BotFather bergan **TOKEN** ni saqlab qo'ying

### 2-QADAM: Claude API Key olish

1. `https://console.anthropic.com` saytiga o'ting
2. Ro'yxatdan o'ting yoki kiring
3. **API Keys** bo'limiga o'ting
4. **Create Key** tugmasini bosing
5. Kalitni nusxalab oling

### 3-QADAM: Admin ID ni bilish

1. Telegramda `@userinfobot` ga o'ting
2. `/start` yozing
3. U sizga **ID raqamingizni** ko'rsatadi
4. Bu raqamni saqlab qo'ying

### 4-QADAM: Serverga o'rnatish

```bash
# Fayllarni serverga yuklang
git clone https://github.com/yourname/maktab_bot  # yoki fayllarni ko'chiring
cd maktab_bot

# .env faylini yarating
cp .env.example .env
nano .env
```

`.env` faylini to'ldiring:
```
BOT_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_IDS=123456789
GOOGLE_SHEET_ID=
```

```bash
# O'rnatish skriptini ishga tushiring
chmod +x setup.sh
bash setup.sh
```

---

## 💻 BOTDAN FOYDALANISH

### Asosiy Menyular

| Tugma | Vazifasi |
|-------|----------|
| 👨‍🎓 O'quvchilar boshqaruvi | O'quvchi qo'shish, qidirish, profil ko'rish |
| 🏆 Yutuq va olimpiadalar | Diplomlar, sertifikatlar, g'alabalar |
| 🎭 To'garaklar va yo'nalishlar | Madaniyat, texnologiya, sport, san'at |
| 🎯 Kasb yo'naltirish | Universitet, kasb, MOCK natijalar |
| 📋 Portfel yaratish | AI orqali ijtimoiy portfel tayyorlash |
| ❓ AI maslahat | Istalgan savol — Claude AI javob beradi |

---

### O'quvchi qo'shish va ma'lumot yig'ish

**1. O'quvchi profili yaratish:**
```
👨‍🎓 O'quvchilar boshqaruvi → ➕ Yangi o'quvchi qo'shish
→ Ismini kiriting: Karimov Jasur Aliyevich
→ Sinfini kiriting: 9-A
✅ ID: 1 beriladi
```

**2. Ma'lumot qo'shish:**
```
/add_media 1
```
Keyin xohlagan narsani yuboring:
- 📝 Matn: "Matematika olimpiadasida 1-o'rin oldi"
- 🖼 Rasm: diplom rasmi + izoh
- 🎥 Video: musobaqa videosi
- 📄 Hujjat: sertifikat PDF

Tugatganda: `/done`

**3. Portfel yaratish:**
```
📋 Portfel yaratish → "Karimov" yoki "1" kiriting
```
Claude AI 10-15 soniyada professional portfel tayyorlaydi.

---

### Portfel namunasi (Claude AI tomonidan)

```
📋 IJTIMOIY PORTFEL: Karimov Jasur Aliyevich
━━━━━━━━━━━━━━━━━━━━━━━━

👤 UMUMIY MA'LUMOT
9-A sinf o'quvchisi. Matematika va fizika yo'nalishida
kuchli, faol ijtimoiy hayot ishtirokchisi.

🏆 YUTUQLAR VA MUVAFFAQIYATLAR
• 2024 — Viloyat matematika olimpiadasi, 1-o'rin
• 2024 — Respublika fizika musobaqasi, 2-o'rin
• IELTS 6.5 ball (2024-yil mart)

🎭 TO'GARAKLAR VA FAOLIYATLAR
• "Kelajak" markazi — dasturlash to'garagi
• Maktab "Debate" klubi — faol a'zo
• "Eco-schools" ekologiya loyihasi ishtirokchisi

🎯 KELAJAK REJALARI
MIT yoki INHA universitetiga kirish maqsadi bor.
Sun'iy intellekt yo'nalishi qiziqtiradi.

💡 SHAXSIY SIFATLAR
Tashabbuskor, jamoada ishlash qobiliyati yuqori,
mustaqil fikrlovchi.

📊 MASLAHATCHI XULOSASI
Jasur kuchli akademik ko'rsatkichlar va faol
ijtimoiy hayotini muvozanatda ushlab turoladi.
INHA yoki xalqaro universitetlarga tavsiya etiladi.
━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔧 QOSHIMCHA SOZLAMALAR

### Google Sheets ulash (ixtiyoriy)

1. `https://console.cloud.google.com` → yangi loyiha
2. **Google Sheets API** va **Google Drive API** ni yoqing
3. **Service Account** yarating
4. `credentials.json` faylini yuklab oling va bot papkasiga qo'ying
5. `.env` da `GOOGLE_SHEET_ID` ni to'ldiring

### Bir nechta admin qo'shish

`.env` faylida:
```
ADMIN_IDS=123456789,987654321,111222333
```

---

## 🔄 24/7 ISHLASH

Bot `systemd` orqali avtomatik ishga tushadi va crash bo'lsa qayta tushadi.

```bash
# Holat ko'rish
sudo systemctl status maktab-bot

# Loglarni kuzatish (real vaqtda)
sudo journalctl -u maktab-bot -f

# Qayta ishga tushirish
sudo systemctl restart maktab-bot

# To'xtatish
sudo systemctl stop maktab-bot
```

---

## 🌐 ARZON SERVER VARIANTLARI

| Xizmat | Narx | Tavsiya |
|--------|------|---------|
| Oracle Cloud (Free) | Bepul | ⭐⭐⭐ |
| Render.com | Bepul (limited) | ⭐⭐ |
| Railway.app | $5/oy | ⭐⭐⭐ |
| DigitalOcean | $6/oy | ⭐⭐⭐⭐ |
| VPS.uz | ~50,000 so'm/oy | ⭐⭐⭐ |

---

## 📞 TEXNIK YORDAM

Xato yuz bersa loglarni tekshiring:
```bash
sudo journalctl -u maktab-bot --since "1 hour ago"
```

Yoki `bot.log` faylini oching.

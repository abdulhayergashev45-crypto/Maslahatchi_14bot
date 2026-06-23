#!/bin/bash
# ============================================================
# Maktab Maslahatchisi Bot — O'rnatish va Ishga Tushirish
# ============================================================

set -e
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🏫 Maktab Maslahatchisi Bot o'rnatilmoqda...${NC}"

# 1. Python va pip tekshirish
echo -e "${YELLOW}1. Python tekshirilmoqda...${NC}"
python3 --version || { echo -e "${RED}Python3 topilmadi!${NC}"; exit 1; }
pip3 --version || apt-get install -y python3-pip

# 2. Kerakli paketlar o'rnatish
echo -e "${YELLOW}2. Paketlar o'rnatilmoqda...${NC}"
pip3 install -r requirements.txt

# 3. .env fayl tekshirish
echo -e "${YELLOW}3. .env konfiguratsiya tekshirilmoqda...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${RED}⚠️  .env fayl yaratildi. Iltimos tokenlarni kiriting:${NC}"
    echo -e "   nano .env"
    echo ""
    echo "Keyin qayta ishga tushiring: bash setup.sh"
    exit 1
fi

# .env yuklash
export $(grep -v '^#' .env | xargs)

# Token tekshirish
if [ "$BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo -e "${RED}❌ BOT_TOKEN kiritilmagan! .env faylini tahrirlang.${NC}"
    exit 1
fi
if [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
    echo -e "${RED}❌ ANTHROPIC_API_KEY kiritilmagan! .env faylini tahrirlang.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Tokenlar topildi!${NC}"

# 4. Bazani initsializatsiya qilish (test)
echo -e "${YELLOW}4. Database yaratilmoqda...${NC}"
python3 -c "
import sqlite3
conn = sqlite3.connect('maktab.db')
print('✅ SQLite database tayyor')
conn.close()
"

# 5. Systemd service o'rnatish (ixtiyoriy)
read -p "24/7 ishlash uchun systemd service o'rnatilsinmi? (y/n): " install_service
if [ "$install_service" = "y" ]; then
    CURRENT_DIR=$(pwd)
    CURRENT_USER=$(whoami)
    
    # Service faylni yangilash
    sed -i "s|/home/ubuntu/maktab_bot|$CURRENT_DIR|g" maktab-bot.service
    sed -i "s|User=ubuntu|User=$CURRENT_USER|g" maktab-bot.service
    
    sudo cp maktab-bot.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable maktab-bot
    sudo systemctl start maktab-bot
    
    echo -e "${GREEN}✅ Bot systemd service sifatida o'rnatildi va ishga tushirildi!${NC}"
    echo ""
    echo "📊 Status ko'rish:    sudo systemctl status maktab-bot"
    echo "📋 Loglar ko'rish:    sudo journalctl -u maktab-bot -f"
    echo "🔄 Qayta ishlatish:   sudo systemctl restart maktab-bot"
    echo "⏹  To'xtatish:        sudo systemctl stop maktab-bot"
else
    echo -e "${YELLOW}Bot oddiy rejimda ishga tushirilmoqda...${NC}"
    echo "To'xtatish uchun Ctrl+C bosing"
    echo ""
    python3 bot.py
fi

echo -e "${GREEN}🎉 O'rnatish muvaffaqiyatli yakunlandi!${NC}"

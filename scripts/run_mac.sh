#!/bin/bash

# 📊 Portföy Analiz Platformu — Mac Launcher
# ===================================================

# Renkler
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Portföy Analiz Platformu başlatılıyor...${NC}"

# Sanal ortam kontrolü
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment (.venv)...${NC}"
    python3 -m venv .venv
fi

# Sanal ortamı aktif et
source .venv/bin/activate

# Bağımlılıkları kontrol et / güncelle
echo -e "${YELLOW}Checking dependencies...${NC}"
pip install -r requirements.txt

# .env dosyası kontrolü
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env from .env.example...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ .env dosyası oluşturuldu.${NC}"
        echo -e "${RED}⚠️  Lütfen .env dosyasını açıp API anahtarlarınızı (GEMINI_API_KEY vb.) girin.${NC}"
    else
        echo -e "${RED}Warning: .env.example not found. Cannot create .env.${NC}"
    fi
fi

# Uygulamayı başlat
echo -e "${GREEN}🌐 Başlatılıyor: http://127.0.0.1:8000/ui ${NC}"
uvicorn src.api.main:app --reload

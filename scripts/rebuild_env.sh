#!/bin/bash
# 🛡️ rebuild_env.sh: Steril Ortam Yeniden Kurulum Betiği
# ==========================================================

# Adım 1: Mevcut venv klasörünü temizle
echo "🧹 Mevcut 'venv' dizini siliniyor..."
rm -rf venv

# Adım 2: Python 3.11 ile yeni venv oluştur
# /opt/homebrew/bin/python3.11 dizini daha önce QA araştırmasında tespit edilmiştir.
PYTHON_PATH="/opt/homebrew/bin/python3.11"

if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ HATA: $PYTHON_PATH bulunamadı!"
    exit 1
fi

echo "🐍 Python 3.11 ile yeni sanal ortam kuruluyor..."
$PYTHON_PATH -m venv venv

# Adım 3: Bağımlılıkları kur
echo "📦 Bağımlılıklar (requirements.txt) yükleniyor..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Adım 4: Sürüm doğrulama
echo "✅ BAŞARILI: Ortam sterilize edildi."
python --version
echo "--------------------------------------------------------"

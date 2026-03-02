#!/bin/bash
# AI İslami Portföy Yöneticisi Başlatıcı (Mac/Linux)

echo "AI İslami Portföy Yöneticisi Başlatılıyor..."

# Proje dizinine git
cd "$(dirname "$0")"

# Gerekli kütüphanelerin yüklü olduğunu doğrula
echo "Gereksinimler kontrol ediliyor..."
python3 -m pip install -r requirements.txt -q

# Masaüstü uygulamasını arka planda başlat
echo "Sunucu başlatılıyor, lütfen bekleyin..."
python3 src/desktop_app.py

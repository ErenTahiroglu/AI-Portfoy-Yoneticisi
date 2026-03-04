#!/bin/bash
# AI İslami Portföy Yöneticisi Başlatıcı (Mac/Linux)

echo "AI İslami Portföy Yöneticisi Başlatılıyor..."

# Proje dizinine git
cd "$(dirname "$0")"

# Python check
if ! command -v python3 &> /dev/null
then
    echo "[Hata] Python3 bulunamadı! Lütfen Python 3 kurulumunu yapın."
    read -p "Çıkmak için Enter'a basın..."
    exit
fi

# Gerekli kütüphanelerin yüklü olduğunu doğrula
echo "Gereksinimler kontrol ediliyor ve yükleniyor (bu işlem biraz sürebilir)..."
python3 -m pip install -r requirements.txt

# Sanal tarayıcı (Playwright) bileşenlerini yükle
echo "Sanal tarayıcı (Playwright) bileşenleri kontrol ediliyor..."
python3 -m playwright install chromium
# Masaüstü uygulamasını arka planda başlat
echo ""
echo "Sunucu başlatılıyor, lütfen bekleyin..."
python3 src/desktop_app.py

echo ""
echo "Uygulama kapatıldı veya bir hata oluştu. Lütfen yukarıdaki hata mesajını kontrol edin."
read -p "Çıkmak için Enter'a basın..."

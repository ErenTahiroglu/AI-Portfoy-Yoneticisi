@echo off
title AI Islami Portfoy Yoneticisi
echo AI Islami Portfoy Yoneticisi Baslatiliyor...

cd /d "%~dp0"

echo Python kurulumu kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Hata] Python bulunamadi!
    echo Lutfen Python'u "Add to PATH" secenegini isaretleyerek kurdugunuzdan emin olun.
    echo Veya Microsoft Store uzerinden Python 3.10+ indirin.
    pause
    exit /b
)

echo Gereksinimler kontrol ediliyor ve yukleniyor (bu islem biraz surebilir)...
pip install -r requirements.txt
echo Sanal tarayici (Playwright) bilesenleri yukleniyor...
playwright install chromium
echo.
echo Sunucu baslatiliyor, lutfen bekleyin...
python src\desktop_app.py

echo.
echo Uygulama kapatildi veya baslatilamadi. Lutfen yukaridaki hata mesajini kontrol edin.
pause

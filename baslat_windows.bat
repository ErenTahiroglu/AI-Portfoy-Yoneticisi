@echo off
title AI İslami Portfoy Yoneticisi
echo AI Islami Portfoy Yoneticisi Baslatiliyor...

cd /d "%~dp0"

echo Gereksinimler kontrol ediliyor...
pip install -r requirements.txt -q >nul 2>&1

echo Sunucu baslatiliyor, lutfen bekleyin...
python src\desktop_app.py

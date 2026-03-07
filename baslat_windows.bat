@echo off
chcp 65001 >nul 2>&1
title Portfoy Analiz Platformu
echo ══════════════════════════════════════
echo   Portfoy Analiz Platformu
echo ══════════════════════════════════════
echo.

cd /d "%~dp0"

:: ── Python kontrolu ──────────────────────────────────────────────
echo [1/4] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo       Python bulundu.
    goto :python_ok
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo       Python bulundu (py launcher).
    set "PYTHON_CMD=py"
    goto :python_ok
)

:: Python bulunamadi — otomatik kurmaya calis
echo       Python bulunamadi! Otomatik kurulum deneniyor...
echo.

:: Yontem 1: winget ile kur (Windows 10/11 dahili)
winget --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] winget ile Python 3.12 kuruluyor...
    echo     (Bu islem 1-2 dakika surebilir, lutfen bekleyin)
    winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
    if %errorlevel% equ 0 (
        echo.
        echo [OK] Python basariyla kuruldu!
        echo [!]  ONEMLI: Bu penceyi KAPATIN ve baslat_windows.bat'i TEKRAR CALISTIRIN.
        echo      (Yeni kurulum PATH'e eklenmis olacak)
        echo.
        pause
        exit /b
    )
)

:: Yontem 2: Dogrudan Python.org'dan indir
echo [*] winget bulunamadi veya basarisiz oldu.
echo [*] Python.org'dan indiriliyor...
set "PYTHON_URL=https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
set "INSTALLER=%TEMP%\python_installer.exe"

:: curl veya PowerShell ile indir
curl -L -o "%INSTALLER%" "%PYTHON_URL%" 2>nul
if not exist "%INSTALLER%" (
    powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%INSTALLER%'" 2>nul
)

if not exist "%INSTALLER%" (
    echo.
    echo [Hata] Python indirilemedi!
    echo        Lutfen python.org/downloads adresinden manuel olarak indirip kurun.
    echo        Kurarken "Add Python to PATH" kutucugunu isaretlemeyi unutmayin!
    pause
    exit /b
)

echo [*] Python kuruluyor (sessiz mod + PATH ekleme)...
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1

if %errorlevel% equ 0 (
    echo.
    echo [OK] Python basariyla kuruldu!
    del "%INSTALLER%" >nul 2>&1
    echo [!]  ONEMLI: Bu pencereyi KAPATIN ve baslat_windows.bat'i TEKRAR CALISTIRIN.
    pause
    exit /b
) else (
    echo.
    echo [Hata] Kurulum basarisiz oldu.
    echo        python.org/downloads adresinden manuel kurun.
    echo        "Add Python to PATH" kutucugunu isaretlemeyi unutmayin!
    del "%INSTALLER%" >nul 2>&1
    pause
    exit /b
)

:python_ok
if not defined PYTHON_CMD set "PYTHON_CMD=python"

:: ── Sanal ortam kontrolu ─────────────────────────────────────────
echo [2/4] Sanal ortam kontrol ediliyor...
if not exist ".venv\Scripts\activate.bat" (
    echo       Sanal ortam olusturuluyor...
    %PYTHON_CMD% -m venv .venv
)
call .venv\Scripts\activate.bat

:: ── Bagimliliklar ────────────────────────────────────────────────
echo [3/4] Gereksinimler kontrol ediliyor...
pip install -r requirements.txt --quiet
echo       Playwright tarayici kontrol ediliyor...
playwright install chromium --with-deps >nul 2>&1

:: ── Baslat ───────────────────────────────────────────────────────
echo [4/4] Sunucu baslatiliyor...
echo.
python src\desktop_app.py

echo.
echo Uygulama kapatildi.
pause

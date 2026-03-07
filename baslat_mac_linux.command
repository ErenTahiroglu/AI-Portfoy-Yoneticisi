#!/bin/bash
# ══════════════════════════════════════
#   Portföy Analiz Platformu
#   Mac/Linux Başlatıcı
# ══════════════════════════════════════

echo "══════════════════════════════════════"
echo "  Portföy Analiz Platformu"
echo "══════════════════════════════════════"
echo ""

# Proje dizinine git
cd "$(dirname "$0")"

# ── Python kontrolü ─────────────────────────────────────────────
echo "[1/4] Python kontrol ediliyor..."

PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo "      Python3 bulundu."
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "      Python bulundu."
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "      Python bulunamadı! Otomatik kurulum deneniyor..."
    echo ""
    
    # macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            echo "[*] Homebrew ile Python kuruluyor..."
            brew install python3
            PYTHON_CMD="python3"
        else
            echo "[*] Homebrew bulunamadı. Önce Homebrew kuruluyor..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install python3
            PYTHON_CMD="python3"
        fi
    
    # Debian/Ubuntu
    elif command -v apt-get &> /dev/null; then
        echo "[*] apt ile Python kuruluyor (sudo gerekebilir)..."
        sudo apt-get update -qq
        sudo apt-get install -y python3 python3-pip python3-venv
        PYTHON_CMD="python3"
    
    # Fedora/RHEL
    elif command -v dnf &> /dev/null; then
        echo "[*] dnf ile Python kuruluyor (sudo gerekebilir)..."
        sudo dnf install -y python3 python3-pip
        PYTHON_CMD="python3"
    
    # Arch
    elif command -v pacman &> /dev/null; then
        echo "[*] pacman ile Python kuruluyor (sudo gerekebilir)..."
        sudo pacman -Sy --noconfirm python python-pip
        PYTHON_CMD="python3"
    
    else
        echo ""
        echo "[Hata] Python otomatik kurulamadı!"
        echo "       Lütfen python.org/downloads adresinden manuel olarak kurun."
        read -p "Çıkmak için Enter'a basın..."
        exit 1
    fi
    
    # Kurulumu doğrula
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo "[Hata] Python kurulumu başarısız oldu."
        echo "       Lütfen python.org/downloads adresinden manuel olarak kurun."
        read -p "Çıkmak için Enter'a basın..."
        exit 1
    fi
    echo "[OK] Python başarıyla kuruldu!"
fi

# ── Sanal ortam kontrolü ────────────────────────────────────────
echo "[2/4] Sanal ortam kontrol ediliyor..."
if [ ! -d ".venv" ]; then
    echo "      Sanal ortam oluşturuluyor..."
    $PYTHON_CMD -m venv .venv
fi
source .venv/bin/activate

# ── Bağımlılıklar ───────────────────────────────────────────────
echo "[3/4] Gereksinimler kontrol ediliyor..."
pip install -r requirements.txt --quiet
echo "      Playwright tarayıcı kontrol ediliyor..."
playwright install chromium 2>/dev/null

# ── Başlat ──────────────────────────────────────────────────────
echo "[4/4] Sunucu başlatılıyor..."
echo ""
$PYTHON_CMD src/desktop_app.py

echo ""
echo "Uygulama kapatıldı."
read -p "Çıkmak için Enter'a basın..."

"""
🧩 Puzzle Parça: Dosya İşleme (Excel/DOCX/PDF)
=================================================
Kullanıcının yüklediği dosyalardan ticker çıkarır,
analiz sonuçlarını Excel/PDF/DOCX formatında dışa aktarır.
"""

import logging
import os
import re
import io

import pandas as pd
import docx
from fpdf import FPDF

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Ticker Çıkarma
# ══════════════════════════════════════════════════════════════════════════════

def extract_tickers_from_text(text):
    """Metinden hisse/fon sembollerini çıkarır (AAPL, TP2, THYAO.IS vb.)."""
    words = re.findall(r'\b[A-Za-z][A-Za-z0-9.]*\b', text)
    return list(set([word.upper() for word in words]))


def process_uploaded_file(uploaded_file):
    pass  # Removed as part of dead code cleanup


# ══════════════════════════════════════════════════════════════════════════════
# Excel Dışa Aktarım
# ══════════════════════════════════════════════════════════════════════════════

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Arindirma_Analizi')
    return output.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# PDF Dışa Aktarım — fpdf2 Unicode (Türkçe tam destek)
# ══════════════════════════════════════════════════════════════════════════════

def _get_unicode_font_path():
    """Sistemde bulunan Unicode destekli bir font yolu döndürür."""
    # Windows
    win_fonts = [
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", f)
        for f in ["arial.ttf", "segoeui.ttf", "tahoma.ttf", "calibri.ttf"]
    ]
    # macOS / Linux
    unix_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    
    for path in win_fonts + unix_fonts:
        if os.path.exists(path):
            return path
    return None


def _clean_emojis(text: str) -> str:
    """PDF fontlarının desteklemediği emojileri anlamlı metne çevirir."""
    emoji_map = {
        '✅': '[OK]', '⚠️': '[!]', '❌': '[X]', '🔍': '[?]',
        '📈': '[^]', '📊': '[#]', '💰': '[$]', '🎯': '[*]',
        '🤖': '[AI]', '☪️': '[I]', '🌍': '[W]', '🛡️': '[S]',
        '📂': '[F]', '⚡': '[!]', '🌐': '[W]', '🚀': '[>]',
        '🧩': '[P]', '🔒': '[L]', '♻️': '[R]',
    }
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)
    # Kalan unicode emojileri temizle (BMP dışı karakterler)
    return ''.join(c for c in text if ord(c) < 0x10000 or c in 'ğüşöçıİĞÜŞÖÇ₺')





# ══════════════════════════════════════════════════════════════════════════════
# DOCX Dışa Aktarım
# ══════════════════════════════════════════════════════════════════════════════

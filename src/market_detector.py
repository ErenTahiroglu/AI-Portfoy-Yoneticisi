"""
🧩 Puzzle Parça: Pazar Algılama ve Fon Sınıflandırma
=====================================================
Ticker sembollerinin hangi pazara (US / TR / TEFAS) ait olduğunu tespit eder.
TEFAS fonları için Katılım fon sınıflandırması ve ilk işlem tarihi bilgisi sağlar.

Kullanım:
    from market_detector import detect_market, classify_fund
"""

import logging
import yfinance as yf
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Bilinen BIST hisseleri (hızlı eşleşme) ──────────────────────────────────
_BILINEN_BIST = {
    "THYAO", "ASELS", "GARAN", "AKBNK", "YKBNK", "EREGL", "BIMAS",
    "SAHOL", "KCHOL", "SISE", "TUPRS", "FROTO", "TOASO", "TCELL",
    "PGSUS", "TAVHL", "EKGYO", "KOZAL", "SASA", "TTKOM", "AKSA",
    "ARCLK", "DOHOL", "ENKAI", "HALKB", "ISCTR", "MGROS", "PETKM",
    "SOKM", "VESTL", "VAKBN", "KOZAA", "GUBRF", "KRDMD", "AEFES",
    "CIMSA", "CEMTS", "OTKAR", "BRISA", "AGHOL", "TSKB", "ALARK",
    "ISDMR", "NTHOL", "ISGYO", "KLRHO",
}


def detect_market(ticker: str) -> tuple:
    """
    Ticker'ın pazarını otomatik algılar.
    
    Returns:
        (market, fetcher_ticker, is_tefas)
        Örn: ("US", "AAPL", False) veya ("TR", "TP2", True)
    """
    ticker = ticker.upper().strip()
    
    # 1. Açıkça BIST formatıysa (.IS soneki)
    if ticker.endswith(".IS"):
        return "TR", ticker, False
    
    # 2. Bilinen BIST hisselerini hızlı eşle (Yahoo'ya istek atmadan)
    if ticker in _BILINEN_BIST:
        return "TR", f"{ticker}.IS", False
    
    # 3. Yahoo'da ABD hissesi olarak ara
    try:
        if yf.Ticker(ticker).fast_info.get('lastPrice', 0) > 0:
            return "US", ticker, False
    except Exception:
        pass
    
    # 4. Yahoo'da BIST hissesi olarak ara (.IS ekleyerek)
    try:
        if yf.Ticker(f"{ticker}.IS").fast_info.get('lastPrice', 0) > 0:
            return "TR", f"{ticker}.IS", False
    except Exception:
        pass
    
    # 5. Yukarıda bulunamadıysa ve kısa kodsa → TEFAS fonu
    if len(ticker) <= 5:
        return "TR", ticker, True
    
    # 6. Son çare: ABD olarak kabul et
    return "US", ticker, False


def classify_fund(ticker: str) -> dict:
    """
    TEFAS fonunun Katılım (İslami) fon olup olmadığını tespit eder.
    Fonun ilk işlem tarihini ve aktif süresini hesaplar.
    
    Returns:
        {
            "status": "Katılım Fonu (Uygun)" | "Katılım Fonu Değil",
            "is_etf": True,
            "fund_note": str,
            "fund_start_date": "15.03.2020" | None,
            "fund_age": "4 yıl 11 aydır aktif" | "",
            "purification_ratio": 0,
            "debt_ratio": 0,
            "holdings_str": ""
        }
    """
    # ── Ticker objesini BİR KEZ oluştur ───────────────────────────────
    yf_ticker = yf.Ticker(ticker + ".IS")
    
    # ── Fon adını çek ─────────────────────────────────────────────────
    fund_name = ""
    try:
        fund_info = yf_ticker.info
        fund_name = fund_info.get('longName', '') or fund_info.get('shortName', '') or ''
    except Exception:
        pass
    
    # ── Katılım fon tespiti ───────────────────────────────────────────
    katilim_keywords = ['katılım', 'katilim', 'participation', 'sukuk', 'islamic']
    is_katilim = any(kw in fund_name.lower() for kw in katilim_keywords)
    
    if is_katilim:
        fund_note = f"✅ Katılım Fonu ({fund_name})"
    else:
        fund_note = "⚠️ Bu fon resmi olarak 'Katılım' türünde değildir. Bazı fonlar katılım ilkelerini uygulasa da resmi sınıflandırması farklı olabilir."
        if fund_name:
            fund_note = f"Fon: {fund_name} — " + fund_note
    
    # ── İlk işlem tarihi (aynı ticker objesinden) ─────────────────────
    fund_start_date = None
    fund_age_text = ""
    try:
        hist = yf_ticker.history(period="max")
        if hist is not None and not hist.empty:
            first_date = hist.index[0]
            fund_start_date = first_date.strftime("%d.%m.%Y")
            days_active = (datetime.now() - first_date.to_pydatetime().replace(tzinfo=None)).days
            years = days_active // 365
            months = (days_active % 365) // 30
            if years > 0:
                fund_age_text = f"{years} yıl {months} aydır aktif"
            else:
                fund_age_text = f"{months} aydır aktif"
    except Exception:
        pass
    
    # ── Sonuç ─────────────────────────────────────────────────────────
    return {
        "status": "Katılım Fonu (Uygun)" if is_katilim else "Katılım Fonu Değil",
        "is_etf": True,
        "holdings_str": "",
        "purification_ratio": 0,
        "debt_ratio": 0,
        "fund_note": fund_note,
        "fund_start_date": fund_start_date,
        "fund_age": fund_age_text,
    }

"""
🧩 Puzzle Parça: Veri Kaynakları Altyapısı
============================================
Tüm modüllerin paylaştığı SSL bypass, oturum yönetimi ve
ortak sabitler bu tek dosyada toplanır.

Diğer modüller buradan import eder:
    from src.data.data_sources import HAS_CURL, CURL_SESSION, AV_KEY, req_lib
"""

# ══════════════════════════════════════════════════════════════════════════════
# Merkezi logging konfigürasyonu — tüm proje bu ayarları kullanır
# ══════════════════════════════════════════════════════════════════════════════
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

# ══════════════════════════════════════════════════════════════════════════════
# Python 3.12+ uyumu — distutils kaldırıldı, setuptools gerekli
# ══════════════════════════════════════════════════════════════════════════════
try:
    import setuptools  # noqa: F401 — ensures distutils is available
except ImportError:
    pass

# ══════════════════════════════════════════════════════════════════════════════
# SSL BYPASS — tüm proje için tek noktadan yönetim
# ══════════════════════════════════════════════════════════════════════════════
import os
import ssl
import warnings
import urllib3
from src.api.config import settings

if not settings.SSL_VERIFY:
    os.environ["CURL_CA_BUNDLE"]     = ""
    os.environ["REQUESTS_CA_BUNDLE"] = ""
    os.environ["SSL_CERT_FILE"]      = ""
    os.environ["PYTHONHTTPSVERIFY"]  = "0"
    
    warnings.filterwarnings("ignore")
    urllib3.disable_warnings()
    ssl._create_default_https_context = ssl._create_unverified_context

try:
    import certifi
    certifi.where = lambda: ""
    certifi.old_where = certifi.where
except ImportError:
    pass

# ── curl_cffi oturumu (varsa) ─────────────────────────────────────────────

try:
    from curl_cffi import requests as curl_req
    CURL_SESSION = curl_req.Session(verify=False, impersonate="chrome")
    HAS_CURL = True
except Exception:
    HAS_CURL = False
    CURL_SESSION = None


# ── .env dosyasını yükle ──────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── API Anahtarları ───────────────────────────────────────────────────────
from src.api.config import settings
AV_KEY = settings.ALPHA_VANTAGE_KEY or os.environ.get("ALPHA_VANTAGE_KEY", "")

# ── Sabitler (paylaşılan) ─────────────────────────────────────────────────
ANALIZ_YIL_SAYI     = 5
AYLIK_DONEMLER      = [1, 2, 3, 4, 5, 6, 9, 12, 24, 36, 60, 120]
HAFTALIK_DONEMLER   = [1, 2, 4, 8, 13, 26]
RETRY_SAYISI        = 4
RETRY_BEKLEME       = [5, 15, 30, 60]
FIYAT_TOLERANS      = 2.0     # Kaynaklar arası max fark (%)

# Market-specific defaults
US_VARSAYILAN_ENF   = 3.0     # ABD enflasyonu
TR_VARSAYILAN_ENF   = 50.0    # Türkiye enflasyonu

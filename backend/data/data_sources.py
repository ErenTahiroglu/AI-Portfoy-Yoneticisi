"""
🧩 Puzzle Parça: Veri Kaynakları Altyapısı
============================================
Tüm modüllerin paylaştığı SSL bypass, oturum yönetimi ve
ortak sabitler bu tek dosyada toplanır.

Diğer modüller buradan import eder:
    from backend.data.data_sources import HAS_CURL, CURL_SESSION, AV_KEY, req_lib
"""

# ══════════════════════════════════════════════════════════════════════════════
# Merkezi logging konfigürasyonu — tüm proje bu ayarları kullanır
# ══════════════════════════════════════════════════════════════════════════════
import logging
import time
import os
import ssl
import warnings
import urllib3
import sys

from backend.api.config import settings
from backend.utils.circuit_breaker import CircuitBreaker, FastFailList

if not logging.getLogger().handlers:
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
    req_lib = CURL_SESSION
except Exception:
    HAS_CURL = False
    CURL_SESSION = None
    import requests
    req_lib = requests


# ── .env dosyasını yükle ──────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── API Anahtarları ───────────────────────────────────────────────────────
AV_KEY = settings.ALPHA_VANTAGE_KEY or os.environ.get("ALPHA_VANTAGE_KEY", "")

# ── Sabitler (paylaşılan) ─────────────────────────────────────────────────
ANALIZ_YIL_SAYI     = 5
AYLIK_DONEMLER      = [1, 2, 3, 4, 5, 6, 9, 12, 24, 36, 60, 120]
HAFTALIK_DONEMLER   = [1, 2, 4, 8, 13, 26]
RETRY_SAYISI        = 4

_RETRY_BEKLEME     = [5, 15, 30, 60]
FIYAT_TOLERANS      = 2.0     # Kaynaklar arası max fark (%)

yahoo_cb = CircuitBreaker(name="Yahoo", threshold=3, timeout=60, fallback_factory=lambda: None)
RETRY_BEKLEME       = FastFailList(_RETRY_BEKLEME, cb=yahoo_cb)

# Market-specific defaults
US_VARSAYILAN_ENF   = 3.0     # ABD enflasyonu
TR_VARSAYILAN_ENF   = 50.0    # Türkiye enflasyonu

# ── Monkey-Patch yahooquery.Ticker ─────────────────────────────────────────
try:
    import yahooquery as yq
    
    original_Ticker = yq.Ticker

    class SafeTicker:
        def __init__(self, *args, **kwargs):
            if yahoo_cb.state == "OPEN":
                if time.time() - yahoo_cb.last_failure_time > yahoo_cb.timeout:
                    yahoo_cb.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit Breaker [Yahoo] is OPEN")

            try:
                self._ticker = original_Ticker(*args, **kwargs)
            except Exception as e:
                yahoo_cb.failures += 1
                yahoo_cb.last_failure_time = time.time()
                if yahoo_cb.failures >= yahoo_cb.threshold:
                    yahoo_cb.state = "OPEN"
                raise e
        
        def __getattr__(self, name):
            attr = getattr(self._ticker, name)
            if callable(attr):
                return yahoo_cb(attr)
            return attr


    yq.Ticker = SafeTicker
    # Optional: also monkey-patch it in sys.modules just in case some place uses local import
    sys.modules["yahooquery"].Ticker = SafeTicker
except Exception as e:
    logging.warning(f"yahooquery monkey-patch failed: {e}")

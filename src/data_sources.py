"""
🧩 Puzzle Parça: Veri Kaynakları Altyapısı
============================================
Tüm modüllerin paylaştığı SSL bypass, oturum yönetimi ve
pandas-datareader uyumluluk yamaları bu tek dosyada toplanır.

Diğer modüller buradan import eder:
    from data_sources import HAS_CURL, CURL_SESSION, AV_KEY, req_lib
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
import os, ssl, warnings, urllib3

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
import requests as req_lib

try:
    from curl_cffi import requests as curl_req
    CURL_SESSION = curl_req.Session(verify=False, impersonate="chrome")
    HAS_CURL = True
except Exception:
    HAS_CURL = False
    CURL_SESSION = None

# ── pandas_datareader uyumluluk yaması (pandas 2.x / 3.x) ────────────────
# pandas.util._decorators.deprecate_kwarg imzası pandas'ın yeni sürümlerinde
# değişti, pandas_datareader ile uyumsuz. Her zaman override ediyoruz.
import sys as _sys, types as _types
try:
    import pandas.util._decorators as _pd_dec
except ImportError:
    if "pandas.util._decorators" not in _sys.modules:
        _sys.modules["pandas.util._decorators"] = _types.ModuleType("pandas.util._decorators")
    _pd_dec = _sys.modules["pandas.util._decorators"]

from functools import wraps as _wraps

def _deprecate_kwarg(*args, **kwargs):
    def _dec(func):
        @_wraps(func)
        def _wrapper(*a, **kw):
            return func(*a, **kw)
        return _wrapper
    return _dec

setattr(_pd_dec, "deprecate_kwarg", _deprecate_kwarg)

# ── pandas-datareader SSL bypass (FRED erişimi için) ──────────────────────
try:
    _pdr_session = req_lib.Session()
    _pdr_session.verify = False
    import pandas_datareader.base as _pdr_base
    _orig_pdr_init = _pdr_base._BaseReader.__init__
    def _patched_pdr_init(self, *args, **kwargs):
        _orig_pdr_init(self, *args, **kwargs)
        self.session = _pdr_session
    _pdr_base._BaseReader.__init__ = _patched_pdr_init
except Exception:
    pass

# ── .env dosyasını yükle ──────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── API Anahtarları ───────────────────────────────────────────────────────
AV_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")

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

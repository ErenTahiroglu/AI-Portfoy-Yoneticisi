"""
ABD Portföy Analiz Aracı  –  v5.0
===================================
Yenilikler (v4 → v5):
  • Tüm oturum analizleri biriktirilir; Excel export sadece çıkışta sorulur.
  • Çoklu kaynak: Yahoo Finance + Stooq (pandas-datareader) fiyat doğrulaması.
  • Alpha Vantage opsiyonel üçüncü kaynak (ALPHA_VANTAGE_KEY env değişkeni ile).
  • Kaynaklar arası son fiyat farkı > %2 → ⚠️ uyarı + kaynakları listele.
  • Her analiz için kaynak güvenilirlik özeti yazdırılır.

Gereksinimler:
  python -m pip install yfinance pandas pandas-datareader numpy openpyxl curl_cffi certifi requests
"""

# ══════════════════════════════════════════════════════════════════════════════
# SSL BYPASS  — her şeyden ÖNCE yapılmalı
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

try:
    from curl_cffi import requests as curl_req
    _CURL_SESSION = curl_req.Session(verify=False, impersonate="chrome")
    _HAS_CURL = True
except Exception:
    _HAS_CURL  = False
    _CURL_SESSION = None

# ── pandas_datareader uyumluluk yaması (pandas 3.0 desteği) ────────
import sys as _sys, types as _types
try:
    import pandas.util._decorators as _pd_dec
except ImportError:
    _sys.modules["pandas.util._decorators"] = _types.ModuleType("pandas.util._decorators")
    _pd_dec = _sys.modules["pandas.util._decorators"]

from functools import wraps as _wraps

def _deprecate_kwarg(*args_dk, **kwargs_dk):
    def _dec(func):
        @_wraps(func)
        def _wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return _wrapper
    return _dec

setattr(_pd_dec, "deprecate_kwarg", _deprecate_kwarg)

# ── Normal import'lar ─────────────────────────────────────────────────────────
import time
import requests as req_lib
import yfinance as yf
import pandas as pd
import pandas_datareader as pdr
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ── pandas-datareader için SSL bypass (FRED erişimi) ─────────────────────────
try:
    import requests as _req
    _pdr_session = _req.Session()
    _pdr_session.verify = False
    import pandas_datareader.base as _pdr_base
    _orig_pdr_init = _pdr_base._BaseReader.__init__
    def _patched_pdr_init(self, *args, **kwargs):
        _orig_pdr_init(self, *args, **kwargs)
        self.session = _pdr_session
    _pdr_base._BaseReader.__init__ = _patched_pdr_init
except Exception:
    pass

# ── Sabitler ──────────────────────────────────────────────────────────────────
VARSAYILAN_ENF   = 3.0
ANALIZ_YIL_SAYI  = 5
AYLIK_DONEMLER   = [1, 2, 3, 6, 9]
RETRY_SAYISI     = 4
RETRY_BEKLEME    = [5, 15, 30, 60]
FIYAT_TOLERANS   = 2.0          # Kaynaklar arası max fark (%)

# ── .env dosyasını yükle (varsa; python-dotenv opsiyoneldir) ─────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Alpha Vantage API key — ömür boyu geçerli, yenileme gerekmez.
# Değiştirmek isterseniz .env dosyasına ALPHA_VANTAGE_KEY=... satırı ekleyin.
_AV_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")


# ══════════════════════════════════════════════════════════════════════════════
class HisseAnaliz:
# ══════════════════════════════════════════════════════════════════════════════

    def __init__(self, av_key: str = None):
        self.bugun  = pd.Timestamp.now(tz="UTC")
        self.bu_yil = self.bugun.year
        self.yillar = list(range(self.bu_yil - ANALIZ_YIL_SAYI, self.bu_yil))
        self.av_key = av_key or _AV_KEY

        print(f"\n{'═'*68}")
        print(f"  ABD PORTFÖY ANALİZ ARACI  –  v5.0")
        print(f"{'═'*68}")
        print(f"  Tarih         : {self.bugun.strftime('%d.%m.%Y')}")
        print(f"  Analiz yılları: {self.yillar[0]} – {self.yillar[-1]}")
        print(f"  curl_cffi     : {'✅ aktif (SSL bypass + Chrome impersonate)' if _HAS_CURL else '⚠️ yok, yedek mod'}")
        print(f"  Alpha Vantage : {'✅ ' + self.av_key[:8] + '...' if self.av_key else '⚠️ yok (Parametre / ENV boş)'}")
        print(f"{'═'*68}\n")

        self.yillik_enf: Dict[int, float] = self._yillik_enflasyon_al()
        self.aylik_cpi:  pd.DataFrame      = self._aylik_cpi_al()

    # ─────────────────────────────────────────────────────────────────────────
    # ENFLASYON  (FRED birincil, BLS backup)
    # ─────────────────────────────────────────────────────────────────────────

    def _yillik_enflasyon_al(self) -> Dict[int, float]:
        print("📊 Yıllık enflasyon çekiliyor (FRED – CPIAUCSL)...")
        try:
            cpi = pdr.get_data_fred(
                "CPIAUCSL",
                start=datetime(self.yillar[0] - 1, 1, 1),
                end  =datetime(self.bu_yil, 12, 31),
            )
            sonuc: Dict[int, float] = {}
            for yil in self.yillar:
                try:
                    once = cpi[cpi.index.year == yil - 1]["CPIAUCSL"].iloc[-1]
                    bu   = cpi[cpi.index.year == yil    ]["CPIAUCSL"].iloc[-1]
                    sonuc[yil] = ((bu - once) / once) * 100
                except Exception:
                    sonuc[yil] = VARSAYILAN_ENF
            print("✅ Yıllık enflasyon alındı (FRED).\n")
            return sonuc
        except Exception as e:
            print(f"⚠️  FRED erişilemedi, tahmini değer kullanılacak: {e}\n")
            return {y: VARSAYILAN_ENF for y in self.yillar}

    def _aylik_cpi_al(self) -> pd.DataFrame:
        print("📊 Aylık CPI çekiliyor (FRED)...")
        try:
            bugun_n = self.bugun.tz_convert(None)
            cpi = pdr.get_data_fred(
                "CPIAUCSL",
                start=(bugun_n - pd.DateOffset(days=730)).to_pydatetime(),
                end  = bugun_n.to_pydatetime(),
            )
            print("✅ Aylık CPI alındı.\n")
            return cpi
        except Exception as e:
            print(f"⚠️  Aylık CPI alınamadı: {e}\n")
            return pd.DataFrame()

    def _donem_enflasyonu(self, bas: pd.Timestamp, bit: pd.Timestamp) -> float:
        try:
            if self.aylik_cpi.empty:
                raise ValueError
            def _n(ts):
                return ts.tz_convert(None) if ts.tzinfo else ts
            cb = self.aylik_cpi[self.aylik_cpi.index <= _n(bas)]["CPIAUCSL"].iloc[-1]
            ce = self.aylik_cpi[self.aylik_cpi.index <= _n(bit)]["CPIAUCSL"].iloc[-1]
            return ((ce - cb) / cb) * 100
        except Exception:
            return (VARSAYILAN_ENF / 365) * (bit - bas).days

    # ─────────────────────────────────────────────────────────────────────────
    # YARDIMCI
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _utc(df) -> pd.DataFrame:
        if isinstance(df, pd.Series):
            df = df.to_frame()
        if df.index.tzinfo is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")
        return df

    # ─────────────────────────────────────────────────────────────────────────
    # KAYNAK 1: Yahoo Finance
    # ─────────────────────────────────────────────────────────────────────────

    def _yahoo_cek(self, sembol: str, baslangic: datetime, bitis: datetime
                   ) -> Optional[pd.DataFrame]:
        indir_kwargs = dict(
            start=baslangic, end=bitis,
            auto_adjust=True, progress=False, timeout=30,
        )
        if _HAS_CURL:
            indir_kwargs["session"] = _CURL_SESSION
        ham = yf.download(sembol, **indir_kwargs)
        if ham is None or ham.empty:
            return None
        if isinstance(ham.columns, pd.MultiIndex):
            ham.columns = ham.columns.get_level_values(0)
        return self._utc(ham)

    # ─────────────────────────────────────────────────────────────────────────
    # KAYNAK 2: Stooq (pandas-datareader)
    # ─────────────────────────────────────────────────────────────────────────

    def _stooq_cek(self, sembol: str, baslangic: datetime, bitis: datetime
                   ) -> Optional[pd.DataFrame]:
        """
        Stooq, ABD hisselerini '<SEMBOL>.US' formatında kabul eder.
        Bazen sembol Stooq'ta bulunmaz; o zaman None döner.
        """
        try:
            stooq_sembol = sembol if "." in sembol else f"{sembol}.US"
            df = pdr.get_data_stooq(stooq_sembol, start=baslangic, end=bitis)
            if df is None or df.empty:
                return None
            df = df.sort_index()        # Stooq ters sıralı gelir
            # Stooq sütunları: Open, High, Low, Close, Volume
            return self._utc(df)
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # KAYNAK 3: Alpha Vantage (opsiyonel, API key gerekir)
    # ─────────────────────────────────────────────────────────────────────────

    def _alphavantage_cek(self, sembol: str) -> Optional[pd.DataFrame]:
        if not self.av_key:
            return None
        try:
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=TIME_SERIES_DAILY_ADJUSTED"
                f"&symbol={sembol}&outputsize=full&apikey={self.av_key}"
            )
            r = req_lib.get(url, timeout=30, verify=False)
            data = r.json()
            ts = data.get("Time Series (Daily)", {})
            if not ts:
                return None
            df = pd.DataFrame.from_dict(ts, orient="index")
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns={"5. adjusted close": "Close"})
            df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
            df = df[["Close"]].sort_index()
            return self._utc(df)
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # ÇOK KAYNAKLI VERİ ÇEKME + DOĞRULAMA
    # ─────────────────────────────────────────────────────────────────────────

    def _veri_cek(self, sembol: str) -> Optional[Dict]:
        print(f"  📥 {sembol} → veri çekiliyor...")
        baslangic = datetime(self.yillar[0] - 1, 12, 1)
        bitis     = self.bugun.tz_convert(None).to_pydatetime()

        # ── Fiyat: Yahoo Finance (birincil, retry'lı) ─────────────────────────
        fiyatlar_yf = None
        for deneme in range(RETRY_SAYISI):
            try:
                fiyatlar_yf = self._yahoo_cek(sembol, baslangic, bitis)
                if fiyatlar_yf is not None:
                    print(f"     ✅ Yahoo Finance: {len(fiyatlar_yf)} gün")
                    break
            except Exception as e:
                bekleme = RETRY_BEKLEME[min(deneme, len(RETRY_BEKLEME) - 1)]
                print(f"     ⏳ Yahoo deneme {deneme+1}/{RETRY_SAYISI}: {str(e)[:80]}")
                time.sleep(bekleme)

        # ── Fiyat: Stooq (ikincil) ────────────────────────────────────────────
        fiyatlar_stooq = None
        try:
            fiyatlar_stooq = self._stooq_cek(sembol, baslangic, bitis)
            if fiyatlar_stooq is not None:
                print(f"     ✅ Stooq        : {len(fiyatlar_stooq)} gün")
            else:
                print(f"     ⚠️  Stooq: veri yok")
        except Exception as e:
            print(f"     ⚠️  Stooq hata: {e}")

        # ── Fiyat: Alpha Vantage (üçüncül, opsiyonel) ─────────────────────────
        fiyatlar_av = None
        if self.av_key:
            try:
                fiyatlar_av = self._alphavantage_cek(sembol)
                if fiyatlar_av is not None:
                    print(f"     ✅ Alpha Vantage: {len(fiyatlar_av)} gün")
                else:
                    print(f"     ⚠️  Alpha Vantage: veri yok")
            except Exception as e:
                print(f"     ⚠️  Alpha Vantage hata: {e}")

        # ── En az bir kaynak lazım ────────────────────────────────────────────
        if fiyatlar_yf is None and fiyatlar_stooq is None and fiyatlar_av is None:
            print(f"  ❌ {sembol}: hiçbir kaynaktan veri alınamadı.")
            return None

        # ── Çapraz doğrulama (son fiyat karşılaştırma) ────────────────────────
        self._capraz_dogrula(sembol, fiyatlar_yf, fiyatlar_stooq, fiyatlar_av)

        # ── Birincil fiyat: mevcut kaynakların ilki ───────────────────────────
        if fiyatlar_yf is not None:
            fiyatlar = fiyatlar_yf
        elif fiyatlar_stooq is not None:
            fiyatlar = fiyatlar_stooq
        else:
            fiyatlar = fiyatlar_av

        # ── Temettü (Yahoo'dan) ───────────────────────────────────────────────
        temettular = pd.Series(dtype=float)
        try:
            ticker_kwargs = {"session": _CURL_SESSION} if _HAS_CURL else {}
            ticker = yf.Ticker(sembol, **ticker_kwargs)
            tem    = ticker.dividends
            if tem is not None and not tem.empty:
                temettular = self._utc(tem.to_frame()).iloc[:, 0]
        except Exception:
            pass

        # ── Şirket adı ────────────────────────────────────────────────────────
        ad = sembol
        try:
            ad = ticker.fast_info.company_name or sembol
        except Exception:
            pass

        return {"fiyatlar": fiyatlar, "temettular": temettular, "ad": ad}

    def _capraz_dogrula(self, sembol: str,
                        yf_df:    Optional[pd.DataFrame],
                        stooq_df: Optional[pd.DataFrame],
                        av_df:    Optional[pd.DataFrame]) -> None:
        """
        Mevcut kaynaklardan son kapanış fiyatını alır, aralarındaki farkı kontrol eder.
        Fark FIYAT_TOLERANS (%) üzerindeyse kullanıcıyı uyarır.
        """
        fiyatlar_dict: Dict[str, float] = {}
        for isim, df in [("Yahoo", yf_df), ("Stooq", stooq_df), ("AlphaVantage", av_df)]:
            if df is not None and not df.empty and "Close" in df.columns:
                try:
                    fiyatlar_dict[isim] = float(df["Close"].dropna().iloc[-1])
                except Exception:
                    pass

        if len(fiyatlar_dict) < 2:
            return          # Tek kaynak varsa kıyaslama yapılamaz

        degerler = list(fiyatlar_dict.values())
        maks     = max(degerler)
        min_     = min(degerler)
        fark_pct = abs(maks - min_) / min_ * 100

        satir = "  🔍 Fiyat çapraz doğrulama: " + \
                " | ".join(f"{k}={v:.2f}$" for k, v in fiyatlar_dict.items())
        print(satir)

        if fark_pct > FIYAT_TOLERANS:
            print(f"  ⚠️  DİKKAT: Kaynaklar arası fiyat farkı = %{fark_pct:.2f} "
                  f"(eşik: %{FIYAT_TOLERANS}). Verileri manuel doğrulayın!")
        else:
            print(f"  ✅ Kaynaklar tutarlı (max fark: %{fark_pct:.2f})")

    # ─────────────────────────────────────────────────────────────────────────
    # HESAPLAMALAR
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _ydf(df: pd.DataFrame, yil: int) -> pd.DataFrame:
        return df[df.index.year == yil]

    def _yillik_getiri(self, fiyatlar: pd.DataFrame, yil: int) -> Optional[float]:
        try:
            once = self._ydf(fiyatlar, yil - 1)
            bu   = self._ydf(fiyatlar, yil)
            if once.empty or bu.empty:
                return None
            return ((bu["Close"].iloc[-1] - once["Close"].iloc[-1])
                    / once["Close"].iloc[-1]) * 100
        except Exception:
            return None

    def _toplam_getiri(self, fiyatlar: pd.DataFrame,
                       bas_yil: int, bit_yil: int) -> Optional[float]:
        try:
            once = self._ydf(fiyatlar, bas_yil - 1)
            bit  = self._ydf(fiyatlar, bit_yil)
            if once.empty or bit.empty:
                return None
            return ((bit["Close"].iloc[-1] - once["Close"].iloc[-1])
                    / once["Close"].iloc[-1]) * 100
        except Exception:
            return None

    def _temettü_verimi(self, temettular: pd.Series,
                        fiyatlar: pd.DataFrame, yil: int) -> float:
        try:
            yt = temettular[temettular.index.year == yil]
            if yt.empty:
                return 0.0
            yf_ = self._ydf(fiyatlar, yil)
            if yf_.empty:
                return 0.0
            return (yt.sum() / yf_["Close"].iloc[0]) * 100
        except Exception:
            return 0.0

    def _donemsel_getiri(self, fiyatlar: pd.DataFrame, ay: int
                         ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        try:
            hedef   = self.bugun - pd.DateOffset(months=ay)
            sonraki = fiyatlar[fiyatlar.index >= hedef]
            if sonraki.empty:
                return None, None, None
            bas = sonraki.iloc[0]
            bit = fiyatlar.iloc[-1]
            g   = ((bit["Close"] - bas["Close"]) / bas["Close"]) * 100
            enf = self._donem_enflasyonu(bas.name, bit.name)
            return g, g - enf, enf
        except Exception:
            return None, None, None

    # ─────────────────────────────────────────────────────────────────────────
    # ANA ANALİZ
    # ─────────────────────────────────────────────────────────────────────────

    def analiz_et(self, sembol: str) -> Optional[Dict]:
        print(f"\n{'─'*68}")
        print(f"🔍  {sembol}")
        print(f"{'─'*68}")

        veri = self._veri_cek(sembol)
        if not veri:
            return None

        fiyatlar   = veri["fiyatlar"]
        temettular = veri["temettular"]
        sonuc = {
            "sembol": sembol, "ad": veri["ad"],
            "yg": {}, "yr": {}, "yt": {},
            "s5": None, "s3": None, "ay": {},
        }

        print(f"\n  {'Yıl':<6} {'Getiri':>8} {'Reel':>8} {'Enflasyon':>10} {'Temettü':>8}")
        print(f"  {'─'*46}")
        for yil in self.yillar:
            g = self._yillik_getiri(fiyatlar, yil)
            if g is None:
                continue
            enf = self.yillik_enf.get(yil, VARSAYILAN_ENF)
            r   = g - enf
            t   = self._temettü_verimi(temettular, fiyatlar, yil)
            sonuc["yg"][yil] = g
            sonuc["yr"][yil] = r
            sonuc["yt"][yil] = t
            print(f"  {yil:<6} {g:>+7.2f}%  {r:>+7.2f}%  {enf:>+8.2f}%  {t:>7.2f}%")

        s5 = self._toplam_getiri(fiyatlar, self.yillar[0],  self.yillar[-1])
        s3 = self._toplam_getiri(fiyatlar, self.yillar[-3], self.yillar[-1])
        sonuc["s5"] = s5
        sonuc["s3"] = s3
        print(f"\n  📊 Toplam getiri:")
        if s5 is not None:
            print(f"     Son 5 yıl ({self.yillar[0]}–{self.yillar[-1]}): {s5:>+8.2f}%")
        if s3 is not None:
            print(f"     Son 3 yıl ({self.yillar[-3]}–{self.yillar[-1]}): {s3:>+8.2f}%")

        print(f"\n  {'Dönem':<9} {'Getiri':>8} {'Reel':>8} {'Dönem Enf.':>11}")
        print(f"  {'─'*40}")
        for ay in AYLIK_DONEMLER:
            g, r, enf = self._donemsel_getiri(fiyatlar, ay)
            if g is None:
                continue
            sonuc["ay"][ay] = {"g": g, "r": r, "enf": enf}
            print(f"  Son {ay:>2} ay   {g:>+7.2f}%  {r:>+7.2f}%  {enf:>+9.2f}%")

        return sonuc


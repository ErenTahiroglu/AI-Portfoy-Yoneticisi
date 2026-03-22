"""
🧩 Puzzle Parça: Temel Analizör Sınıfı
========================================
bist_analyzer.py ve us_analyzer.py arasında paylaşılan
hesaplama mantığını DRY (Don't Repeat Yourself) prensibiyle
tek bir yerde toplar.

Ortak özellikler:
  • Yıllık / dönemsel / haftalık getiri hesaplama
  • Temettü verimi
  • Günlük istatistik (ort, std, min, max)
  • Sharpe Ratio, Max Drawdown
  • DataFrame timezone yardımcıları
  • Enflasyon cache (modül seviyesinde)
"""

import logging
import time
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# Sonuç veri yapıları (TypedDict yerine dataclass — daha temiz)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SonFiyat:
    fiyat: float = 0.0
    degisim: float = 0.0
    tarih: str = "?"
    yuksek: float = 0.0
    dusuk: float = 0.0



@dataclass
class GunlukIstatistik:
    ort: float = 0.0
    std: float = 0.0
    min: float = 0.0
    max: float = 0.0
    pozitif: int = 0
    negatif: int = 0
    toplam: int = 0

@dataclass
class RiskMetrikleri:
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None      # %
    max_drawdown_tarih: Optional[str] = None

# ══════════════════════════════════════════════════════════════════════════════
# Modül seviyesinde enflasyon cache
# ══════════════════════════════════════════════════════════════════════════════

_ENF_CACHE: Dict[str, Dict] = {}  # {"TURCPIALLMINMEI": {"ts": ..., "data": ...}}
_ENF_CACHE_TTL = 3600  # 1 saat


def get_cached_cpi(fred_seri: str, start: datetime, end: datetime) -> Optional[pd.DataFrame]:
    """FRED CPI verisini cache'den döndürür veya yeni çeker."""
    from io import StringIO
    
    cache_key = fred_seri
    now = time.time()
    
    if cache_key in _ENF_CACHE:
        cached = _ENF_CACHE[cache_key]
        if now - cached["ts"] < _ENF_CACHE_TTL:
            logger.info(f"📊 {fred_seri} cache'den alındı.")
            return cached["data"]
    
    try:
        logger.info(f"📊 {fred_seri} FRED'den çekiliyor (doğrudan CSV)...")
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={fred_seri}"
        
        import urllib.request
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            csv_text = response.read().decode('utf-8')
            
        csv_data = StringIO(csv_text)
        cpi = pd.read_csv(csv_data, index_col=0, parse_dates=True, na_values='.')
        
        # Beklenmeyen na değerleri temizle ve datetime indeksle
        cpi = cpi.dropna()
        cpi.columns = [fred_seri]
        
        # Filtrele ve tz-naive datetime kullanışından koru
        cpi.index = pd.to_datetime(cpi.index).tz_localize(None)
        start_naive = pd.to_datetime(start).tz_localize(None)
        end_naive = pd.to_datetime(end).tz_localize(None)
        cpi = cpi.loc[start_naive:end_naive]
        
        _ENF_CACHE[cache_key] = {"ts": now, "data": cpi}
        logger.info(f"✅ {fred_seri} alındı ve cache'lendi.")
        return cpi
    except Exception as e:
        logger.warning(f"⚠️  {fred_seri} FRED erişilemedi: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
class BaseAnalyzer:
# ══════════════════════════════════════════════════════════════════════════════
    """Her iki analizörün (US / TR) miras aldığı temel sınıf."""

    # ─────────────────────────────────────────────────────────────────────────
    # YARDIMCI — UTC dönüşüm
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _utc(df: "pd.DataFrame | pd.Series") -> pd.DataFrame:
        if isinstance(df, pd.Series):
            df = df.to_frame()
        idx = pd.DatetimeIndex(df.index)
        if idx.tzinfo is None:
            df.index = idx.tz_localize("UTC")
        else:
            df.index = idx.tz_convert("UTC")
        return df

    # ─────────────────────────────────────────────────────────────────────────
    # YILLIK FİLTRE
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _ydf(df: pd.DataFrame, yil: int) -> pd.DataFrame:
        return df.loc[pd.DatetimeIndex(df.index).year == yil]

    # ─────────────────────────────────────────────────────────────────────────
    # GETİRİ HESAPLAMALARI
    # ─────────────────────────────────────────────────────────────────────────

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

    def _temettu_verimi(self, temettular: pd.Series,
                        fiyatlar: pd.DataFrame, yil: int) -> float:
        try:
            yt = temettular.loc[pd.DatetimeIndex(temettular.index).year == yil]
            if yt.empty:
                return 0.0
            yf_ = self._ydf(fiyatlar, yil)
            if yf_.empty:
                return 0.0
            return (yt.sum() / yf_["Close"].iloc[0]) * 100
        except Exception:
            return 0.0

    def _donemsel_getiri(self, fiyatlar: pd.DataFrame, ay: int,
                          bugun: pd.Timestamp,
                          donem_enflasyonu_fn) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        try:
            hedef   = bugun - pd.DateOffset(months=ay)
            sonraki = fiyatlar[fiyatlar.index >= hedef]
            if sonraki.empty:
                return None, None, None
            bas = sonraki.iloc[0]
            bit = fiyatlar.iloc[-1]
            g   = ((bit["Close"] - bas["Close"]) / bas["Close"]) * 100
            enf = donem_enflasyonu_fn(bas.name, bit.name)
            return g, g - enf, enf
        except Exception:
            return None, None, None

    def _haftalik_getiri(self, haftalik: pd.DataFrame, hafta: int,
                          bugun: pd.Timestamp,
                          donem_enflasyonu_fn) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        try:
            hedef   = bugun - pd.DateOffset(weeks=hafta)
            sonraki = haftalik[haftalik.index >= hedef]
            if sonraki.empty:
                return None, None, None
            bas = sonraki.iloc[0]
            bit = haftalik.iloc[-1]
            g   = ((bit["Close"] - bas["Close"]) / bas["Close"]) * 100
            enf = donem_enflasyonu_fn(bas.name, bit.name)
            return g, g - enf, enf
        except Exception:
            return None, None, None

    # ─────────────────────────────────────────────────────────────────────────
    # GÜNLÜK İSTATİSTİK
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _gunluk_istatistik(fiyatlar: pd.DataFrame, gun: int = 30) -> Optional[GunlukIstatistik]:
        try:
            son = fiyatlar.tail(gun + 1)
            if len(son) < 2:
                return None
            gunluk_getiri = son["Close"].pct_change().dropna() * 100
            return GunlukIstatistik(
                ort    = float(gunluk_getiri.mean()),
                std    = float(gunluk_getiri.std()),
                min    = float(gunluk_getiri.min()),
                max    = float(gunluk_getiri.max()),
                pozitif= int((gunluk_getiri > 0).sum()),
                negatif= int((gunluk_getiri < 0).sum()),
                toplam = len(gunluk_getiri),
            )
        except Exception:
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # SON FİYAT BİLGİSİ
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _son_fiyat_bilgisi(fiyatlar: pd.DataFrame) -> SonFiyat:
        try:
            son = fiyatlar.iloc[-1]
            onceki = fiyatlar.iloc[-2] if len(fiyatlar) > 1 else son
            degisim = ((son["Close"] - onceki["Close"]) / onceki["Close"]) * 100
            return SonFiyat(
                fiyat   = float(son["Close"]),
                degisim = float(degisim),
                tarih   = son.name.strftime("%d.%m.%Y"),
                yuksek  = float(son["High"]) if "High" in son.index else float(son["Close"]),
                dusuk   = float(son["Low"])  if "Low"  in son.index else float(son["Close"]),
            )
        except Exception:
            return SonFiyat()

    # ─────────────────────────────────────────────────────────────────────────
    # RİSK METRİKLERİ (Sharpe Ratio + Max Drawdown) — YENİ
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _risk_metrikleri(fiyatlar: pd.DataFrame, risksiz_faiz: float = 0.05) -> RiskMetrikleri:
        """Sharpe Ratio ve Maximum Drawdown hesaplar."""
        try:
            close = fiyatlar["Close"].dropna()
            if len(close) < 30:
                return RiskMetrikleri()
            
            gunluk = close.pct_change().dropna()
            
            # Sharpe Ratio (yıllıklandırılmış)
            yillik_getiri = gunluk.mean() * 252
            yillik_vol    = gunluk.std() * np.sqrt(252)
            sharpe = (yillik_getiri - risksiz_faiz) / yillik_vol if yillik_vol > 0 else None
            
            # Max Drawdown
            cummax = close.cummax()
            drawdown = (close - cummax) / cummax
            max_dd = float(drawdown.min() * 100)
            max_dd_idx = drawdown.idxmin()
            max_dd_tarih = max_dd_idx.strftime("%d.%m.%Y") if hasattr(max_dd_idx, "strftime") else "?"
            
            return RiskMetrikleri(
                sharpe_ratio     = round(float(sharpe), 3) if sharpe is not None else None,
                max_drawdown     = round(max_dd, 2),
                max_drawdown_tarih = max_dd_tarih,
            )
        except Exception:
            return RiskMetrikleri()

    # ─────────────────────────────────────────────────────────────────────────
    # ÇAPRAZ DOĞRULAMA
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _capraz_dogrula(sembol: str,
                        kaynaklar: Dict[str, Optional[pd.DataFrame]],
                        tolerans: float,
                        para_birimi: str = "₺") -> None:
        fiyatlar_dict: Dict[str, float] = {}
        for isim, df in kaynaklar.items():
            if df is not None and not df.empty and "Close" in df.columns:
                try:
                    fiyatlar_dict[isim] = float(df["Close"].dropna().iloc[-1])
                except Exception:
                    pass

        if len(fiyatlar_dict) < 2:
            return

        degerler = list(fiyatlar_dict.values())
        maks     = max(degerler)
        min_     = min(degerler)
        fark_pct = abs(maks - min_) / min_ * 100

        satir = "  🔍 Fiyat çapraz doğrulama: " + \
                " | ".join(f"{k}={v:.2f}{para_birimi}" for k, v in fiyatlar_dict.items())
        logger.info(satir)

        if fark_pct > tolerans:
            logger.warning(f"  ⚠️  DİKKAT: Kaynaklar arası fiyat farkı = %{fark_pct:.2f} "
                           f"(eşik: %{tolerans})")
        else:
            logger.info(f"  ✅ Kaynaklar tutarlı (max fark: %{fark_pct:.2f})")

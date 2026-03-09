"""
🧩 Puzzle Parça: BIST Portföy Analizörü  –  v2.0
====================================================
Borsa İstanbul hisse senetleri ve TEFAS fonlarının finansal
performansını nominal ve reel (enflasyondan arındırılmış) bazda analiz eder.

v2.0 Yenilikler:
  • BaseAnalyzer kalıtımı (DRY — ortak hesaplamalar tek yerde)
  • Playwright TEFAS scraper (WAF bypass)
  • Paralel veri çekme (Yahoo + Stooq + AV eşzamanlı)
  • FRED enflasyon tek çağrı + modül cache
  • Sharpe Ratio & Max Drawdown metrikleri
  • logging modülü (print yerine)
  • Dataclass sonuç formatı
"""

# ══════════════════════════════════════════════════════════════════════════════
# İmport'lar
# ══════════════════════════════════════════════════════════════════════════════
import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

import yfinance as yf
# Render.com/Vercel gibi ortamlarda yazma izni sorunu olmaması için cache'i /tmp/ altına alıyoruz
try:
    yf.set_tz_cache_location("/tmp/py-yfinance")
except Exception:
    pass
import pandas as pd
from io import StringIO
from datetime import datetime
from typing import Dict, Optional

from src.data.data_sources import (
    HAS_CURL, CURL_SESSION, AV_KEY, req_lib,
    TR_VARSAYILAN_ENF as VARSAYILAN_ENF,
    ANALIZ_YIL_SAYI, AYLIK_DONEMLER, HAFTALIK_DONEMLER,
    RETRY_SAYISI, RETRY_BEKLEME, FIYAT_TOLERANS
)
from .base_analyzer import BaseAnalyzer, get_cached_cpi, RiskMetrikleri
from src.data.tefas_scraper import get_tefas_data_sync

logger = logging.getLogger(__name__)

# Yahoo Finance'te BIST hisseleri .IS soneki ile aranır
BIST_SONEK = ".IS"

# Popüler BIST sembolleri (referans)
POPULER_BIST = {
    "THYAO": "Türk Hava Yolları",
    "ASELS": "ASELSAN",
    "GARAN": "Garanti BBVA",
    "AKBNK": "Akbank",
    "YKBNK": "Yapı Kredi",
    "EREGL": "Ereğli Demir Çelik",
    "BIMAS": "BİM Mağazalar",
    "SAHOL": "Sabancı Holding",
    "KCHOL": "Koç Holding",
    "SISE":  "Şişecam",
    "TUPRS": "Tüpraş",
    "FROTO": "Ford Otosan",
    "TOASO": "Tofaş",
    "TCELL": "Turkcell",
    "PGSUS": "Pegasus",
    "TAVHL": "TAV Havalimanları",
    "EKGYO": "Emlak Konut GYO",
    "KOZAL": "Koza Altın",
    "SASA":  "SASA Polyester",
    "TTKOM": "Türk Telekom",
}


# ══════════════════════════════════════════════════════════════════════════════
class HisseAnaliz(BaseAnalyzer):
# ══════════════════════════════════════════════════════════════════════════════

    def __init__(self, stop_event: Optional[threading.Event] = None):
        self._stop_event = stop_event
        self.bugun  = pd.Timestamp.now(tz="UTC")
        self.bu_yil = self.bugun.year
        self.yillar = list(range(self.bu_yil - ANALIZ_YIL_SAYI, self.bu_yil))

        logger.info(f"\n{'═'*68}")
        logger.info(f"  BIST PORTFÖY ANALİZ ARACI  –  v2.0")
        logger.info(f"{'═'*68}")
        logger.info(f"  Tarih         : {self.bugun.strftime('%d.%m.%Y')}")
        logger.info(f"  Analiz yılları: {self.yillar[0]} – {self.yillar[-1]}")
        logger.info(f"  curl_cffi     : {'✅ aktif' if HAS_CURL else '⚠️ yok, yedek mod'}")
        logger.info(f"  Alpha Vantage : {'✅ ' + AV_KEY[:8] + '...' if AV_KEY else '⚠️ yok'}")
        logger.info(f"{'═'*68}\n")

        # ── Enflasyon: TEK çağrı, iki amaç ────────────────────────────────────
        self._enflasyon_al()

    # ─────────────────────────────────────────────────────────────────────────
    # SEMBOL NORMALIZASYONU
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _bist_sembol(sembol: str) -> str:
        sembol = sembol.upper().strip()
        if sembol.endswith(".IS"):
            return sembol
        if "." in sembol:
            return sembol
        return sembol + BIST_SONEK

    @staticmethod
    def _temiz_sembol(sembol: str) -> str:
        return sembol.replace(".IS", "").replace(".is", "")

    @staticmethod
    def _fon_kodu_mu(sembol: str) -> bool:
        """Kısa alfanümerik kodlar → TEFAS fon kodu (örn: AKB, TP2, ZP8). 
        BIST hisseler minimum 4 karakter (AKSA, THYAO vb.)."""
        s = sembol.strip().upper().replace(".IS", "")
        if len(s) <= 3 and s[0].isalpha():
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # ENFLASYON — TEK FRED ÇAĞRISI, İKİ SONUÇ
    # ─────────────────────────────────────────────────────────────────────────

    def _enflasyon_al(self):
        """FRED'den Türkiye CPI verisini TEK bir çağrıda alır.
        Hem yıllık enflasyon dict'ini hem aylık CPI DataFrame'ini tek seferde üretir."""
        cpi = get_cached_cpi(
            "TURCPIALLMINMEI",
            start=datetime(self.yillar[0] - 1, 1, 1),
            end=datetime(self.bu_yil, 12, 31),
        )
        
        if cpi is not None and not cpi.empty:
            # Yıllık enflasyon hesapla
            sonuc: Dict[int, float] = {}
            cpi_idx = pd.DatetimeIndex(cpi.index)
            cpi_col = cpi["TURCPIALLMINMEI"]
            for yil in self.yillar:
                try:
                    once = float(cpi_col[cpi_idx.year == yil - 1].iloc[-1])
                    bu   = float(cpi_col[cpi_idx.year == yil    ].iloc[-1])
                    sonuc[yil] = ((bu - once) / once) * 100
                except Exception:
                    sonuc[yil] = VARSAYILAN_ENF
            self.yillik_enf = sonuc
            
            # Aylık CPI (son 2 yıl)
            bugun_n = self.bugun.tz_convert(None)
            cutoff = (bugun_n - pd.DateOffset(days=730)).to_pydatetime()
            self.aylik_cpi = cpi[cpi.index >= cutoff]
            logger.info("✅ Enflasyon verisi alındı (tek FRED çağrısı).\n")
        else:
            logger.warning(f"⚠️  FRED erişilemedi, tahmini değer kullanılacak ({VARSAYILAN_ENF}%).\n")
            self.yillik_enf = {y: VARSAYILAN_ENF for y in self.yillar}
            self.aylik_cpi = pd.DataFrame()

    def _donem_enflasyonu(self, bas: pd.Timestamp, bit: pd.Timestamp) -> float:
        try:
            if self.aylik_cpi.empty:
                raise ValueError
            def _n(ts):
                return ts.tz_convert(None) if ts.tzinfo else ts
            col = self.aylik_cpi["TURCPIALLMINMEI"]
            cb = float(col[self.aylik_cpi.index <= _n(bas)].iloc[-1])
            ce = float(col[self.aylik_cpi.index <= _n(bit)].iloc[-1])
            return ((ce - cb) / cb) * 100
        except Exception:
            return (VARSAYILAN_ENF / 365) * (bit - bas).days

    # ─────────────────────────────────────────────────────────────────────────
    # VERİ KAYNAKLARI
    # ─────────────────────────────────────────────────────────────────────────

    def _yahoo_cek(self, sembol: str, baslangic: datetime, bitis: datetime
                   ) -> Optional[pd.DataFrame]:
        yf_sembol = self._bist_sembol(sembol)
        session = CURL_SESSION if (HAS_CURL and CURL_SESSION is not None) else None
        ham = yf.download(
            yf_sembol,
            start=baslangic, end=bitis,
            auto_adjust=True, progress=False, timeout=30,
            session=session,
        )
        if ham is None or ham.empty:
            return None
        if isinstance(ham.columns, pd.MultiIndex):
            ham.columns = ham.columns.get_level_values(0)
        return self._utc(ham)

    def _stooq_cek(self, sembol: str, baslangic: datetime, bitis: datetime
                   ) -> Optional[pd.DataFrame]:
        """Stooq'tan doğrudan CSV API ile veri çeker (pandas_datareader kullanmaz)."""
        try:
            temiz = self._temiz_sembol(sembol)
            s_start = pd.Timestamp(baslangic).strftime('%Y%m%d')
            s_end   = pd.Timestamp(bitis).strftime('%Y%m%d')
            url = (
                f"https://stooq.pl/q/d/l/"
                f"?s={temiz}.tr&d1={s_start}&d2={s_end}&i=d"
            )
            r = req_lib.get(url, timeout=20, verify=False)
            if r.status_code != 200 or len(r.text) < 50:
                return None
            df = pd.read_csv(StringIO(r.text), index_col=0, parse_dates=True)
            if df.empty or 'Close' not in df.columns:
                return None
            return self._utc(df.sort_index())
        except Exception:
            return None

    def _alphavantage_cek(self, sembol: str) -> Optional[pd.DataFrame]:
        if not AV_KEY:
            return None
        try:
            temiz = self._temiz_sembol(sembol)
            av_sembol = f"{temiz}.IST"
            url = (
                f"https://www.alphavantage.co/query"
                f"?function=TIME_SERIES_DAILY_ADJUSTED"
                f"&symbol={av_sembol}&outputsize=full&apikey={AV_KEY}"
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

    def _tefas_cek(self, fon_kodu: str, baslangic: datetime, bitis: datetime
                   ) -> Optional[pd.DataFrame]:
        """TEFAS → Playwright (Sanal Tarayıcı) ile F5 WAF bypass."""
        fon_kodu = fon_kodu.strip().upper()
        logger.info(f"     ⏳ TEFAS WAF Aşılıyor (Arkaplan Tarayıcısı)...")
        try:
            df = get_tefas_data_sync(fon_kodu, baslangic.date(), bitis.date())
            if df is not None and not df.empty:
                df.index = pd.DatetimeIndex(df.index).tz_localize("UTC")
                logger.info(f"     ✅ TEFAS         : {len(df)} gün ({fon_kodu})")
                return df
            else:
                logger.warning(f"     ⚠️  TEFAS: {fon_kodu} için veri bulunamadı.")
                return None
        except Exception as e:
            logger.error(f"     ⚠️  TEFAS hata: {str(e)[:80]}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # ÇOK KAYNAKLI VERİ ÇEKME + PARALEL + DOĞRULAMA
    # ─────────────────────────────────────────────────────────────────────────

    def _veri_cek(self, sembol: str, is_tefas: bool = False) -> Optional[Dict]:
        temiz     = self._temiz_sembol(sembol)
        fon_mu    = is_tefas or self._fon_kodu_mu(temiz)
        baslangic = datetime(self.yillar[0] - 1, 12, 1)
        bitis     = self.bugun.tz_convert(None).to_pydatetime()

        # ── TEFAS yolu (yatırım fonu) ─────────────────────────────────────────
        if fon_mu:
            logger.info(f"  📥 {temiz} → fon verisi çekiliyor (TEFAS)...")
            fiyatlar_tefas = self._tefas_cek(temiz, baslangic, bitis)
            if fiyatlar_tefas is None:
                logger.error(f"  ❌ {temiz}: TEFAS'tan veri alınamadı.")
                return None
            haftalik = fiyatlar_tefas.resample("W-FRI").last().dropna()
            return {
                "fiyatlar":  fiyatlar_tefas,
                "haftalik":  haftalik,
                "temettular": pd.Series(dtype=float),
                "ad":        f"Fon: {temiz}",
            }

        # ── Hisse senedi yolu — PARALEL veri çekme ────────────────────────────
        logger.info(f"  📥 {temiz} → hisse verisi çekiliyor (paralel)...")

        kaynaklar: Dict[str, Optional[pd.DataFrame]] = {
            "Yahoo": None, "Stooq": None, "AlphaVantage": None
        }

        def _yahoo_retry():
            for deneme in range(RETRY_SAYISI):
                try:
                    result = self._yahoo_cek(sembol, baslangic, bitis)
                    if result is not None:
                        return result
                except Exception as e:
                    bekleme = RETRY_BEKLEME[min(deneme, len(RETRY_BEKLEME) - 1)]
                    logger.warning(f"     ⏳ Yahoo deneme {deneme+1}/{RETRY_SAYISI}: {str(e)[:80]}")
                    for _ in range(bekleme):
                        if self._stop_event and self._stop_event.is_set():
                            return None
                        time.sleep(1)
            return None

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {
                pool.submit(_yahoo_retry): "Yahoo",
                pool.submit(self._stooq_cek, sembol, baslangic, bitis): "Stooq",
                pool.submit(self._alphavantage_cek, sembol): "AlphaVantage",
            }
            for future in as_completed(futures):
                kaynak_adi = futures[future]
                try:
                    sonuc_df = future.result()
                    kaynaklar[kaynak_adi] = sonuc_df
                    if sonuc_df is not None:
                        logger.info(f"     ✅ {kaynak_adi:14s}: {len(sonuc_df)} gün")
                    else:
                        logger.info(f"     ⚠️  {kaynak_adi}: veri yok")
                except Exception as e:
                    logger.warning(f"     ⚠️  {kaynak_adi} hata: {e}")

        # En az bir kaynak lazım
        fiyatlar = kaynaklar["Yahoo"] if kaynaklar["Yahoo"] is not None else (kaynaklar["Stooq"] if kaynaklar["Stooq"] is not None else kaynaklar["AlphaVantage"])
        if fiyatlar is None:
            logger.error(f"  ❌ {temiz}: hiçbir kaynaktan veri alınamadı.")
            return None

        # Çapraz doğrulama (BaseAnalyzer'dan)
        self._capraz_dogrula(temiz, kaynaklar, FIYAT_TOLERANS, "₺")

        # Temettü (Yahoo'dan)
        temettular = pd.Series(dtype=float)
        ticker = None
        try:
            yf_sembol = self._bist_sembol(sembol)
            ticker_kwargs = {"session": CURL_SESSION} if HAS_CURL else {}
            ticker = yf.Ticker(yf_sembol, **ticker_kwargs)
            tem    = ticker.dividends
            if tem is not None and not tem.empty:
                temettular = self._utc(tem.to_frame()).iloc[:, 0]
        except Exception:
            pass

        # Şirket adı
        ad = POPULER_BIST.get(temiz, temiz)
        try:
            if ticker is not None:
                name = getattr(ticker.fast_info, "company_name", None)
                if name:
                    ad = name
        except Exception:
            pass

        # Haftalık veri oluştur
        if "Open" in fiyatlar.columns:
            haftalik = fiyatlar.resample("W-FRI").agg({
                "Open": "first", "High": "max", "Low": "min",
                "Close": "last", "Volume": "sum"
            }).dropna()
        else:
            haftalik = fiyatlar.resample("W-FRI").last().dropna()

        return {
            "fiyatlar":  fiyatlar,
            "haftalik":  haftalik,
            "temettular": temettular,
            "ad":        ad,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # ANA ANALİZ
    # ─────────────────────────────────────────────────────────────────────────

    def analiz_et(self, sembol: str, is_tefas: bool = False) -> Optional[Dict]:
        temiz = self._temiz_sembol(sembol)
        logger.info(f"\n{'─'*68}")
        logger.info(f"🔍  {temiz}")
        logger.info(f"{'─'*68}")

        veri = self._veri_cek(sembol, is_tefas=is_tefas)
        if not veri:
            return None

        fiyatlar   = veri["fiyatlar"]
        haftalik   = veri["haftalik"]
        temettular = veri["temettular"]

        son_fiyat = self._son_fiyat_bilgisi(fiyatlar)
        logger.info(f"\n  💰 Son Fiyat: {son_fiyat.fiyat:.2f} ₺ "
                     f"({son_fiyat.degisim:+.2f}%) — {son_fiyat.tarih}")

        sonuc = {
            "sembol": temiz, "ad": veri["ad"],
            "son_fiyat": asdict(son_fiyat),
            "yg": {}, "yr": {}, "yt": {},
            "s5": None, "s3": None,
            "ay": {}, "hafta": {},
            "gunluk_ist": None,
            "risk": None,
        }

        # ── Yıllık getiri ────────────────────────────────────────────────────
        logger.info(f"\n  {'Yıl':<6} {'Getiri':>8} {'Reel':>8} {'Enflasyon':>10} {'Temettü':>8}")
        logger.info(f"  {'─'*46}")
        for yil in self.yillar:
            g = self._yillik_getiri(fiyatlar, yil)
            if g is None:
                continue
            enf = self.yillik_enf.get(yil, VARSAYILAN_ENF)
            r   = g - enf
            t   = self._temettu_verimi(temettular, fiyatlar, yil)
            sonuc["yg"][yil] = g
            sonuc["yr"][yil] = r
            sonuc["yt"][yil] = t
            logger.info(f"  {yil:<6} {g:>+7.2f}%  {r:>+7.2f}%  {enf:>+8.2f}%  {t:>7.2f}%")

        # ── Toplam getiri ─────────────────────────────────────────────────────
        s5 = self._toplam_getiri(fiyatlar, self.yillar[0],  self.yillar[-1])
        s3 = self._toplam_getiri(fiyatlar, self.yillar[-3], self.yillar[-1])
        sonuc["s5"] = s5
        sonuc["s3"] = s3
        logger.info(f"\n  📊 Toplam getiri:")
        if s5 is not None:
            logger.info(f"     Son 5 yıl ({self.yillar[0]}–{self.yillar[-1]}): {s5:>+8.2f}%")
        if s3 is not None:
            logger.info(f"     Son 3 yıl ({self.yillar[-3]}–{self.yillar[-1]}): {s3:>+8.2f}%")

        # ── Aylık dönemsel getiri ─────────────────────────────────────────────
        logger.info(f"\n  {'Dönem':<9} {'Getiri':>8} {'Reel':>8} {'Dönem Enf.':>11}")
        logger.info(f"  {'─'*40}")
        for ay in AYLIK_DONEMLER:
            g, r, enf = self._donemsel_getiri(fiyatlar, ay, self.bugun, self._donem_enflasyonu)
            if g is None:
                continue
            sonuc["ay"][ay] = {"g": g, "r": r, "enf": enf}
            logger.info(f"  Son {ay:>2} ay   {g:>+7.2f}%  {r:>+7.2f}%  {enf:>+9.2f}%")

        # ── Haftalık dönemsel getiri ──────────────────────────────────────────
        logger.info(f"\n  {'Dönem':<12} {'Getiri':>8} {'Reel':>8}")
        logger.info(f"  {'─'*32}")
        for hafta in HAFTALIK_DONEMLER:
            g, r, enf = self._haftalik_getiri(haftalik, hafta, self.bugun, self._donem_enflasyonu)
            if g is None:
                continue
            sonuc["hafta"][hafta] = {"g": g, "r": r, "enf": enf}
            logger.info(f"  Son {hafta:>2} hafta  {g:>+7.2f}%  {r:>+7.2f}%")

        # ── Günlük istatistik ─────────────────────────────────────────────────
        gist = self._gunluk_istatistik(fiyatlar, 30)
        if gist:
            sonuc["gunluk_ist"] = asdict(gist)
            logger.info(f"\n  📈 Son 30 Gün İstatistikleri:")
            logger.info(f"     Ort. günlük getiri : {gist.ort:+.3f}%")
            logger.info(f"     Volatilite (std)   : {gist.std:.3f}%")
            logger.info(f"     Min / Max          : {gist.min:+.2f}% / {gist.max:+.2f}%")
            logger.info(f"     Pozitif / Negatif  : {gist.pozitif} / {gist.negatif} gün")

        # ── Risk Metrikleri (Sharpe + Max Drawdown) — YENİ ────────────────────
        risk = self._risk_metrikleri(fiyatlar, risksiz_faiz=0.30)  # TR risksiz faiz ~%30
        if risk.sharpe_ratio is not None:
            sonuc["risk"] = asdict(risk)
            logger.info(f"\n  🎯 Risk Metrikleri:")
            logger.info(f"     Sharpe Ratio       : {risk.sharpe_ratio:+.3f}")
            logger.info(f"     Max Drawdown       : {risk.max_drawdown:+.2f}% ({risk.max_drawdown_tarih})")

        return sonuc

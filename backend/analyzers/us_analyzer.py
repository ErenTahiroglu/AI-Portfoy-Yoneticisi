"""
🧩 Puzzle Parça: ABD Portföy Analizörü  –  v6.0
==================================================
Yenilikler (v5 → v6):
  • BaseAnalyzer kalıtımı (DRY — ortak hesaplamalar tek yerde)
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

# Render.com/Vercel gibi ortamlarda yazma izni sorunu olmaması için cache'i /tmp/ altına alıyoruz
# yfinance kaldırıldı, yahooquery kullanılacak
import pandas as pd
from io import StringIO
from datetime import datetime
from typing import Dict, Optional

from backend.data.data_sources import (
    HAS_CURL, AV_KEY, req_lib,
    US_VARSAYILAN_ENF as VARSAYILAN_ENF,
    ANALIZ_YIL_SAYI, AYLIK_DONEMLER, RETRY_SAYISI, RETRY_BEKLEME, FIYAT_TOLERANS
)
from backend.analyzers.base_analyzer import BaseAnalyzer, get_cached_cpi

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
class HisseAnaliz(BaseAnalyzer):
    market_code = "US"
# ══════════════════════════════════════════════════════════════════════════════

    def __init__(self, av_key: Optional[str] = None):
        self.bugun  = pd.Timestamp.now(tz="UTC")
        self.bu_yil = self.bugun.year
        self.yillar = list(range(self.bu_yil - ANALIZ_YIL_SAYI, self.bu_yil))
        self.av_key = av_key or AV_KEY

        logger.info(f"\n{'═'*68}")
        logger.info("  ABD PORTFÖY ANALİZ ARACI  –  v6.0")
        logger.info(f"{'═'*68}")
        logger.info(f"  Tarih         : {self.bugun.strftime('%d.%m.%Y')}")
        logger.info(f"  Analiz yılları: {self.yillar[0]} – {self.yillar[-1]}")
        logger.info(f"  curl_cffi     : {'✅ aktif' if HAS_CURL else '⚠️ yok, yedek mod'}")
        logger.info(f"  Alpha Vantage : {'✅ ' + self.av_key[:8] + '...' if self.av_key else '⚠️ yok'}")
        logger.info(f"{'═'*68}\n")

        # ── Enflasyon: TEK çağrı, iki amaç ────────────────────────────────────
        self._enflasyon_al()

    # ─────────────────────────────────────────────────────────────────────────
    # ENFLASYON — TEK FRED ÇAĞRISI, İKİ SONUÇ
    # ─────────────────────────────────────────────────────────────────────────

    def _enflasyon_al(self):
        """FRED'den ABD CPI verisini TEK bir çağrıda alır."""
        cpi = get_cached_cpi(
            "CPIAUCSL",
            start=datetime(self.yillar[0] - 1, 1, 1),
            end=datetime(self.bu_yil, 12, 31),
        )

        if cpi is not None and not cpi.empty:
            sonuc: Dict[int, float] = {}
            for yil in self.yillar:
                try:
                    once = cpi[cpi.index.year == yil - 1]["CPIAUCSL"].iloc[-1]
                    bu   = cpi[cpi.index.year == yil    ]["CPIAUCSL"].iloc[-1]
                    sonuc[yil] = ((bu - once) / once) * 100
                except Exception:
                    sonuc[yil] = VARSAYILAN_ENF
            self.yillik_enf = sonuc

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
            cb = self.aylik_cpi[self.aylik_cpi.index <= _n(bas)]["CPIAUCSL"].iloc[-1]
            ce = self.aylik_cpi[self.aylik_cpi.index <= _n(bit)]["CPIAUCSL"].iloc[-1]
            return ((ce - cb) / cb) * 100
        except Exception:
            return (VARSAYILAN_ENF / 365) * (bit - bas).days

    # ─────────────────────────────────────────────────────────────────────────
    # VERİ KAYNAKLARI
    # ─────────────────────────────────────────────────────────────────────────

    def _yahoo_cek(self, sembol: str, baslangic: datetime, bitis: datetime
                   ) -> Optional[pd.DataFrame]:
        try:
            from yahooquery import Ticker
            t = Ticker(sembol)
            ham = t.history(start=baslangic, end=bitis, adj_ohlc=True)
            if ham is None or not isinstance(ham, pd.DataFrame) or ham.empty:
                return None
            try:
                ham = ham.loc[sembol]
            except KeyError:
                return None
            if ham.empty:
                return None
            ham.columns = [c.title() for c in ham.columns]
            return self._utc(ham)
        except Exception:
            return None

    def _stooq_cek(self, sembol: str, baslangic: datetime, bitis: datetime
                   ) -> Optional[pd.DataFrame]:
        """Stooq'tan doğrudan CSV API ile veri çeker (pandas_datareader kullanmaz)."""
        try:
            stooq_sembol = sembol if "." in sembol else f"{sembol}.US"
            s_start = pd.Timestamp(baslangic).strftime('%Y%m%d')
            s_end   = pd.Timestamp(bitis).strftime('%Y%m%d')
            url = (
                f"https://stooq.pl/q/d/l/"
                f"?s={stooq_sembol.lower()}&d1={s_start}&d2={s_end}&i=d"
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

            if "Information" in data and "rate limit" in data["Information"].lower():
                raise Exception("ALPHA_VANTAGE_RATE_LIMIT")
            if "Note" in data and "API call frequency" in data["Note"]:
                raise Exception("ALPHA_VANTAGE_RATE_LIMIT")

            ts = data.get("Time Series (Daily)", {})
            if not ts:
                return None
            df = pd.DataFrame.from_dict(ts, orient="index")
            df.index = pd.to_datetime(df.index)
            df = df.rename(columns={"5. adjusted close": "Close"})
            df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
            df = df[["Close"]].sort_index()
            return self._utc(df)
        except Exception as e:
            if str(e) == "ALPHA_VANTAGE_RATE_LIMIT":
                raise e
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # ÇOK KAYNAKLI VERİ ÇEKME + PARALEL + DOĞRULAMA
    # ─────────────────────────────────────────────────────────────────────────

    def _veri_cek(self, sembol: str) -> Optional[Dict]:
        logger.info(f"  📥 {sembol} → veri çekiliyor (paralel)...")
        baslangic = datetime(self.yillar[0] - 1, 12, 1)
        bitis     = self.bugun.tz_convert(None).to_pydatetime()

        kaynaklar: Dict[str, Optional[pd.DataFrame]] = {
            "Yahoo": None, "Stooq": None, "AlphaVantage": None
        }
        av_rate_limited = False

        def _yahoo_retry():
            for deneme in range(RETRY_SAYISI):
                try:
                    result = self._yahoo_cek(sembol, baslangic, bitis)
                    if result is not None:
                        return result
                except Exception as e:
                    bekleme = RETRY_BEKLEME[min(deneme, len(RETRY_BEKLEME) - 1)]
                    logger.warning(f"     ⏳ Yahoo deneme {deneme+1}/{RETRY_SAYISI}: {str(e)[:80]}")
                    time.sleep(bekleme)
            return None

        # Render 512MB limitine uymak için kaynak paralelliğini de 2'ye düşürüyoruz
        with ThreadPoolExecutor(max_workers=2) as pool:
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
                    if str(e) == "ALPHA_VANTAGE_RATE_LIMIT":
                        av_rate_limited = True
                        logger.warning("     ⚠️  Alpha Vantage: RATE LIMIT AŞILDI")
                    else:
                        logger.warning(f"     ⚠️  {kaynak_adi} hata: {e}")

        fiyatlar = kaynaklar["Yahoo"] if kaynaklar["Yahoo"] is not None else (kaynaklar["Stooq"] if kaynaklar["Stooq"] is not None else kaynaklar["AlphaVantage"])
        if fiyatlar is None:
            if av_rate_limited:
                raise Exception("ALPHA_VANTAGE_RATE_LIMIT")
            logger.error(f"  ❌ {sembol}: hiçbir kaynaktan veri alınamadı.")
            return None

        # Çapraz doğrulama
        self._capraz_dogrula(sembol, kaynaklar, FIYAT_TOLERANS, "$")

        # Temettü (Yahoo'dan)
        temettular = pd.Series(dtype=float)
        ad = sembol
        
        try:
            from yahooquery import Ticker
            t = Ticker(sembol)
            
            # Şirket adı
            price_info = t.price
            if isinstance(price_info, dict) and sembol in price_info:
                ad = price_info[sembol].get('shortName') or price_info[sembol].get('longName') or sembol
                
            # Temettü (Eğer Yahoo verisi varsa)
            if kaynaklar["Yahoo"] is not None and "Dividends" in kaynaklar["Yahoo"].columns:
                tem = kaynaklar["Yahoo"]["Dividends"]
                tem = tem[tem > 0]
                if not tem.empty:
                    temettular = tem
        except Exception:
            pass

        return {"fiyatlar": fiyatlar, "temettular": temettular, "ad": ad}

    # ─────────────────────────────────────────────────────────────────────────
    # ANA ANALİZ
    # ─────────────────────────────────────────────────────────────────────────

    def analiz_et(self, sembol: str) -> Optional[Dict]:
        logger.info(f"\n{'─'*68}")
        logger.info(f"🔍  {sembol}")
        logger.info(f"{'─'*68}")

        try:
            veri = self._veri_cek(sembol)
        except Exception as e:
            if str(e) == "ALPHA_VANTAGE_RATE_LIMIT":
                raise e
            return None

        if not veri:
            return None

        fiyatlar   = veri["fiyatlar"]
        temettular = veri["temettular"]

        son_fiyat = self._son_fiyat_bilgisi(fiyatlar)

        sonuc = {
            "sembol": sembol, "ad": veri["ad"],
            "son_fiyat": asdict(son_fiyat),
            "yg": {}, "yr": {}, "yt": {},
            "s5": None, "s3": None, "ay": {},
            "risk": None,
        }

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

        s5 = self._toplam_getiri(fiyatlar, self.yillar[0],  self.yillar[-1])
        s3 = self._toplam_getiri(fiyatlar, self.yillar[-3], self.yillar[-1])
        sonuc["s5"] = s5
        sonuc["s3"] = s3
        logger.info("\n  📊 Toplam getiri:")
        if s5 is not None:
            logger.info(f"     Son 5 yıl ({self.yillar[0]}–{self.yillar[-1]}): {s5:>+8.2f}%")
        if s3 is not None:
            logger.info(f"     Son 3 yıl ({self.yillar[-3]}–{self.yillar[-1]}): {s3:>+8.2f}%")

        logger.info(f"\n  {'Dönem':<9} {'Getiri':>8} {'Reel':>8} {'Dönem Enf.':>11}")
        logger.info(f"  {'─'*40}")
        for ay in AYLIK_DONEMLER:
            g, r, enf = self._donemsel_getiri(fiyatlar, ay, self.bugun, self._donem_enflasyonu)
            if g is None:
                continue
            sonuc["ay"][ay] = {"g": g, "r": r, "enf": enf}
            logger.info(f"  Son {ay:>2} ay   {g:>+7.2f}%  {r:>+7.2f}%  {enf:>+9.2f}%")

        # ── Risk Metrikleri (Sharpe + Max Drawdown) — YENİ ────────────────────
        risk = self._risk_metrikleri(fiyatlar, risksiz_faiz=0.05)  # US risksiz ~%5
        if risk.sharpe_ratio is not None:
            sonuc["risk"] = asdict(risk)
            logger.info("\n  🎯 Risk Metrikleri:")
            logger.info(f"     Sharpe Ratio       : {risk.sharpe_ratio:+.3f}")
            logger.info(f"     Max Drawdown       : {risk.max_drawdown:+.2f}% ({risk.max_drawdown_tarih})")

        return sonuc

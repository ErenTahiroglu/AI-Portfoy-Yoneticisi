"""
🧩 Puzzle Parça: TEFAS Scraper (Curl CFFI)
=================================================
TEFAS'ın F5 Advanced WAF engelini curl_cffi tabanlı TLS impersonation ile aşar.
Playwright'tan çok daha hızlı ve stabildir.
"""

import logging
import pandas as pd
import datetime
import requests
from requests import Session
from rate_limiter import with_retry

logger = logging.getLogger(__name__)

class TefasScraper:
    """TEFAS fon verilerini çekmek için HTTP istekleri kullanır.
    
    Kullanım:
        scraper = TefasScraper()
        df = scraper.fetch_sync("TP2", start_date, end_date)
    """
    
    def __init__(self):
        self._session = Session()
        self._headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Origin': 'https://www.tefas.gov.tr',
            'Referer': 'https://www.tefas.gov.tr/FonAnaliz.aspx',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    @with_retry()
    def _fetch_chunk(self, fonkod: str, bastarih: str, bittarih: str) -> pd.DataFrame:
        url = 'https://www.tefas.gov.tr/api/DB/BindHistoryInfo'
        
        # 1. YAT dene
        data_yat = f"fontip=YAT&sfonkod={fonkod}&bastarih={bastarih}&bittarih={bittarih}"
        try:
            r = self._session.post(url, data=data_yat, headers=self._headers, timeout=5)
            if r.status_code == 200:
                try:
                    json_data = r.json()
                    if json_data and json_data.get("data"):
                        return self._parse_tefas_data(json_data["data"])
                except Exception:
                    pass
            
            # 2. Bulamazsa EMK dene
            data_emk = f"fontip=EMK&sfonkod={fonkod}&bastarih={bastarih}&bittarih={bittarih}"
            r2 = self._session.post(url, data=data_emk, headers=self._headers, timeout=5)
            if r2.status_code == 200:
                try:
                    json_data = r2.json()
                    if json_data and json_data.get("data"):
                        return self._parse_tefas_data(json_data["data"])
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"[{fonkod}] TEFAS API başarısız ({bastarih}-{bittarih}): {e}")
            
        return pd.DataFrame()

    def fetch_sync(self, fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        """Belirtilen tarih aralığındaki fon verisini 90 günlük parçalar halinde çeker."""
        chunk_days = 90
        current_start = start_date
        dfs = []
        
        logger.info(f"[{fonkod}] TEFAS bypass: 90 günlük parçalar halinde veri çekiliyor...")
        
        while current_start <= end_date:
            current_end = min(current_start + datetime.timedelta(days=chunk_days - 1), end_date)
            
            bastarih = current_start.strftime("%d.%m.%Y")
            bittarih = current_end.strftime("%d.%m.%Y")
            
            df_chunk = self._fetch_chunk(fonkod, bastarih, bittarih)
            if not df_chunk.empty:
                dfs.append(df_chunk)
                
            current_start = current_end + datetime.timedelta(days=1)
            
        if dfs:
            df_final = pd.concat(dfs)
            df_final = df_final[~df_final.index.duplicated(keep='first')]
            df_final.sort_index(inplace=True)
            return df_final
            
        return pd.DataFrame()
        
    @staticmethod
    def _parse_tefas_data(data: list) -> pd.DataFrame:
        """TEFAS JSON verisini pandas DataFrame'e çevirir."""
        df = pd.DataFrame(data)
        
        if "TARIH" not in df.columns or "FIYAT" not in df.columns:
            return pd.DataFrame()
        
        # .NET /Date(...)/ formatı kontrolü
        if df["TARIH"].astype(str).str.contains("/Date").any():
            df["TARIH"] = df["TARIH"].astype(str).str.extract(r'\/Date\((\d+)\)\/')
        
        df["Date"] = pd.to_datetime(df["TARIH"].astype(float), unit="ms", errors="coerce")
        df["Close"] = pd.to_numeric(df["FIYAT"], errors="coerce")
        df.dropna(subset=["Date", "Close"], inplace=True)
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)
        return df[["Close"]]

    def close(self):
        """curl_cffi için tarayıcı kalıntısı yok, geriye dönük uyumluluk için."""
        pass

# ── Geriye dönük uyumluluk ────────────────────────────────────────────────────
def get_tefas_data_sync(fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    """Eski API: tefas_scraper.get_tefas_data_sync(...) şeklinde kullananlar için."""
    scraper = TefasScraper()
    return scraper.fetch_sync(fonkod, start_date, end_date)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start = datetime.date(2023, 1, 1)
    end = datetime.date(2024, 3, 1)
    
    scraper = TefasScraper()
    for kod in ["TP2", "ZP8", "NIB"]:
        res = scraper.fetch_sync(kod, start, end)
        print(f"\n{kod}: {len(res)} gün")
        print(res.tail())

"""
🧩 REFACTORED TEFAS Scraper (Requests-based, 90-Day Chunking)
=============================================================
Bypasses the WAF without heavy Selenium/Playwright dependencies,
allowing successful deployment to Vercel (250MB limit).
"""

import logging
import pandas as pd
import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class TefasScraper:
    def __init__(self):
        self.url = "https://www.tefas.gov.tr/api/DB/BindHistoryInfo"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.tefas.gov.tr",
            "Referer": "https://www.tefas.gov.tr/FonAnaliz.aspx",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_chunk(self, fonkod: str, start_date: str, end_date: str, fontip: str = "YAT"):
        data = {
            "fontip": fontip,
            "sfonkod": fonkod,
            "bastarih": start_date,
            "bittarih": end_date
        }
        resp = requests.post(self.url, headers=self.headers, data=data, timeout=15)
        resp.raise_for_status()
        
        if "text/html" in resp.headers.get("Content-Type", ""):
            raise ValueError(f"WAF Blocked Request (HTML received instead of JSON) for chunk {start_date} to {end_date}")
            
        json_resp = resp.json()
        return json_resp.get("data", [])

    def fetch_sync(self, fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        logger.info(f"[{fonkod}] TEFAS Requests Fetching data from {start_date} to {end_date} in 90-day chunks...")
        
        all_data = []
        current_start = start_date
        
        while current_start <= end_date:
            current_end = current_start + datetime.timedelta(days=89)
            if current_end > end_date:
                current_end = end_date
                
            str_start = current_start.strftime("%d.%m.%Y")
            str_end = current_end.strftime("%d.%m.%Y")
            
            try:
                # Try YAT first
                chunk_data = self._fetch_chunk(fonkod, str_start, str_end, "YAT")
                if not chunk_data:
                    # Try EMK (Pension Funds)
                    chunk_data = self._fetch_chunk(fonkod, str_start, str_end, "EMK")
                
                if chunk_data:
                    all_data.extend(chunk_data)
                    logger.debug(f"[{fonkod}] Fetched {len(chunk_data)} records for {str_start} - {str_end}")
                    
            except Exception as e:
                logger.error(f"[{fonkod}] Failed to fetch chunk {str_start} - {str_end}: {e}")
                
            current_start = current_end + datetime.timedelta(days=1)
            
        if not all_data:
            logger.warning(f"[{fonkod}] No data returned from TEFAS.")
            return pd.DataFrame()
            
        return self._parse_tefas_data(all_data)

    def _parse_tefas_data(self, data: list) -> pd.DataFrame:
        df = pd.DataFrame(data)
        if "TARIH" not in df.columns or "FIYAT" not in df.columns:
            return pd.DataFrame()
            
        if df["TARIH"].astype(str).str.contains("/Date").any():
            df["TARIH"] = df["TARIH"].astype(str).str.extract(r'\/Date\((\d+)\)\/')
            
        df["Date"] = pd.to_datetime(df["TARIH"].astype(float), unit="ms", errors="coerce")
        df["Close"] = pd.to_numeric(df["FIYAT"], errors="coerce")
        df.dropna(subset=["Date", "Close"], inplace=True)
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)
        return df[["Close"]]

    def close(self):
        pass

def get_tefas_data_sync(fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    scraper = TefasScraper()
    return scraper.fetch_sync(fonkod, start_date, end_date)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = TefasScraper()
    end = datetime.date.today()
    start = end - datetime.timedelta(days=150)
    
    df = scraper.fetch_sync("TP2", start, end)
    print("TP2 Data:")
    print(df.tail())

"""
🧩 TEFAS FON YARDIMCISI (Super-Optimized - curl_cffi & Render Uyumlu)
============================================================
Render.com Free Tier (512MB RAM) limitine uymak için
Playwright yerine curl_cffi (impersonate="chrome") kullanır.
WAF ve Cookie engellerini aşmak için tarayıcıyı taklit eder.
"""

import json
import logging
import pandas as pd
import datetime
import gc
import time
import threading
from curl_cffi import requests
from bs4 import BeautifulSoup
from typing import cast

logger = logging.getLogger(__name__)

class TefasScraper:
    def __init__(self):
        self.url_base = "https://www.tefas.gov.tr/FonAnaliz.aspx"
        self.url_api = "https://www.tefas.gov.tr/api/DB/BindHistoryInfo"
        # Impersonate chrome to bypass WAF
        self.session = requests.Session(impersonate="chrome")
        self.fund_type_cache = {} # Cache for fonkod -> fontip (YAT/EMK)

    def _ensure_session(self):
        """WAF ve Cookie oturumu için ana sayfayı bir kez ziyaret et."""
        try:
            # Sadece bir kere ana sayfaya gitmek yeterlidir
            if not hasattr(self, '_session_ready'):
                logger.info("Initializing TEFAS session...")
                self.session.get(self.url_base, timeout=15)
                self._session_ready = True
        except Exception as e:
            logger.error(f"Failed to initialize TEFAS session: {e}")

    def _fetch_chunk(self, fonkod: str, start_date: str, end_date: str, fontip: str = "YAT"):
        payload = {
            "fontip": fontip,
            "sfonkod": fonkod,
            "bastarih": start_date,
            "bittarih": end_date
        }
        
        for attempt in range(3):
            try:
                response = self.session.post(
                    self.url_api, 
                    data=payload,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "X-Requested-With": "XMLHttpRequest",
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        "Referer": self.url_base,
                        "Origin": "https://www.tefas.gov.tr"
                    },
                    timeout=(15, 60) # Connect: 15s, Read: 60s
                )
                
                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        return json_data.get("data", [])
                    except json.JSONDecodeError:
                        # WAF Block veya HTML döndü
                        soup = BeautifulSoup(response.text, "html.parser")
                        clean_text = soup.get_text(separator=' ', strip=True)
                        if "WAF" in clean_text or "Cloudflare" in clean_text:
                            logger.warning(f"TEFAS WAF Block detected for {fonkod} (Attempt {attempt+1}/3)")
                        if attempt == 2:
                            return []
                else:
                    logger.warning(f"HTTP Error {response.status_code} for {fonkod} (Attempt {attempt+1}/3)")
                    if attempt == 2:
                        return []
                    
            except Exception as e:
                logger.error(f"Chunk fetch error for {fonkod} (Attempt {attempt+1}/3): {e}")
                if attempt == 2:
                    return []
            
            # Geri çekilme (Backoff)
            time.sleep(1 * (attempt+1))
        return []

    def fetch_sync(self, fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        logger.info(f"[{fonkod}] TEFAS Optimized curl_cffi Fetching from {start_date} to {end_date}...")
        
        self._ensure_session()
        
        all_data = []
        current_start = start_date
        
        # Determine fund type once per request if not cached
        fontip = self.fund_type_cache.get(fonkod)
        
        while current_start <= end_date:
            current_end = current_start + datetime.timedelta(days=180) # 6 Month chunks (RAM safe)
            if current_end > end_date:
                current_end = end_date
                
            str_start = current_start.strftime("%d.%m.%Y")
            str_end = current_end.strftime("%d.%m.%Y")
            
            try:
                chunk_data = []
                if fontip:
                    # Use known fund type
                    chunk_data = self._fetch_chunk(fonkod, str_start, str_end, fontip)
                else:
                    # Detect fund type (YAT is most common)
                    chunk_data = self._fetch_chunk(fonkod, str_start, str_end, "YAT")
                    if chunk_data:
                        fontip = "YAT"
                        self.fund_type_cache[fonkod] = "YAT"
                    else:
                        # Try EMK (Emeklilik)
                        chunk_data = self._fetch_chunk(fonkod, str_start, str_end, "EMK")
                        if chunk_data:
                            fontip = "EMK"
                            self.fund_type_cache[fonkod] = "EMK"
                
                if chunk_data:
                    all_data.extend(chunk_data)
                    logger.debug(f"[{fonkod}] Fetched {len(chunk_data)} records for {str_start} - {str_end}")
                    # Explicit memory cleanup for large lists
                    del chunk_data
                    gc.collect()
                
                # Small delay to respect WAF
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"[{fonkod}] Failed to fetch chunk {str_start} - {str_end}: {e}")
                
            current_start = current_end + datetime.timedelta(days=1)
            
        if not all_data:
            logger.warning(f"[{fonkod}] No data returned from TEFAS.")
            return pd.DataFrame(columns=["Close"]).rename_axis("Date")
            
        df = self._parse_tefas_data(all_data)
        gc.collect()
        return df

    def _parse_tefas_data(self, data: list) -> pd.DataFrame:
        df = pd.DataFrame(data)
        if df.empty or "TARIH" not in df.columns or "FIYAT" not in df.columns:
            return pd.DataFrame(columns=["Close"]).rename_axis("Date")
            
        # Handle /Date(123456789)/ format if present
        if df["TARIH"].astype(str).str.contains("/Date").any():
            df["TARIH"] = df["TARIH"].astype(str).str.extract(r'\/Date\((\d+)\)\/')
            
        df["Date"] = pd.to_datetime(df["TARIH"].astype(float), unit="ms", errors="coerce")
        df["Close"] = pd.to_numeric(df["FIYAT"], errors="coerce")
        df.dropna(subset=["Date", "Close"], inplace=True)
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        return cast(pd.DataFrame, df[["Close"]])

_tefas_lock = threading.Lock()

def get_tefas_data_sync(fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    with _tefas_lock:
        scraper = TefasScraper()
        return scraper.fetch_sync(fonkod, start_date, end_date)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    end = datetime.date.today()
    start = end - datetime.timedelta(days=730) # 2 Years
    df = get_tefas_data_sync("TI1", start, end)
    logger.info("TI1 Data:")
    logger.info(df.tail() if not df.empty else "No Data")

"""
🧩 TEFAS FON YARDIMCISI (Optimized Playwright - Render Uyumlu)
============================================================
Render.com Free Tier (512MB RAM) limitine uymak için
özel bellek optimizasyonlu Chromium ayarları ile çalışır.
Browser her istekte bir kez açılır ve tüm chunklar bitince kapatılır.
"""

import json
import logging
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import gc
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class TefasScraper:
    def __init__(self):
        self.url = "https://www.tefas.gov.tr/api/DB/BindHistoryInfo"

    async def _fetch_chunk_with_page(self, page, fonkod: str, start_date: str, end_date: str, fontip: str = "YAT"):
        try:
            # Sadece gerekli JSON POST isteklerini geçirerek belleği korur
            await page.route(
                "**/*", 
                lambda route: route.continue_() if route.request.resource_type in ["document", "xhr", "fetch"] else route.abort()
            )
            
            await page.goto("https://www.tefas.gov.tr/FonAnaliz.aspx", wait_until="domcontentloaded", timeout=20000)
            
            payload = f"fontip={fontip}&sfonkod={fonkod}&bastarih={start_date}&bittarih={end_date}"
            
            js_code = f"""
            async () => {{
                try {{
                    const response = await fetch('{self.url}', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Origin': 'https://www.tefas.gov.tr',
                            'Referer': 'https://www.tefas.gov.tr/FonAnaliz.aspx',
                            'Accept': 'application/json, text/javascript, */*; q=0.01'
                        }},
                        body: '{payload}'
                    }});
                    const text = await response.text();
                    return text;
                }} catch (e) {{
                    return "ERROR: " + e.message;
                }}
            }}
            """
            
            result_text = await page.evaluate(js_code)
            
            if result_text.startswith("ERROR:"):
                raise ValueError(f"Browser Fetch Error: {result_text}")
                
            try:
                json_data = json.loads(result_text)
                return json_data.get("data", [])
            except json.JSONDecodeError:
                soup = BeautifulSoup(result_text, "html.parser")
                clean_text = soup.get_text(separator=' ', strip=True)
                if len(clean_text) > 200:
                    clean_text = clean_text[:200] + "..."
                raise ValueError(f"WAF Block (HTML received): {clean_text}")
                
        except Exception as e:
            logger.error(f"Chunk fetch failed for {fonkod}: {e}")
            return []

    async def _fetch_async(self, fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        logger.info(f"[{fonkod}] TEFAS Optimized Playwright Fetching from {start_date} to {end_date}...")
        
        all_data = []
        current_start = start_date
        
        async with async_playwright() as p:
            # Memory Optimized Chromium Arguments for 512MB RAM Linux
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--single-process',
                    '--disable-extensions',
                    '--js-flags=--max-old-space-size=128',
                    '--disable-software-rasterizer',
                    '--mute-audio'
                ]
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 800, 'height': 600}
            )
            
            page = await context.new_page()
            
            try:
                while current_start <= end_date:
                    current_end = current_start + datetime.timedelta(days=89)
                    if current_end > end_date:
                        current_end = end_date
                        
                    str_start = current_start.strftime("%d.%m.%Y")
                    str_end = current_end.strftime("%d.%m.%Y")
                    
                    try:
                        chunk_data = await self._fetch_chunk_with_page(page, fonkod, str_start, str_end, "YAT")
                        if not chunk_data:
                            chunk_data = await self._fetch_chunk_with_page(page, fonkod, str_start, str_end, "EMK")
                        
                        if chunk_data:
                            all_data.extend(chunk_data)
                            logger.debug(f"[{fonkod}] Fetched {len(chunk_data)} records for {str_start} - {str_end}")
                            
                    except Exception as e:
                        logger.error(f"[{fonkod}] Failed to fetch chunk {str_start} - {str_end}: {e}")
                        
                    current_start = current_end + datetime.timedelta(days=1)
                    
                if not all_data:
                    logger.warning(f"[{fonkod}] No data returned from TEFAS.")
                    return pd.DataFrame(columns=["Close"]).rename_axis("Date")
                    
                return self._parse_tefas_data(all_data)
                
            finally:
                await browser.close()
                gc.collect()

    def _parse_tefas_data(self, data: list) -> pd.DataFrame:
        df = pd.DataFrame(data)
        if "TARIH" not in df.columns or "FIYAT" not in df.columns:
            return pd.DataFrame(columns=["Close"]).rename_axis("Date")
            
        if df["TARIH"].astype(str).str.contains("/Date").any():
            df["TARIH"] = df["TARIH"].astype(str).str.extract(r'\/Date\((\d+)\)\/')
            
        df["Date"] = pd.to_datetime(df["TARIH"].astype(float), unit="ms", errors="coerce")
        df["Close"] = pd.to_numeric(df["FIYAT"], errors="coerce")
        df.dropna(subset=["Date", "Close"], inplace=True)
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)
        return df[["Close"]]

    def fetch_sync(self, fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(self._fetch_async(fonkod, start_date, end_date), loop)
            return future.result()
        else:
            return loop.run_until_complete(self._fetch_async(fonkod, start_date, end_date))

import threading

_tefas_lock = threading.Lock()

def get_tefas_data_sync(fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    with _tefas_lock:
        scraper = TefasScraper()
        return scraper.fetch_sync(fonkod, start_date, end_date)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    end = datetime.date.today()
    start = end - datetime.timedelta(days=150)
    df = get_tefas_data_sync("TP2", start, end)
    print("TP2 Data:")
    print(df.tail() if not df.empty else "No Data")

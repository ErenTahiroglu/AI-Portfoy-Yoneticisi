"""
🧩 Puzzle Parça: TEFAS Scraper (Sanal Tarayıcı)
=================================================
TEFAS'ın F5 Advanced WAF engelini Playwright headless browser ile aşar.
Tarayıcıyı bir kez açıp tüm fonlar için yeniden kullanır (Singleton).
"""

import asyncio
import logging
import pandas as pd
from playwright.async_api import async_playwright, Browser, BrowserContext
import datetime

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
# Singleton Browser Yöneticisi
# ══════════════════════════════════════════════════════════════════════════════

class TefasScraper:
    """TEFAS WAF'ını aşmak için tek bir Chromium instance'ı yönetir.
    
    Kullanım:
        scraper = TefasScraper()
        df = scraper.fetch_sync("TP2", start_date, end_date)
        # ... daha fazla fon çek ...
        scraper.close()  # sonda temizle
    """
    
    _instance = None  # Singleton
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._browser = None
            cls._instance._context = None
            cls._instance._playwright = None
            cls._instance._loop = None
        return cls._instance
    
    def _get_loop(self):
        """Mevcut veya yeni event loop döndürür."""
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        self._loop = loop
        return loop

    async def _ensure_browser(self):
        """Tarayıcı açık değilse bir kez açar."""
        if self._browser is None or not self._browser.is_connected():
            logger.info("🌐 Playwright Chromium başlatılıyor (tek seferlik)...")
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            self._context = await self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 720},
                ignore_https_errors=True
            )
            # Bot tespiti atlatma
            await self._context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            # WAF cookie'lerini almak için ana sayfaya bir kez git
            page = await self._context.new_page()
            try:
                await page.goto(
                    "https://www.tefas.gov.tr/FonAnaliz.aspx",
                    wait_until="domcontentloaded", timeout=30000
                )
                await page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f"TEFAS ana sayfa yüklenemedi: {e}")
            finally:
                await page.close()
            logger.info("✅ Playwright Chromium hazır.")
    
    async def _fetch_async(self, fonkod: str, bastarih: str, bittarih: str) -> pd.DataFrame:
        """Tek bir fon için async veri çekimi. Tarayıcı zaten açık."""
        await self._ensure_browser()
        
        page = await self._context.new_page()
        try:
            # Navigate to TEFAS to get correct origin/cookies
            await page.goto('https://www.tefas.gov.tr/', wait_until='commit')
            # Tarayıcı içinden fetch ile API'yi çağır (WAF cookie'leri otomatik gider)
            script = f"""
            async () => {{
                try {{
                    const response = await fetch('https://www.tefas.gov.tr/api/DB/BindHistoryInfo', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                            'X-Requested-With': 'XMLHttpRequest'
                        }},
                        body: 'fontip=YAT&sfonkod={fonkod}&bastarih={bastarih}&bittarih={bittarih}'
                    }});
                    const json = await response.json();
                    if (json && json.data && json.data.length > 0) return json;
                    
                    // YAT bulamazsa EMK dene
                    const r2 = await fetch('https://www.tefas.gov.tr/api/DB/BindHistoryInfo', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                            'X-Requested-With': 'XMLHttpRequest'
                        }},
                        body: 'fontip=EMK&sfonkod={fonkod}&bastarih={bastarih}&bittarih={bittarih}'
                    }});
                    return await r2.json();
                }} catch (e) {{ return null; }}
            }}
            """
            json_response = await page.evaluate(script)
            logger.debug(f"JSON RESP for {fonkod}: {json_response}")
            
            if not json_response or "data" not in json_response:
                return pd.DataFrame()
            
            data = json_response.get("data", [])
            if not data:
                return pd.DataFrame()
            
            return self._parse_tefas_data(data)
            
        except Exception as e:
            logger.error(f"[{fonkod}] Playwright fetch başarısız: {e}")
            return pd.DataFrame()
        finally:
            await page.close()  # Sayfa kapanır, tarayıcı açık kalır
    
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
    
    def fetch_sync(self, fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        """Senkron sarmalayıcı — her yerden çağrılabilir."""
        logger.info(f"[{fonkod}] TEFAS WAF bypass başlatılıyor...")
        loop = self._get_loop()
        bastarih = start_date.strftime("%d.%m.%Y")
        bittarih = end_date.strftime("%d.%m.%Y")
        return loop.run_until_complete(self._fetch_async(fonkod, bastarih, bittarih))
    
    def close(self):
        """Tarayıcıyı kapat (uygulama kapanırken çağrılmalı)."""
        if self._browser and self._browser.is_connected():
            loop = self._get_loop()
            loop.run_until_complete(self._browser.close())
            self._browser = None
            self._context = None
        if self._playwright:
            loop = self._get_loop()
            loop.run_until_complete(self._playwright.stop())
            self._playwright = None
        logger.info("🔒 Playwright Chromium kapatıldı.")


# ── Geriye dönük uyumluluk ────────────────────────────────────────────────────
def get_tefas_data_sync(fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    """Eski API: tefas_scraper.get_tefas_data_sync(...) şeklinde kullananlar için."""
    scraper = TefasScraper()
    return scraper.fetch_sync(fonkod, start_date, end_date)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start = datetime.date.today() - datetime.timedelta(days=365)
    end = datetime.date.today()
    
    scraper = TefasScraper()
    for kod in ["TP2", "ZP8"]:
        res = scraper.fetch_sync(kod, start, end)
        print(f"\n{kod}: {len(res)} gün")
        print(res.tail())
    scraper.close()

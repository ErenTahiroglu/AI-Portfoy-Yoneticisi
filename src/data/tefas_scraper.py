"""
🧩 REFACTORED TEFAS Scraper
===========================
Uses the official 'tefas' PyPI package to easily download fund data.
This eliminates the massive Playwright dependency, allowing Deployment to Vercel.
"""

import logging
import pandas as pd
import datetime
from tefas import Crawler

logger = logging.getLogger(__name__)

class TefasScraper:
    def fetch_sync(self, fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        """
        Uses tefas Crawler to fetch fund data.
        Returns a DataFrame with a DatetimeIndex and a 'Close' column representing the price.
        """
        logger.info(f"[{fonkod}] TEFAS Crawler Fetching data from {start_date} to {end_date}...")
        try:
            crawler = Crawler()
            
            # Fetch data using tefas.Crawler
            data = crawler.fetch(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                name=fonkod,
                columns=["date", "price"]
            )
            
            if data is None or data.empty:
                logger.warning(f"[{fonkod}] No data returned from TEFAS.")
                return pd.DataFrame()
                
            df = data.copy()
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.rename(columns={'price': 'Close'}, inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"[{fonkod}] Successfully fetched {len(df)} days of data.")
            return df[['Close']]
            
        except Exception as e:
            logger.error(f"[{fonkod}] TEFAS fetch failed: {e}")
            return pd.DataFrame()

    def close(self):
        pass

def get_tefas_data_sync(fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    scraper = TefasScraper()
    return scraper.fetch_sync(fonkod, start_date, end_date)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = TefasScraper()
    end = datetime.date.today()
    start = end - datetime.timedelta(days=365)
    
    df = scraper.fetch_sync("TP2", start, end)
    print("TP2 Data:")
    print(df.tail())

"""
🧩 TEFAS FON YARDIMCISI (Statik Fallback)
=========================================
Cloudflare (WAF) kısıtlamaları ve Vercel (250MB) limitleri sebebiyle
canlı veri çekimi geçici olarak deaktif edilmiştir. Analizin çökmemesi
için boş veri döndüren güvenli bir iskelettir.
"""

import pandas as pd
import datetime
import logging

logger = logging.getLogger(__name__)

def get_tefas_data_sync(fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    """
    TEFAS Cloudflare korumasını Vercel üzerinden aşmak mümkün olmadığı için,
    analizin sonsuz döngüye girmemesi ve çökmemesi adına boş (güvenli) DataFrame döner.
    """
    logger.warning(f"[{fonkod}] TEFAS canlı veri çekimi WAF limitleri sebebiyle atlandı.")
    
    # İleride bir API bulunursa buraya kolayca bağlanabilir.
    # Şimdilik uygulamanın (BIST ve US hisseleri için) hata vermeden devam etmesini sağlıyoruz.
    
    # Create an empty DataFrame with the expected structure
    df = pd.DataFrame(columns=["Close"])
    df.index.name = "Date"
    return df

class TefasScraper:
    def __init__(self):
        pass

    def fetch_sync(self, fonkod: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
        return get_tefas_data_sync(fonkod, start_date, end_date)

    def close(self):
        pass

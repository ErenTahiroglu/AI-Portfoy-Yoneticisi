"""
🧩 Puzzle Parça: Veri Sabitleri
============================================
Uygulama genelinde kullanılan statik veriler,
önerilen hisse listeleri ve genel yapılandırma sabitleri.
"""

POPULAR_TICKERS = {
    # ABD Popüler
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.", "TSLA": "Tesla Inc.", "META": "Meta Platforms",
    "NVDA": "NVIDIA Corp.", "JPM": "JPMorgan Chase", "V": "Visa Inc.",
    "JNJ": "Johnson & Johnson", "WMT": "Walmart Inc.", "PG": "Procter & Gamble",
    "MA": "Mastercard Inc.", "UNH": "UnitedHealth Group", "HD": "Home Depot",
    "DIS": "Walt Disney Co.", "BAC": "Bank of America", "KO": "Coca-Cola Co.",
    "PEP": "PepsiCo Inc.", "NFLX": "Netflix Inc.", "INTC": "Intel Corp.",
    "AMD": "Advanced Micro Devices", "CRM": "Salesforce Inc.", "AVGO": "Broadcom Inc.",
    "COST": "Costco Wholesale", "ABBV": "AbbVie Inc.", "MRK": "Merck & Co.",
    "TMO": "Thermo Fisher", "ACN": "Accenture plc", "LLY": "Eli Lilly & Co.",
    "PYPL": "PayPal Holdings", "NKE": "Nike Inc.", "ADBE": "Adobe Inc.",
    "CSCO": "Cisco Systems", "ORCL": "Oracle Corp.", "TXN": "Texas Instruments",
    # BIST Popüler
    "THYAO": "Türk Hava Yolları", "ASELS": "Aselsan", "GARAN": "Garanti Bankası",
    "AKBNK": "Akbank", "YKBNK": "Yapı Kredi Bankası", "EREGL": "Ereğli Demir Çelik",
    "BIMAS": "BİM Mağazaları", "SAHOL": "Sabancı Holding", "KCHOL": "Koç Holding",
    "SISE": "Şişecam", "TUPRS": "Tüpraş", "FROTO": "Ford Otosan",
    "TOASO": "Tofaş", "TCELL": "Turkcell", "PGSUS": "Pegasus",
    "TAVHL": "TAV Havalimanları", "EKGYO": "Emlak Konut GYO", "KOZAL": "Koza Altın",
    "SASA": "SASA Polyester", "TTKOM": "Türk Telekom", "ARCLK": "Arçelik",
    "MGROS": "Migros", "PETKM": "PETKİM", "SOKM": "Şok Marketler",
    "VESTL": "Vestel Elektronik", "HALKB": "Halkbank", "VAKBN": "VakıfBank",
    "GUBRF": "Gübre Fabrikaları", "KOZAA": "Koza Anadolu Metal", "ODAS": "Odaş Elektrik",
    "KRDMD": "Kardemir D", "AEFES": "Anadolu Efes", "ENKAI": "Enka İnşaat",
    "DOHOL": "Doğan Holding", "ISCTR": "İş Bankası C", "ALARK": "Alarko Holding",
    # TEFAS Popüler
    "TP2": "Tera Portföy Para Piyasası Fonu", "AKB": "Ak Portföy Birinci Değişken Fon",
    "ZP8": "Ziraat Portföy Kehribar Para Piyasası Katılım Serbest Fon", "IPB": "İş Portföy Birinci Değişken Fon",
    "YAY": "Yapı Kredi Yabancı Teknoloji Hisse Senedi Fonu", "TI2": "TEB Portföy İş İştirakleri Fonu",
    "MAC": "Marmara Capital Hisse Senedi Fonu", "AFA": "Ak Portföy Amerika Yabancı Hisse Fonu",
    "TDF": "TEB Portföy Amerika Yabancı Hisse Fonu", "KTM": "Kuveyt Türk Portföy Katılım Serbest Fon",
    "GBG": "Garanti Portföy Birinci Değişken Fon", "TMM": "Tacirler Portföy Değişken Fon",
    "NRC": "Neo Portföy Birinci Değişken Fon", "YAS": "Yapı Kredi Koç Holding İştirak",
    "NVDI": "GraniteShares 1.5x Long NVDA ETF", "IUV": "İş Portföy BIST Teknoloji Fonu",
}

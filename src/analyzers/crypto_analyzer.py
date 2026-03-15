import httpx
import logging
import asyncio
from datetime import datetime
from src.core.analysis_engine import BaseAnalyzerStrategy

logger = logging.getLogger(__name__)

class CryptoAnalyzerStrategy(BaseAnalyzerStrategy):
    """Kripto Para Analiz Stratejisi — Binance API"""
    
    @property
    def name(self): return "crypto"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        market = context.get("market")
        if market != "CRYPTO": return

        async def fetch_crypto():
            try:
                # Binance Formatına Getir (Dash/USD temizle)
                clean_symbol = ticker.upper().replace("-", "").replace("USD", "USDT")
                if "USDT" not in clean_symbol:
                    clean_symbol += "USDT"

                async with httpx.AsyncClient() as client:
                    # 1. 24s Ticker Verisi (Anlık Fiyat & Değişim)
                    ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={clean_symbol}"
                    res_ticker = await client.get(ticker_url)
                    
                    if res_ticker.status_code == 200:
                        data = res_ticker.json()
                        price = float(data.get("lastPrice", 0))
                        change = float(data.get("priceChangePercent", 0))
                        high = float(data.get("highPrice", 0))
                        low = float(data.get("lowPrice", 0))

                        result_entry["financials"] = {
                            "son_fiyat": {"fiyat": price, "degisim": change},
                            "s5": 0  # Kriptoda 5Y veri genelde tefas gibi olmaz
                        }
                        result_entry["full_name"] = ticker
                        result_entry["status"] = "Kriter Dışı"  # Kripto İslami Uygunluk Kriteri Dışıdır genellikle
                        
                        result_entry["valuation"] = {
                            "high_52w": high,
                            "low_52w": low,
                            "market_cap": 0
                        }
                    else:
                        logger.warning(f"Binance ticker failed for {clean_symbol}: {res_ticker.status_code}")

                    # 2. Mum Verisi (Historical Klines) — 100 Gün
                    klines_url = f"https://api.binance.com/api/v3/klines?symbol={clean_symbol}&interval=1d&limit=100"
                    res_hist = await client.get(klines_url)
                    if res_hist.status_code == 200:
                        klines = res_hist.json()
                        if isinstance(klines, list):
                            prices_yg = {}
                            klines_data = []

                            for k in klines:
                                try:
                                    t_ms = k[0]
                                    t_sec = int(t_ms / 1000)
                                    date_str = datetime.fromtimestamp(t_sec).strftime("%Y-%m-%d")
                                    close = float(k[4])
                                    
                                    prices_yg[date_str] = close
                                    klines_data.append({
                                        "time": t_sec,  # TV Lightweight Charts saniye türü bekler
                                        "open": float(k[1]),
                                        "high": float(k[2]),
                                        "low": float(k[3]),
                                        "close": close,
                                        "volume": float(k[5])
                                    })
                                except Exception:
                                    continue

                            if "financials" not in result_entry:
                                result_entry["financials"] = {}
                            result_entry["financials"]["yg"] = prices_yg
                            result_entry["klines"] = klines_data  # Mum Grafik Datası
                    else:
                        logger.warning(f"Binance klines failed for {clean_symbol}: {res_hist.status_code}")

            except Exception as e:
                logger.error(f"Crypto fetch exception for {ticker}: {e}")
                if "financials" not in result_entry:
                    result_entry["error"] = f"Kripto veri hatası: {str(e)}"

        try:
            # Stratejiler genellikle ThreadPool'da çalıştığı için asyncio.run güvenlidir
            asyncio.run(fetch_crypto())
        except Exception as e:
            logger.error(f"Crypto Strategy Error for {ticker}: {e}")

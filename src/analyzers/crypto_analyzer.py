import httpx
import logging
from datetime import datetime, timezone
from src.core.analysis_engine import BaseAnalyzerStrategy

logger = logging.getLogger(__name__)

class CryptoAnalyzerStrategy(BaseAnalyzerStrategy):
    """Kripto Para Analiz Stratejisi — Binance API"""
    
    @property
    def name(self): return "crypto"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        market = context.get("market")
        if market != "CRYPTO": return

        try:
            # Binance Formatına Getir (Dash/USD temizle)
            clean_symbol = ticker.upper().replace("-", "").replace("USD", "USDT")
            if "USDT" not in clean_symbol:
                clean_symbol += "USDT"

            with httpx.Client(timeout=10.0) as client:
                # 1. 24s Ticker Verisi (Anlık Fiyat & Değişim)
                ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={clean_symbol}"
                res_ticker = client.get(ticker_url)
                
                if res_ticker.status_code == 200:
                    data = res_ticker.json()
                    price = float(data.get("lastPrice", 0))
                    change = float(data.get("priceChangePercent", 0))

                    result_entry["financials"] = {
                        "son_fiyat": {"fiyat": price, "degisim": change},
                        "s5": 0  # Kriptoda 5Y veri genelde tefas gibi olmaz
                    }
                    result_entry["full_name"] = ticker
                    result_entry["status"] = "Kriter Dışı"  # Kripto İslami Uygunluk Kriteri Dışıdır genellikle
                    
                    result_entry["valuation"] = {
                        "pe": None,
                        "pb": None,
                        "beta": None,
                        "high_52w": 0, # Will be populated by true 100d history
                        "low_52w": 0, 
                        "market_cap": 0
                    }
                else:
                    logger.warning(f"Binance ticker failed for {clean_symbol}: {res_ticker.status_code}")

                # 2. Mum Verisi (Historical Klines) — 100 Gün
                klines_url = f"https://api.binance.com/api/v3/klines?symbol={clean_symbol}&interval=1d&limit=100"
                res_hist = client.get(klines_url)
                if res_hist.status_code == 200:
                    klines = res_hist.json()
                    if isinstance(klines, list):
                        prices_yg = {}
                        klines_data = []
                        highs = []
                        lows = []

                        for i, k in enumerate(klines):
                            try:
                                t_ms = k[0]
                                t_sec = int(t_ms / 1000)
                                date_str = datetime.fromtimestamp(t_sec, tz=timezone.utc).strftime("%Y-%m-%d")
                                
                                open_p = float(k[1])
                                high_p = float(k[2])
                                low_p = float(k[3])
                                close_p = float(k[4])
                                vol = float(k[5])
                                
                                highs.append(high_p)
                                lows.append(low_p)
                                
                                # Yarım Mum Koruması: Sadece kapanmış mumları (en son mum hariç) prices_yg'ye ekle.
                                # (En son mum klines_data için grafik verisi olarak eklenir, ancak AI/Portföy analizini bozmaz)
                                is_last_candle = (i == len(klines) - 1)
                                if not is_last_candle:
                                    prices_yg[date_str] = close_p
                                    
                                klines_data.append({
                                    "time": t_sec,  # TV Lightweight Charts saniye türü bekler
                                    "open": open_p,
                                    "high": high_p,
                                    "low": low_p,
                                    "close": close_p,
                                    "volume": vol
                                })
                            except Exception as parse_e:
                                logger.debug(f"Kripto mum ayrıştırma hatası: {parse_e}")
                                continue

                        if "financials" not in result_entry:
                            result_entry["financials"] = {}
                        result_entry["financials"]["yg"] = prices_yg
                        result_entry["klines"] = klines_data  # Mum Grafik Datası
                        
                        # Gerçek High/Low (100 günlük veriden çekilerek)
                        if "valuation" in result_entry:
                            result_entry["valuation"]["high_52w"] = max(highs) if highs else 0
                            result_entry["valuation"]["low_52w"] = min(lows) if lows else 0
                else:
                    logger.warning(f"Binance klines failed for {clean_symbol}: {res_hist.status_code}")

        except httpx.RequestError as req_e:
            logger.error(f"Crypto fetch network error for {ticker}: {req_e}")
            if "financials" not in result_entry:
                result_entry["error"] = f"Kripto ağ hatası: Bağlantı kurulamadı."
        except Exception as e:
            logger.error(f"Crypto fetch logic exception for {ticker}: {e}")
            if "financials" not in result_entry:
                result_entry["error"] = f"Kripto veri hatası: {str(e)}"

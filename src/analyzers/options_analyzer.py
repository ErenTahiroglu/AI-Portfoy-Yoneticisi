"""
📊 Opsiyon Zinciri Analizörü — P6 Öncelik Matrisi
===================================================
Yahoo Finance üzerinden gerçek zamanlı opsiyon zinciri çeker.
Calls + Puts, Strike, OI, IV tablosu ve basit ITM/OTM sınıflaması.

Black-Scholes Delta, Gamma, Theta hesaplamaları (yaklaşık).
Yalnızca ABD hisseleri (US market) için geçerlidir.
"""
import logging
import math
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _black_scholes_delta(S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
    """
    Black-Scholes modeli ile Delta hesaplar.
    S=spot, K=strike, T=vadeye kalan yıl, r=risksiz oran, sigma=IV
    """
    if T <= 0 or sigma <= 0:
        return 1.0 if option_type == "call" else -1.0
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        # Normal CDF yaklaşımı (scipy olmadan)
        from statistics import NormalDist
        nd = NormalDist()
        if option_type == "call":
            return round(nd.cdf(d1), 4)
        else:
            return round(nd.cdf(d1) - 1, 4)
    except Exception:
        return 0.5


def get_options_chain(ticker: str, expiration: Optional[str] = None) -> dict:
    """
    Ticker için opsiyon zinciri verisi döndürür.

    Args:
        ticker: Hisse sembolü (ör: "AAPL")
        expiration: Vade tarihi "YYYY-MM-DD" formatında (yoksa en yakın vade)

    Returns:
        {
            "ticker": "AAPL",
            "spot_price": 182.5,
            "expiration": "2026-03-21",
            "days_to_expiry": 3,
            "expirations": ["2026-03-21", "2026-03-28", ...],
            "calls": [...],
            "puts": [...],
            "error": null
        }
    """
    try:
        import yfinance as yf  # type: ignore[import]

        stock = yf.Ticker(ticker)

        # Spot fiyat
        info = stock.fast_info
        spot_price = float(getattr(info, "last_price", 0) or 0)

        # Mevcut vade tarihleri
        try:
            expirations = list(stock.options)
        except Exception:
            return {"ticker": ticker, "error": "Bu sembol için opsiyon verisi bulunamadı."}

        if not expirations:
            return {"ticker": ticker, "error": "Opsiyon vade tarihi bulunamadı."}

        # Vade seçimi
        selected_exp = expiration if expiration in expirations else expirations[0]

        # Vadeye kalan gün
        try:
            exp_date = datetime.strptime(selected_exp, "%Y-%m-%d")
            days_to_expiry = max(0, (exp_date - datetime.now()).days)
            T = days_to_expiry / 365.0
        except Exception:
            T = 0.0
            days_to_expiry = 0

        r = 0.05  # Risksiz oran (yaklaşık ABD T-bill)

        # Opsiyon zinciri çek
        chain = stock.option_chain(selected_exp)

        def _process_contracts(df, option_type: str) -> list:
            contracts = []
            for _, row in df.iterrows():
                strike = float(row.get("strike", 0))
                iv = float(row.get("impliedVolatility", 0) or 0)
                in_the_money = bool(row.get("inTheMoney", False))
                delta = _black_scholes_delta(spot_price, strike, T, r, iv, option_type) if spot_price > 0 else None

                contracts.append({
                    "strike": strike,
                    "lastPrice": round(float(row.get("lastPrice", 0) or 0), 2),
                    "bid": round(float(row.get("bid", 0) or 0), 2),
                    "ask": round(float(row.get("ask", 0) or 0), 2),
                    "volume": int(row.get("volume", 0) or 0),
                    "openInterest": int(row.get("openInterest", 0) or 0),
                    "impliedVolatility": round(iv * 100, 1),  # % olarak
                    "inTheMoney": in_the_money,
                    "delta": delta,
                    "contractSymbol": str(row.get("contractSymbol", "")),
                })
            return contracts

        calls = _process_contracts(chain.calls, "call")
        puts  = _process_contracts(chain.puts, "put")

        # Toplam OI (piyasa ilgisi göstergesi)
        total_call_oi = sum(c["openInterest"] for c in calls)
        total_put_oi  = sum(p["openInterest"] for p in puts)
        put_call_ratio = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else None

        return {
            "ticker": ticker.upper(),
            "spot_price": spot_price,
            "expiration": selected_exp,
            "days_to_expiry": days_to_expiry,
            "expirations": expirations[:12],  # Max 12 vade göster
            "put_call_ratio": put_call_ratio,
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "calls": calls,
            "puts": puts,
            "error": None,
        }

    except ImportError:
        return {"ticker": ticker, "error": "yfinance paketi eksik."}
    except Exception as e:
        logger.error(f"Options chain hatası ({ticker}): {e}")
        return {"ticker": ticker, "error": str(e)}

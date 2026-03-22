"""
🧩 Puzzle Parça: Technical Analyzer (Teknik Analiz)
=====================================================
Hisselerin (Fonsuz) teknik analiz metriklerini (RSI, MACD, EMA vb.)
hesaplama ve TradingView-style güç kadranı değerleme (Gauge Score) mantığı.
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def run_technical_indicators(fetcher_ticker: str, result_entry: dict):
    """Teknik göstergeleri hesaplar: RSI 14, MACD 12/26/9, EMA & SMA (20/50/100/200)."""
    try:
        from yahooquery import Ticker
        t = Ticker(fetcher_ticker)
        hist = t.history(period="1y", adj_ohlc=True)
        if hist is None or not isinstance(hist, pd.DataFrame) or hist.empty:
            raise ValueError(f"API boş DataFrame döndürdü: {fetcher_ticker}")
        
        if len(hist) < 30:
            raise ValueError(f"30 günden az veri geldi: {fetcher_ticker}")
        
        # Yahooquery returns MultiIndex (symbol, date)
        try:
            hist = hist.loc[fetcher_ticker]
        except KeyError:
            raise ValueError(f"Beklenen sembol index'te bulunamadı: {fetcher_ticker}")
            
        if hist.empty or len(hist) < 30:
            raise ValueError(f"Sembol filtrelendikten sonra 30 günden az veri kaldı: {fetcher_ticker}")
            
        # Rename columns to match capitalized expectation (Close, Open, High, Low)
        hist.columns = [c.title() for c in hist.columns]
        hist.index = pd.to_datetime(hist.index) # Ensure DatetimeIndex
        
        if "Close" not in hist.columns:
            raise ValueError(f"'Close' kolonu eksik: {fetcher_ticker}")
            
        close = hist["Close"]
        close = close.ffill().dropna()
        
        if close.empty or len(close) < 30:
            raise ValueError(f"Close verisi temizlendikten sonra 30 günden az veri kaldı: {fetcher_ticker}")
            
        technicals = {}
        
        def safe_assign(key, val, precision=2):
            if val is not None and not pd.isna(val) and not np.isinf(val):
                technicals[key] = round(float(val), precision)
        
        # ── RSI 14 ──
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = np.where(loss == 0, 100, rsi)
        rsi = pd.Series(rsi, index=close.index)
        
        if not rsi.empty:
            safe_assign("rsi_14", rsi.iloc[-1])
        
        # ── MACD (12, 26, 9) ──
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - signal_line
        
        if not macd_line.empty:
            safe_assign("macd", macd_line.iloc[-1], 4)
            safe_assign("macd_signal", signal_line.iloc[-1], 4)
            safe_assign("macd_hist", macd_hist.iloc[-1], 4)
        
        # ── EMA (20, 50, 100, 200) ──
        for period in [20, 50, 100, 200]:
            if len(close) >= period:
                ema = close.ewm(span=period, adjust=False).mean()
                safe_assign(f"ema_{period}", ema.iloc[-1])
        
        # ── SMA (20, 50, 100, 200) ──
        for period in [20, 50, 100, 200]:
            if len(close) >= period:
                sma = close.rolling(window=period).mean()
                safe_assign(f"sma_{period}", sma.iloc[-1])
        
        # ── Mevcut fiyat (gösterge referansı) ──
        safe_assign("last_close", close.iloc[-1])
        
        # TradingView-style Technical Gauge Score (0-100)
        gauge_score = 50
        bullish_signals = 0
        total_signals = 0
        
        if "rsi_14" in technicals:
            total_signals += 1
            if technicals["rsi_14"] > 50: bullish_signals += 1
        if "macd_hist" in technicals:
            total_signals += 1
            if technicals["macd_hist"] > 0: bullish_signals += 1
        if "ema_20" in technicals and "last_close" in technicals:
            total_signals += 1
            if technicals["last_close"] > technicals["ema_20"]: bullish_signals += 1
        if "sma_50" in technicals and "last_close" in technicals:
            total_signals += 1
            if technicals["last_close"] > technicals["sma_50"]: bullish_signals += 1
            
        if total_signals > 0:
            gauge_score = int((bullish_signals / total_signals) * 100)
        
        technicals["gauge_score"] = gauge_score

        # ── Signals (Phase 4) ──
        signals = []
        if "rsi_14" in technicals:
            if technicals["rsi_14"] < 30:
                signals.append({"signal": "BULLISH", "reason": "RSI Aşırı Satım Bölgesinde (< 30)"})
            elif technicals["rsi_14"] > 70:
                signals.append({"signal": "BEARISH", "reason": "RSI Aşırı Alım Bölgesinde (> 70)"})

        if len(macd_line) >= 2 and len(signal_line) >= 2:
            prev_macd = macd_line.iloc[-2]
            prev_sig = signal_line.iloc[-2]
            curr_macd = macd_line.iloc[-1]
            curr_sig = signal_line.iloc[-1]
            
            if not (pd.isna(prev_macd) or pd.isna(prev_sig) or pd.isna(curr_macd) or pd.isna(curr_sig)):
                if prev_macd <= prev_sig and curr_macd > curr_sig:
                    signals.append({"signal": "BULLISH", "reason": "MACD Alım Sinyali (Kesişim)"})
                elif prev_macd >= prev_sig and curr_macd < curr_sig:
                    signals.append({"signal": "BEARISH", "reason": "MACD Satım Sinyali (Kesişim)"})

        technicals["signals"] = signals
        
        # Koyfin-style Relative Performance (Stock vs SPY or XU100)
        benchmark_ticker = "XU100.IS" if fetcher_ticker.endswith(".IS") else "SPY"
        try:
            bm_t = Ticker(benchmark_ticker)
            bm_hist = bm_t.history(period="1y", adj_ohlc=True)
            if isinstance(bm_hist, pd.DataFrame) and not bm_hist.empty:
                bm_hist = bm_hist.loc[benchmark_ticker]
                bm_hist.columns = [c.title() for c in bm_hist.columns]
                bm_hist.index = pd.to_datetime(bm_hist.index)
                bm_close = bm_hist["Close"]
                
                # Align dates
                df = pd.DataFrame({"stock": close, "bm": bm_close}).dropna()
                if len(df) > 30 and df["stock"].iloc[0] > 0 and df["bm"].iloc[0] > 0:
                    # Rebase to 100
                    stock_perf = (df["stock"] / df["stock"].iloc[0]) * 100
                    bm_perf = (df["bm"] / df["bm"].iloc[0]) * 100
                    
                    # Pack into minimal JSON-friendly arrays for the chart
                    # To save space, take weekly data roughly (every 5th day)
                    technicals["relative_performance"] = {
                        "benchmark": benchmark_ticker,
                        "dates": [d.strftime('%Y-%m-%d') for d in df.index[::5]],
                        "stock_history": [round(float(v), 2) for v in stock_perf.iloc[::5]],
                        "bm_history": [round(float(v), 2) for v in bm_perf.iloc[::5]]
                    }
        except Exception as e:
            logger.debug(f"Relative performance fetch failed for {fetcher_ticker} vs {benchmark_ticker}: {e}")
        
        if technicals:
            result_entry["technicals"] = technicals
    except Exception as e:
        logger.debug(f"Technical indicators failed for {fetcher_ticker}: {e}")
        raise

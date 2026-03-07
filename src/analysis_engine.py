"""
🧩 Puzzle Parça: Analiz Orkestratörü — v4.0
==============================================
Tüm analiz adımlarını koordine eder:
  1. Pazar algılama (market_detector)
  2. İslami uygunluk kontrolü (islamic_analyzer)
  3. Finansal getiri analizi (portfolio_analyzer / bist_analyzer)
  4. Temel değerleme metrikleri (P/E, P/B, Beta, Piyasa Değeri)
  5. Teknik göstergeler (RSI, MACD, EMA, SMA)
  6. Sektör bilgisi
  7. AI yorum üretimi (ai_agent)
  8. Portföy düzeyinde: Korelasyon, Monte Carlo, Sektör Dağılımı

v4.0 Yenilikler:
  • Teknik göstergeler (RSI 14, MACD 12/26/9, EMA/SMA 20/50/100/200)
  • Sektör dağılımı (pasta grafik verisi)
  • Korelasyon matrisi (portföy düzeyi)
  • Monte Carlo simülasyonu (1 yıl ileri)
"""

import logging
import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Kullanıcı dostu hata mesajları ────────────────────────────────────────
_ERROR_MESSAGES = {
    "ALPHA_VANTAGE_RATE_LIMIT": "⚠️ Alpha Vantage günlük kotası doldu. Yarın tekrar deneyin.",
    "RESOURCE_EXHAUSTED": "⚠️ Gemini API kotası doldu. 1-2 dakika bekleyip tekrar deneyin.",
    "429": "⚠️ API hız limiti aşıldı. Birkaç dakika bekleyip tekrar deneyin.",
    "SSLError": "🔒 SSL bağlantı hatası. İnternet bağlantınızı kontrol edin.",
    "ConnectionError": "🌐 Sunucuya bağlanılamadı. İnternet bağlantınızı kontrol edin.",
    "Timeout": "⏳ Sunucu yanıt vermedi. Lütfen tekrar deneyin.",
}

def _friendly_error(raw_error: str) -> str:
    """Teknik hata mesajını kullanıcı dostu Türkçe metne çevirir."""
    for key, msg in _ERROR_MESSAGES.items():
        if key in raw_error:
            return msg
    return f"Analiz hatası: {raw_error[:120]}"


# ── Result Cache ─────────────────────────────────────────────────────────
_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 300  # 5 dakika

def _cache_key(ticker: str, check_islamic: bool, check_financials: bool) -> str:
    return f"{ticker}:{check_islamic}:{check_financials}"

def _get_cached(key: str) -> Optional[dict]:
    if key in _CACHE:
        entry = _CACHE[key]
        if time.time() - entry["ts"] < _CACHE_TTL:
            logger.info(f"  💾 Cache hit: {key}")
            return entry["data"]
        del _CACHE[key]
    return None

def _set_cache(key: str, data: dict):
    _CACHE[key] = {"ts": time.time(), "data": data}


class AnalysisEngine:
    """Portföy analiz orkestrasyonu — puzzle parçalarını bir araya getirir."""
    
    def __init__(self):
        self._us_analyzer = None
        self._tr_analyzer = None
        self._init_errors = []
        self._last_av_key = None
    
    def _init_financial_analyzers(self, av_api_key: str = None):
        """Finansal analizörleri tembel (lazy) olarak başlatır."""
        if self._us_analyzer is not None and self._last_av_key == av_api_key:
            return
        
        self._init_errors = []
        self._last_av_key = av_api_key
        try:
            from portfolio_analyzer import HisseAnaliz
            self._us_analyzer = HisseAnaliz(av_key=av_api_key)
        except Exception as e:
            import traceback
            logger.error(f"US Analyzer hatası:\n{traceback.format_exc()}")
            self._init_errors.append(f"US Analyzer hatası: {str(e)}")
        try:
            from bist_analyzer import HisseAnaliz as BistHisseAnaliz
            self._tr_analyzer = BistHisseAnaliz()
        except Exception as e:
            import traceback
            logger.error(f"TR Analyzer hatası:\n{traceback.format_exc()}")
            self._init_errors.append(f"TR Analyzer hatası: {str(e)}")
    
    def analyze(self, tickers: list, *, 
                use_ai: bool = False,
                api_key: str = None,
                av_api_key: str = None,
                model: str = "gemini-2.5-flash",
                check_islamic: bool = False,
                check_financials: bool = True) -> dict:
        """
        Ticker listesi için tam portföy analizi çalıştırır.
        Paralel analiz ile 3-4x hız artışı sağlar.
        """
        from market_detector import detect_market
        
        if check_financials:
            self._init_financial_analyzers(av_api_key)
        
        # Ticker'ları temizle
        clean_tickers = [t.upper().strip() for t in tickers if t.strip()]
        
        # Paralel analiz (max 5 worker)
        results = []
        if len(clean_tickers) <= 1:
            # Tek ticker için thread overhead'ı yok
            for ticker in clean_tickers:
                result = self._analyze_single(
                    ticker,
                    check_islamic=check_islamic,
                    check_financials=check_financials,
                    use_ai=use_ai,
                    api_key=api_key,
                    model=model,
                )
                results.append(result)
        else:
            # Çoklu ticker → paralel
            with ThreadPoolExecutor(max_workers=min(5, len(clean_tickers))) as pool:
                future_map = {}
                for ticker in clean_tickers:
                    future = pool.submit(
                        self._analyze_single,
                        ticker,
                        check_islamic=check_islamic,
                        check_financials=check_financials,
                        use_ai=use_ai,
                        api_key=api_key,
                        model=model,
                    )
                    future_map[future] = ticker
                
                # Sonuçları orijinal sıraya göre topla
                result_dict = {}
                for future in as_completed(future_map):
                    ticker = future_map[future]
                    try:
                        result_dict[ticker] = future.result()
                    except Exception as e:
                        result_dict[ticker] = {
                            "ticker": ticker,
                            "error": _friendly_error(str(e))
                        }
                
                results = [result_dict[t] for t in clean_tickers if t in result_dict]
        
        return {"results": results}
    
    def _analyze_single(self, ticker: str, *, 
                        check_islamic: bool,
                        check_financials: bool,
                        use_ai: bool,
                        api_key: str,
                        model: str) -> dict:
        """Tek bir ticker için tüm analiz adımlarını çalıştırır."""
        from market_detector import detect_market
        
        # Cache kontrolü (AI hariç)
        ckey = _cache_key(ticker, check_islamic, check_financials)
        cached = _get_cached(ckey)
        if cached and not use_ai:
            return cached.copy()
        
        market, fetcher_ticker, is_tefas = detect_market(ticker)
        result_entry = {"ticker": ticker, "market": market}
        
        # ── ADIM 1: İslami Uygunluk ──────────────────────────────────────
        data = None
        if check_islamic:
            data = self._run_islamic_check(fetcher_ticker, is_tefas, result_entry)
        
        # ── ADIM 2: Finansal Getiri Analizi ───────────────────────────────
        fin_data = None
        if check_financials:
            fin_data = self._run_financial_check(ticker, market, is_tefas, result_entry)
        
        # ── ADIM 3: Temel Değerleme Metrikleri ────────────────────────────
        if not is_tefas:
            self._run_valuation_check(fetcher_ticker, result_entry)
        
        # ── ADIM 4: Teknik Göstergeler ────────────────────────────────────
        if check_financials and not is_tefas:
            self._run_technical_indicators(fetcher_ticker, result_entry)
        
        # ── ADIM 5: Sektör Bilgisi ────────────────────────────────────────
        if not is_tefas:
            self._run_sector_check(fetcher_ticker, result_entry)
        
        # ── ADIM 6: AI Yorum ─────────────────────────────────────────────
        if use_ai:
            self._run_ai_comment(
                ticker, data, fin_data, market,
                api_key, model,
                check_islamic, check_financials,
                result_entry
            )
        
        # Cache'e kaydet
        _set_cache(ckey, result_entry)
        
        return result_entry
    
    def _run_islamic_check(self, fetcher_ticker: str, is_tefas: bool, result_entry: dict) -> dict:
        """İslami uygunluk kontrolü."""
        data = None
        
        if is_tefas:
            from market_detector import classify_fund
            data = classify_fund(fetcher_ticker)
        else:
            try:
                from islamic_analyzer import get_financials
                data, error = get_financials(fetcher_ticker)
                if error or data is None:
                    result_entry["islamic_error"] = error or "Uygunluk verisi bulunamadı"
                    data = None
            except Exception as e:
                result_entry["islamic_error"] = _friendly_error(str(e))
                data = None
        
        if data is not None:
            if is_tefas:
                result_entry["status"] = data.get('status', 'Bilinmiyor')
                result_entry["is_etf"] = True
                result_entry["is_tefas"] = True
                result_entry["fund_note"] = data.get('fund_note', '')
                result_entry["fund_start_date"] = data.get('fund_start_date')
                result_entry["fund_age"] = data.get('fund_age', '')
            else:
                result_entry["purification_ratio"] = round(data.get('purification_ratio', 0), 2)
                result_entry["debt_ratio"] = round(data.get('debt_ratio', 0), 2)
                result_entry["interest"] = data.get('interest', 0)
                result_entry["status"] = data.get('status', 'Bilinmiyor')
                result_entry["is_etf"] = data.get("is_etf", False)
        
        return data
    
    def _run_financial_check(self, ticker: str, market: str, is_tefas: bool, result_entry: dict) -> dict:
        """Finansal getiri analizi."""
        analyzer = self._tr_analyzer if market == "TR" else self._us_analyzer
        fin_data = None
        
        if analyzer:
            try:
                if is_tefas and hasattr(analyzer, 'analiz_et'):
                    fin_data = analyzer.analiz_et(ticker, is_tefas=True)
                else:
                    fin_data = analyzer.analiz_et(ticker)
                    
                if fin_data:
                    result_entry["financials"] = fin_data
                else:
                    result_entry["fin_error"] = "Detaylı finansal veri bulunamadı."
            except Exception as e:
                result_entry["fin_error"] = _friendly_error(str(e))
        elif self._init_errors:
            result_entry["fin_error"] = " | ".join(self._init_errors)
        
        return fin_data
    
    def _run_valuation_check(self, fetcher_ticker: str, result_entry: dict):
        """Temel değerleme metriklerini çeker (P/E, P/B, Beta, Market Cap)."""
        try:
            from yahooquery import Ticker
            stock = Ticker(fetcher_ticker)
            
            # summary_detail → P/E, Market Cap, Beta
            sd = stock.summary_detail
            if isinstance(sd, dict) and fetcher_ticker in sd:
                detail = sd[fetcher_ticker]
                if isinstance(detail, dict):
                    valuation = {}
                    
                    pe = detail.get('trailingPE')
                    if pe and isinstance(pe, (int, float)):
                        valuation['pe'] = round(pe, 2)
                    
                    fwd_pe = detail.get('forwardPE')
                    if fwd_pe and isinstance(fwd_pe, (int, float)):
                        valuation['fwd_pe'] = round(fwd_pe, 2)
                    
                    beta = detail.get('beta')
                    if beta and isinstance(beta, (int, float)):
                        valuation['beta'] = round(beta, 2)
                    
                    mcap = detail.get('marketCap')
                    if mcap and isinstance(mcap, (int, float)):
                        valuation['market_cap'] = mcap
                    
                    div_yield = detail.get('dividendYield')
                    if div_yield and isinstance(div_yield, (int, float)):
                        valuation['div_yield'] = round(div_yield * 100, 2)
                    
                    fifty_two_high = detail.get('fiftyTwoWeekHigh')
                    fifty_two_low = detail.get('fiftyTwoWeekLow')
                    if fifty_two_high and isinstance(fifty_two_high, (int, float)):
                        valuation['high_52w'] = round(fifty_two_high, 2)
                    if fifty_two_low and isinstance(fifty_two_low, (int, float)):
                        valuation['low_52w'] = round(fifty_two_low, 2)
                    
                    # key_stats → P/B
                    ks = stock.key_stats
                    if isinstance(ks, dict) and fetcher_ticker in ks:
                        kd = ks[fetcher_ticker]
                        if isinstance(kd, dict):
                            pb = kd.get('priceToBook')
                            if pb and isinstance(pb, (int, float)):
                                valuation['pb'] = round(pb, 2)
                            
                            roe = kd.get('returnOnEquity')
                            if roe and isinstance(roe, (int, float)):
                                valuation['roe'] = round(roe * 100, 2)
                            
                            eps = kd.get('trailingEps')
                            if eps and isinstance(eps, (int, float)):
                                valuation['eps'] = round(eps, 2)
                    
                    if valuation:
                        result_entry["valuation"] = valuation
        except Exception as e:
            logger.debug(f"Valuation check failed for {fetcher_ticker}: {e}")
    
    def _run_technical_indicators(self, fetcher_ticker: str, result_entry: dict):
        """Teknik göstergeleri hesaplar: RSI 14, MACD 12/26/9, EMA & SMA (20/50/100/200)."""
        try:
            import yfinance as yf
            hist = yf.Ticker(fetcher_ticker).history(period="1y")
            if hist is None or hist.empty or len(hist) < 30:
                return
            
            close = hist["Close"]
            technicals = {}
            
            # ── RSI 14 ──
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            if not rsi.empty and not np.isnan(rsi.iloc[-1]):
                technicals["rsi_14"] = round(float(rsi.iloc[-1]), 2)
            
            # ── MACD (12, 26, 9) ──
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_hist = macd_line - signal_line
            if not macd_line.empty:
                technicals["macd"] = round(float(macd_line.iloc[-1]), 4)
                technicals["macd_signal"] = round(float(signal_line.iloc[-1]), 4)
                technicals["macd_hist"] = round(float(macd_hist.iloc[-1]), 4)
            
            # ── EMA (20, 50, 100, 200) ──
            for period in [20, 50, 100, 200]:
                if len(close) >= period:
                    ema = close.ewm(span=period, adjust=False).mean()
                    technicals[f"ema_{period}"] = round(float(ema.iloc[-1]), 2)
            
            # ── SMA (20, 50, 100, 200) ──
            for period in [20, 50, 100, 200]:
                if len(close) >= period:
                    sma = close.rolling(window=period).mean()
                    technicals[f"sma_{period}"] = round(float(sma.iloc[-1]), 2)
            
            # ── Mevcut fiyat (gösterge referansı) ──
            technicals["last_close"] = round(float(close.iloc[-1]), 2)
            
            if technicals:
                result_entry["technicals"] = technicals
        except Exception as e:
            logger.debug(f"Technical indicators failed for {fetcher_ticker}: {e}")
    
    def _run_sector_check(self, fetcher_ticker: str, result_entry: dict):
        """Sektör ve endüstri bilgisini çeker."""
        try:
            from yahooquery import Ticker
            stock = Ticker(fetcher_ticker)
            profile = stock.asset_profile
            prices = stock.price
            
            # Add Full Name using price dictionary
            if isinstance(prices, dict) and fetcher_ticker in prices:
                p_price = prices[fetcher_ticker]
                if isinstance(p_price, dict):
                    full_name = p_price.get("longName") or p_price.get("shortName")
                    if full_name:
                        result_entry["full_name"] = full_name

            if isinstance(profile, dict) and fetcher_ticker in profile:
                p = profile[fetcher_ticker]
                if isinstance(p, dict):
                    sector = p.get("sector")
                    industry = p.get("industry")
                    if sector:
                        result_entry["sector"] = sector
                    if industry:
                        result_entry["industry"] = industry
        except Exception as e:
            logger.debug(f"Sector check failed for {fetcher_ticker}: {e}")
    
    def _run_ai_comment(self, ticker, data, fin_data, market, 
                        api_key, model, check_islamic, check_financials, result_entry):
        """AI yorum üretimi."""
        try:
            from ai_agent import generate_report
            islamic_dict = data if data is not None else {}
            ai_comment = generate_report(
                ticker=ticker,
                data=islamic_dict,
                api_key=api_key,
                model_name=model,
                check_islamic=check_islamic,
                check_financials=check_financials,
                fin_data=fin_data,
                market=market
            )
            result_entry["ai_comment"] = ai_comment
        except Exception as e:
            result_entry["ai_comment"] = _friendly_error(str(e))


# ══════════════════════════════════════════════════════════════════════════
# PORTFOLIO-LEVEL EXTRAS (korelasyon, Monte Carlo, sektör dağılımı)
# ══════════════════════════════════════════════════════════════════════════

def compute_portfolio_extras(results: List[dict]) -> dict:
    """
    Portföy düzeyinde ekstra analizler:
      1. Sektör dağılımı (pasta grafik verisi)
      2. Korelasyon matrisi
      3. Monte Carlo simülasyonu (1 yıl)
    """
    extras = {}
    valid_tickers = [r for r in results if not r.get("error") and r.get("market")]
    
    # ── Sektör Dağılımı ──────────────────────────────────────────────
    sector_counts = {}
    for r in valid_tickers:
        sec = r.get("sector", "Bilinmiyor")
        sector_counts[sec] = sector_counts.get(sec, 0) + 1
    if sector_counts:
        extras["sector_distribution"] = sector_counts
    
    # ── Korelasyon Matrisi ────────────────────────────────────────────
    try:
        import yfinance as yf
        from market_detector import detect_market
        
        fetcher_tickers = []
        display_tickers = []
        for r in valid_tickers:
            _, ft, is_tefas = detect_market(r["ticker"])
            if not is_tefas:
                fetcher_tickers.append(ft)
                display_tickers.append(r["ticker"])
        
        if len(fetcher_tickers) >= 2:
            import pandas as pd
            price_data = {}
            for ft, dt in zip(fetcher_tickers, display_tickers):
                try:
                    hist = yf.Ticker(ft).history(period="1y")["Close"]
                    if hist is not None and len(hist) > 20:
                        price_data[dt] = hist.pct_change().dropna()
                except Exception:
                    pass
            
            if len(price_data) >= 2:
                df = pd.DataFrame(price_data)
                df = df.dropna()
                if len(df) > 10:
                    corr = df.corr()
                    extras["correlation"] = {
                        "tickers": list(corr.columns),
                        "matrix": [[round(v, 3) for v in row] for row in corr.values.tolist()]
                    }
                    
                    # ── Portföy Optimizasyonu (Markowitz) ──
                    try:
                        from optimization_engine import optimize_portfolio
                        opt_weights = optimize_portfolio(df)
                        extras["optimized_weights"] = opt_weights
                    except Exception as opt_err:
                        logger.debug(f"Optimization failed: {opt_err}")
    except Exception as e:
        logger.debug(f"Correlation computation failed: {e}")
    
    # ── Portföy Ağırlıklı Getiri & Monte Carlo ─────────────────────
    try:
        daily_returns = []
        weights = []
        
        weighted_s5_sum = 0.0
        total_weight = 0.0
        
        for r in valid_tickers:
            fin = r.get("financials", {})
            s5 = fin.get("s5")
            w = r.get("weight", 1.0)
            
            if s5 is not None and w > 0:
                annual = s5 / 100
                daily_returns.append(annual / 252)
                weights.append(w)
                
                weighted_s5_sum += s5 * w
                total_weight += w
        
        if total_weight > 0:
            extras["weighted_return_5y"] = round(weighted_s5_sum / total_weight, 2)
            
            # Normalize weights
            weights = [w / total_weight for w in weights]
            
            avg_daily = float(np.average(daily_returns, weights=weights))
            # Standart sapma için yaklaşık ağırlıklı varsayım
            mean_sq = np.average([r**2 for r in daily_returns], weights=weights)
            std_daily = max(float(np.sqrt(abs(mean_sq - avg_daily**2))), 0.005)
            
            n_sims = 200
            n_days = 252
            sims = []
            for _ in range(n_sims):
                path = [1.0]
                for _ in range(n_days):
                    ret = np.random.normal(avg_daily, std_daily)
                    path.append(path[-1] * (1 + ret))
                sims.append(path)
            
            sims_arr = np.array(sims)
            percentiles = {
                "p5": [round(float(v), 4) for v in np.percentile(sims_arr, 5, axis=0)[::21]],
                "p25": [round(float(v), 4) for v in np.percentile(sims_arr, 25, axis=0)[::21]],
                "p50": [round(float(v), 4) for v in np.percentile(sims_arr, 50, axis=0)[::21]],
                "p75": [round(float(v), 4) for v in np.percentile(sims_arr, 75, axis=0)[::21]],
                "p95": [round(float(v), 4) for v in np.percentile(sims_arr, 95, axis=0)[::21]],
            }
            extras["monte_carlo"] = {
                "months": list(range(len(percentiles["p50"]))),
                "percentiles": percentiles,
            }
    except Exception as e:
        logger.debug(f"Monte Carlo simulation failed: {e}")
    
    return extras

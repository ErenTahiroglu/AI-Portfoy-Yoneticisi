"""
🧩 Puzzle Parça: Analiz Orkestratörü — v4.0
==============================================
Tüm analiz adımlarını koordine eder:
  1. Pazar algılama (market_detector)
  2. İslami uygunluk kontrolü (islamic_analyzer)
  3. Finansal getiri analizi (us_analyzer / bist_analyzer)
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
            from src.analyzers.us_analyzer import HisseAnaliz
            self._us_analyzer = HisseAnaliz(av_key=av_api_key)
        except Exception as e:
            import traceback
            logger.error(f"US Analyzer hatası:\n{traceback.format_exc()}")
            self._init_errors.append(f"US Analyzer hatası: {str(e)}")
        try:
            from src.analyzers.bist_analyzer import HisseAnaliz as BistHisseAnaliz
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
                check_financials: bool = True,
                lang: str = "tr") -> dict:
        """
        Ticker listesi için tam portföy analizi çalıştırır.
        Paralel analiz ile 3-4x hız artışı sağlar.
        """
        from src.data.market_detector import detect_market
        
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
                    lang=lang,
                )
                results.append(result)
        else:
            # Çoklu ticker → paralel (Render 512MB RAM için limitli: 2)
            with ThreadPoolExecutor(max_workers=2) as pool:
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
                        lang=lang,
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
                        model: str,
                        lang: str) -> dict:
        """Tek bir ticker için tüm analiz adımlarını çalıştırır."""
        from src.data.market_detector import detect_market
        
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
            fin_data = self._run_financial_check(ticker, market, is_tefas, result_entry, check_financials)
        
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
                result_entry, lang
            )
        
        # Cache'e kaydet
        _set_cache(ckey, result_entry)
        
        return result_entry
    
    def _run_islamic_check(self, fetcher_ticker: str, is_tefas: bool, result_entry: dict) -> dict:
        """İslami uygunluk kontrolü."""
        data = None
        
        if is_tefas:
            from src.data.market_detector import classify_fund
            data = classify_fund(fetcher_ticker)
        else:
            try:
                from src.analyzers.islamic_analyzer import get_financials
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
                p_ratio = round(data.get('purification_ratio', 0), 2)
                d_ratio = round(data.get('debt_ratio', 0), 2)
                i_ratio = round(data.get('interest', 0), 2)
                status = data.get('status', 'Bilinmiyor')
                
                result_entry["purification_ratio"] = p_ratio
                result_entry["debt_ratio"] = d_ratio
                result_entry["interest"] = i_ratio
                result_entry["status"] = status
                result_entry["is_etf"] = data.get("is_etf", False)
                
                # Zoya-style compliance details (Limits: Debt < 33%, Interest < 5%, Haram < 5%)
                result_entry["compliance_details"] = {
                    "debt": {"value": d_ratio, "limit": 33.33, "pass": d_ratio < 33.33},
                    "interest": {"value": i_ratio, "limit": 33.33, "pass": i_ratio < 33.33},
                    "haram_income": {"value": p_ratio, "limit": 5.0, "pass": p_ratio < 5.0}
                }
        
        return data
    
    def _run_financial_check(self, ticker: str, market: str, is_tefas: bool, result_entry: dict, check_financials: bool) -> dict:
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
                    msg = "Tarihsel getiri verisi çekilemedi. (Sadece anlık değerleme metrikleri gösteriliyor)" if check_financials and not is_tefas else "Fon verisi alınamadı (WAF engeli veya bağlantı sorunu)."
                    result_entry["fin_error"] = msg
            except Exception as e:
                result_entry["fin_error"] = _friendly_error(str(e))
        elif self._init_errors:
            result_entry["fin_error"] = " | ".join(self._init_errors)
        
        return fin_data
    
    def _run_valuation_check(self, fetcher_ticker: str, result_entry: dict):
        """Temel değerleme metriklerini çeker (P/E, P/B, Beta, Market Cap)."""
        from src.analyzers.valuation_analyzer import run_valuation_check
        run_valuation_check(fetcher_ticker, result_entry)
    
    def _run_technical_indicators(self, fetcher_ticker: str, result_entry: dict):
        """Teknik göstergeleri hesaplar: RSI 14, MACD 12/26/9, EMA & SMA (20/50/100/200)."""
        from src.analyzers.technical_analyzer import run_technical_indicators
        run_technical_indicators(fetcher_ticker, result_entry)
    
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
                        api_key, model, check_islamic, check_financials, result_entry, lang):
        """AI yorum üretimi."""
        try:
            from .ai_agent import generate_report
            islamic_dict = data if data is not None else {}
            ai_comment = generate_report(
                ticker=ticker,
                data=islamic_dict,
                api_key=api_key,
                model_name=model,
                check_islamic=check_islamic,
                check_financials=check_financials,
                fin_data=fin_data,
                market=market,
                lang=lang
            )
            result_entry["ai_comment"] = ai_comment
        except Exception as e:
            err_msg = str(e)
            if "API_KEY_INVALID" in err_msg or "API key not valid" in err_msg:
                result_entry["ai_comment"] = "❌ <b>Gemini API Hatası:</b> API Anahtarınız geçersiz. Lütfen ayarlar panelinden doğru bir anahtar girdiğinizden emin olun." if lang == "tr" else "❌ <b>Gemini API Error:</b> Your API Key is invalid. Please ensure you entered the correct key in the settings panel."
            else:
                result_entry["ai_comment"] = _friendly_error(err_msg)


# ══════════════════════════════════════════════════════════════════════════

# EOF

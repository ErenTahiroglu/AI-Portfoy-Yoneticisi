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
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

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


def safe_api_call(func, *args, **kwargs):
    """
    Harici API çağrılarını saran, 3 kez hata durumunda fallback üreten Circuit Breaker.
    """
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            err_str = str(e)
            # 429 Rate Limit veya Timeout tespiti
            if "429" in err_str or "Rate Limit" in err_str or "Too Many Requests" in err_str:
                if attempt == 2: # Son deneme
                    return {"error": "API Limiti Aşıldı (429)", "is_fallback": True}
                time.sleep(1) # 1 saniye bekle ve tekrar dene
            elif attempt == 2:
                return {"error": f"API Hatası: {err_str}", "is_fallback": True}
    return {"error": "Bilinmeyen API Hatası", "is_fallback": True}

def _friendly_error(raw_error: str) -> str:
    """Teknik hata mesajını kullanıcı dostu Türkçe metne çevirir."""
    for key, msg in _ERROR_MESSAGES.items():
        if key in raw_error:
            return msg
    return f"Analiz hatası: {raw_error[:120]}"  # type: ignore[index]


# ── Result Cache (Διανεμημένο Redis → In-Memory Fallback) ────────────────────────────
from src.core.redis_cache import cache_get, cache_set  # type: ignore[import]

_CACHE_TTL = int(os.environ.get("CACHE_TTL_SECONDS", 300))  # Overridable via env


def _cache_key(ticker: str, check_islamic: bool, check_financials: bool) -> str:
    return f"{ticker}:{check_islamic}:{check_financials}"


def _get_cached(key: str) -> Optional[dict]:
    return cache_get(key)


def _set_cache(key: str, data: dict):
    cache_set(key, data, ttl=_CACHE_TTL)



# ── Strategy Pattern & Registry ───────────────────────────────────────────
from abc import ABC, abstractmethod

class BaseAnalyzerStrategy(ABC):
    """Analiz adımları için temel strateji sınıfı."""
    @property
    @abstractmethod
    def name(self) -> str: ...  # pragma: no cover

    @abstractmethod
    def run(self, ticker: str, result_entry: dict, context: dict) -> None: ...  # pragma: no cover

class AnalyzerRegistry:
    """Tüm analiz stratejilerini yöneten registry."""
    def __init__(self):
        self._strategies: List[BaseAnalyzerStrategy] = []

    def register(self, strategy: BaseAnalyzerStrategy):
        self._strategies.append(strategy)

    def get_strategies(self) -> List[BaseAnalyzerStrategy]:
        return self._strategies

# Registry Instance
analyzer_registry = AnalyzerRegistry()

class IslamicAnalyzerStrategy(BaseAnalyzerStrategy):
    @property
    def name(self): return "islamic"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        if not context.get("check_islamic"): return
        fetcher_ticker = context.get("fetcher_ticker")
        is_tefas = context.get("is_tefas")
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
        
        context["islamic_data"] = data
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
                l_ratio = round(data.get('liquidity_ratio', 0), 2)
                status = data.get('status', 'Bilinmiyor')
                
                result_entry["purification_ratio"] = p_ratio
                result_entry["debt_ratio"] = d_ratio
                result_entry["liquidity_ratio"] = l_ratio
                result_entry["status"] = status
                result_entry["is_etf"] = data.get("is_etf", False)
                
                result_entry["compliance_details"] = {
                    "haram_income": {"value": p_ratio, "limit": 5.0, "pass": p_ratio <= 5.0},
                    "debt": {"value": d_ratio, "limit": 30.0, "pass": d_ratio <= 30.0},
                    "liquidity": {"value": l_ratio, "limit": 30.0, "pass": l_ratio <= 30.0}
                }

class FinancialAnalyzerStrategy(BaseAnalyzerStrategy):
    @property
    def name(self): return "financial"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        if not context.get("check_financials"): return
        market = context.get("market")
        is_tefas = context.get("is_tefas")
        engine = context.get("engine")
        
        # OCP Registry ile dinamik eşleştirme
        analyzer = engine._analyzers.get(market) if hasattr(engine, "_analyzers") else None  # type: ignore[union-attr]
        fin_data = None
        
        if analyzer:
            try:
                def _call():
                    if is_tefas and hasattr(analyzer, 'analiz_et'):
                        return analyzer.analiz_et(ticker, is_tefas=True)  # type: ignore[union-attr]
                    return analyzer.analiz_et(ticker)  # type: ignore[union-attr]
                
                fin_data = safe_api_call(_call)
                
                if fin_data:
                    if isinstance(fin_data, dict) and "error" in fin_data:
                        result_entry["fin_error"] = fin_data["error"]
                    else:
                        result_entry["financials"] = fin_data
                        # klines verisini yüzeye (surface) çıkar - Frontend uyumluluğu
                        if isinstance(fin_data, dict) and "klines" in fin_data:
                            result_entry["klines"] = fin_data["klines"]
                else:
                    msg = "Tarihsel getiri verisi çekilemedi. (Sadece anlık değerleme metrikleri gösteriliyor)" if not is_tefas else "Fon verisi alınamadı (WAF engeli veya bağlantı sorunu)."
                    result_entry["fin_error"] = msg
            except Exception as e:
                result_entry["fin_error"] = _friendly_error(str(e))
        elif engine._init_errors:  # type: ignore[union-attr]
            result_entry["fin_error"] = " | ".join(engine._init_errors)  # type: ignore[union-attr]
        
        context["fin_data"] = fin_data

class ValuationAnalyzerStrategy(BaseAnalyzerStrategy):
    @property
    def name(self): return "valuation"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        try:
            is_tefas = context.get("is_tefas", False)
            if is_tefas:
                return # TEFAS fonları için Valuation (P/E, P/B vb.) hesaplanmaz.
                
            from src.analyzers.valuation_analyzer import run_valuation_check
            run_valuation_check(context.get("fetcher_ticker"), result_entry)
        except Exception as e:
            result_entry["valuation_error"] = _friendly_error(str(e))

class TechnicalAnalyzerStrategy(BaseAnalyzerStrategy):
    @property
    def name(self): return "technicals"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        try:
            is_tefas = context.get("is_tefas", False)
            if is_tefas:
                return # TEFAS fonları için mum bazlı Teknik Analiz çalıştırılmaz.
                
            from src.analyzers.technical_analyzer import run_technical_indicators
            run_technical_indicators(context.get("fetcher_ticker"), result_entry)
        except Exception as e:
            result_entry["technical_error"] = _friendly_error(str(e))

class SectorAnalyzerStrategy(BaseAnalyzerStrategy):
    @property
    def name(self): return "sector"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        if context.get("is_tefas"): return
        fetcher_ticker = context.get("fetcher_ticker")
        try:
            from yahooquery import Ticker
            
            def _call():
                stock = Ticker(fetcher_ticker)
                return {
                    "asset_profile": stock.asset_profile,
                    "price": stock.price
                }
                
            res = safe_api_call(_call)
            
            if isinstance(res, dict) and "error" in res:
                result_entry["sector_error"] = res["error"]
                return

            profile = res.get("asset_profile")
            prices = res.get("price")
            
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

class MLAnalyzerStrategy(BaseAnalyzerStrategy):
    @property
    def name(self): return "ml_prediction"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        try:
            is_tefas = context.get("is_tefas", False)
            if is_tefas:
                return # TEFAS fonları için ML tahmini devre dışıdır.

            from src.analyzers.ml_predictor import predict_price
            def _call():
                return predict_price(ticker)
                
            res = safe_api_call(_call)
            
            if isinstance(res, dict):
                if res.get("error"):
                    result_entry["ml_error"] = res["error"]
                elif res.get("enabled"):
                    result_entry["ml_prediction"] = {
                        "direction": res.get("direction"),
                        "confidence": res.get("confidence"),
                        "target_7d": res.get("target_7d"),
                        "change_pct": res.get("change_pct")
                    }
        except Exception as e:
            result_entry["ml_error"] = _friendly_error(str(e))

class AICommentAnalyzerStrategy(BaseAnalyzerStrategy):
    @property
    def name(self): return "ai_comment"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        if not context.get("use_ai"): return
        try:
            from .ai_agent import generate_report
            
            system_errors = {}
            for err_key in ["fin_error", "technical_error", "valuation_error", "islamic_error", "sector_error", "ml_error"]:
                if err_key in result_entry:
                    system_errors[err_key] = result_entry[err_key]
                    
            islamic_dict = context.get("islamic_data") if context.get("islamic_data") is not None else {}
            ai_comment = generate_report(
                ticker=ticker,
                data=islamic_dict,
                api_key=context.get("api_key"),
                model_name=context.get("model"),
                check_islamic=context.get("check_islamic"),
                check_financials=context.get("check_financials"),
                fin_data=context.get("fin_data"),
                market=context.get("market"),
                lang=context.get("lang"),
                system_errors=system_errors,
                ml_prediction=result_entry.get("ml_prediction")
            )
            result_entry["ai_comment"] = ai_comment
        except Exception as e:
            err_msg = str(e)
            lang = context.get("lang")
            if "API_KEY_INVALID" in err_msg or "API key not valid" in err_msg:
                result_entry["ai_comment"] = "❌ <b>Gemini API Hatası:</b> API Anahtarınız geçersiz. Lütfen ayarlar panelinden doğru bir anahtar girdiğinizden emin olun." if lang == "tr" else "❌ <b>Gemini API Error:</b> Your API Key is invalid. Please ensure you entered the correct key in the settings panel."
            else:
                result_entry["ai_comment"] = _friendly_error(err_msg)

class SentimentAnalyzerStrategy(BaseAnalyzerStrategy):
    @property
    def name(self): return "sentiment"

    def run(self, ticker: str, result_entry: dict, context: dict) -> None:
        try:
            from src.data.news_fetcher import fetch_recent_news_async
            from .ai_agent import analyze_news_sentiment
            import asyncio

            async def _get_sentiment():
                news = await fetch_recent_news_async(ticker)
                if not news: return None
                return analyze_news_sentiment(
                    news_data=news,
                    check_islamic=context.get("check_islamic", False),
                    api_key=context.get("api_key"),
                    model_name=context.get("model", "gemini-2.5-flash"),
                    lang=context.get("lang", "tr")
                )

            loop = asyncio.new_event_loop()
            try:
                sentiment_data = loop.run_until_complete(_get_sentiment())
                if sentiment_data:
                    result_entry["sentiment"] = sentiment_data
            finally:
                loop.close()
        except Exception as e:
            logger.debug(f"Sentiment analysis failed for {ticker}: {e}")

def register_default_strategies():
    from src.analyzers.crypto_analyzer import CryptoAnalyzerStrategy
    
    # Register Default Strategies
    analyzer_registry.register(CryptoAnalyzerStrategy())
    analyzer_registry.register(IslamicAnalyzerStrategy())
    analyzer_registry.register(FinancialAnalyzerStrategy())
    analyzer_registry.register(ValuationAnalyzerStrategy())
    analyzer_registry.register(TechnicalAnalyzerStrategy())
    analyzer_registry.register(SectorAnalyzerStrategy())
    analyzer_registry.register(MLAnalyzerStrategy())
    analyzer_registry.register(AICommentAnalyzerStrategy())
    analyzer_registry.register(SentimentAnalyzerStrategy())

# Strategies will be registered dynamically or lazy inside AnalysisEngine.__init__


class AnalysisEngine:
    """Portföy analiz orkestrasyonu — puzzle parçalarını bir araya getirir."""
    
    def __init__(self):
        self._analyzers: dict = {}  # Analyzer Registry
        self._init_errors: list = []
        self._last_av_key: Optional[str] = None
        
        # Register strategies (Already defined above)
        register_default_strategies()
    
    def _init_financial_analyzers(self, av_api_key: Optional[str] = None):
        """Finansal analizörleri tembel (lazy) olarak başlatır."""
        if self._analyzers and self._last_av_key == av_api_key:
            return
            
        self._init_errors = []
        self._last_av_key = av_api_key
        self._analyzers = {}
        
        try:
            from src.analyzers.us_analyzer import HisseAnaliz as UsAnaliz
            from src.analyzers.bist_analyzer import HisseAnaliz as BistAnaliz
            
            instances = [UsAnaliz(av_key=av_api_key), BistAnaliz()]
            for a in instances:
                code = getattr(a, "market_code", None)
                if code:
                    self._analyzers[code] = a
                    
        except Exception as e:
            import traceback
            logger.error(f"Analyzer yükleme hatası:\n{traceback.format_exc()}")
            self._init_errors.append(f"Finansal analizör yükleme hatası: {str(e)}")
    
    def analyze(self, tickers: list, *, 
                use_ai: bool = False,
                api_key: Optional[str] = None,
                av_api_key: Optional[str] = None,
                model: str = "gemini-2.5-flash",
                check_islamic: bool = False,
                check_financials: bool = True,
                lang: str = "tr") -> dict:
        """
        Ticker listesi için tam portföy analizi çalıştırır.
        Paralel analiz ile 3-4x hız artışı sağlar.
        """
        
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
                    future = pool.submit(  # type: ignore[arg-type]
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
                        api_key: Optional[str],
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
        
        # Frontend Felci İçin Varsayılan Değerler (Fallback)
        result_entry["radar_score"] = {"profitability": 50, "value": 50, "growth": 50, "debt": 50}
        result_entry["technicals"] = {"gauge_score": 50}
        result_entry["financials"] = {"son_fiyat": {"fiyat": 0.0, "degisim": 0.0, "tarih": ""}, "yg": {}}
        result_entry["valuation"] = {"market_cap": 0, "pe": None, "pb": None, "peg": None, "beta": None, "high_52w": 0, "low_52w": 0}
        result_entry["ml_prediction"] = {"direction": "SIDEWAYS", "confidence": 50, "target_7d": 0, "change_pct": 0}
        result_entry["klines"] = []
        
        # Strateji Bağlamı (Context)
        context = {
            "engine": self,
            "check_islamic": check_islamic,
            "check_financials": check_financials,
            "use_ai": use_ai,
            "api_key": api_key,
            "model": model,
            "lang": lang,
            "market": market,
            "fetcher_ticker": fetcher_ticker,
            "is_tefas": is_tefas
        }
        
        # Stratejileri Sırayla Çalıştır
        for strategy in analyzer_registry.get_strategies():
            strategy.run(ticker, result_entry, context)
        
        # Cache'e kaydet
        _set_cache(ckey, result_entry)
        
        return result_entry


# ══════════════════════════════════════════════════════════════════════════

# EOF

"""
🧩 Puzzle Parça: Analiz Orkestratörü
======================================
Tüm analiz adımlarını koordine eder:
  1. Pazar algılama (market_detector)
  2. İslami uygunluk kontrolü (islamic_analyzer)
  3. Finansal getiri analizi (portfolio_analyzer / bist_analyzer)
  4. AI yorum üretimi (ai_agent)

main.py sadece HTTP endpoint'lerini tanımlar, iş mantığı burada yaşar.

Kullanım:
    from analysis_engine import AnalysisEngine
    engine = AnalysisEngine()
    results = engine.analyze(tickers, options)
"""

import logging

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """Portföy analiz orkestrasyonu — puzzle parçalarını bir araya getirir."""
    
    def __init__(self):
        self._us_analyzer = None
        self._tr_analyzer = None
        self._init_errors = []
        self._last_av_key = None  # Aynı key ile yeniden oluşturmayı engelle
    
    def _init_financial_analyzers(self, av_api_key: str = None):
        """Finansal analizörleri tembel (lazy) olarak başlatır.
        AV key değişmediyse mevcut instance'ları tekrar kullanır."""
        # Zaten başlatılmışsa ve key aynıysa → atla
        if self._us_analyzer is not None and self._last_av_key == av_api_key:
            return
        
        self._init_errors = []
        self._last_av_key = av_api_key
        try:
            from portfolio_analyzer import HisseAnaliz
            self._us_analyzer = HisseAnaliz(av_key=av_api_key)
        except Exception as e:
            self._init_errors.append(f"US Analyzer hatası: {str(e)}")
        try:
            from bist_analyzer import HisseAnaliz as BistHisseAnaliz
            self._tr_analyzer = BistHisseAnaliz()
        except Exception as e:
            self._init_errors.append(f"TR Analyzer hatası: {str(e)}")
    
    def analyze(self, tickers: list, *, 
                use_ai: bool = False,
                api_key: str = None,
                av_api_key: str = None,
                model: str = "gemini-2.5-flash",
                check_islamic: bool = True,
                check_financials: bool = True) -> dict:
        """
        Ticker listesi için tam portföy analizi çalıştırır.
        
        Returns:
            {"results": [ {ticker, market, status?, financials?, ai_comment?, ...}, ... ]}
        """
        from market_detector import detect_market, classify_fund
        
        # Finansal analizörleri başlat (gerekiyorsa)
        if check_financials:
            self._init_financial_analyzers(av_api_key)
        
        results = []
        
        for ticker in tickers:
            ticker = ticker.upper().strip()
            if not ticker:
                continue
            
            result = self._analyze_single(
                ticker,
                check_islamic=check_islamic,
                check_financials=check_financials,
                use_ai=use_ai,
                api_key=api_key,
                model=model,
            )
            results.append(result)
        
        return {"results": results}
    
    def _analyze_single(self, ticker: str, *, 
                        check_islamic: bool,
                        check_financials: bool,
                        use_ai: bool,
                        api_key: str,
                        model: str) -> dict:
        """Tek bir ticker için tüm analiz adımlarını çalıştırır."""
        from market_detector import detect_market, classify_fund
        
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
        
        # ── ADIM 3: AI Yorum ─────────────────────────────────────────────
        if use_ai:
            self._run_ai_comment(
                ticker, data, fin_data, market,
                api_key, model,
                check_islamic, check_financials,
                result_entry
            )
        
        return result_entry
    
    def _run_islamic_check(self, fetcher_ticker: str, is_tefas: bool, result_entry: dict) -> dict:
        """İslami uygunluk kontrolü — TEFAS fonları ve hisseler ayrı yollardan işlenir."""
        data = None
        
        if is_tefas:
            from market_detector import classify_fund
            data = classify_fund(fetcher_ticker)
        else:
            try:
                from islamic_analyzer import get_financials
                data, error = get_financials(fetcher_ticker)
                if error or data is None:
                    result_entry["islamic_error"] = error or "İslami veri bulunamadı"
                    data = None
            except Exception as e:
                result_entry["islamic_error"] = f"İslami analiz hatası: {str(e)}"
                data = None
        
        # Sonuçları result_entry'ye yaz
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
        """Finansal getiri analizi — uygun analizörü seçer ve çalıştırır."""
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
                    result_entry["fin_error"] = "Hisse için detaylı finansal veri kurulamadı."
            except Exception as e:
                if str(e) == "ALPHA_VANTAGE_RATE_LIMIT":
                    result_entry["fin_error"] = "⚠️ Alpha Vantage Kotası Doldu. Yarın tekrar deneyin."
                else:
                    result_entry["fin_error"] = f"Finans modülü hatası: {str(e)}"
        elif self._init_errors:
            result_entry["fin_error"] = " | ".join(self._init_errors)
        
        return fin_data
    
    def _run_ai_comment(self, ticker, data, fin_data, market, 
                        api_key, model, check_islamic, check_financials, result_entry):
        """AI yorum üretimi — mevcut verileri Gemini'ye gönderir."""
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
            result_entry["ai_comment"] = f"API Error: {str(e)}"

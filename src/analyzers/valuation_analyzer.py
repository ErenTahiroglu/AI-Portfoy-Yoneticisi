"""
🧩 Puzzle Parça: Valuation Analyzer (Temel Değerleme)
=====================================================
Hisselerin (Fonsuz) Temel Analiz metriklerini (P/E, P/B, Beta vb.)
çekme ve Fintables-style finansal sağlık skorlaması üretme mantığı.
"""

import logging

import math

logger = logging.getLogger(__name__)

def run_valuation_check(fetcher_ticker: str, result_entry: dict):
    """Temel değerleme metriklerini çeker (P/E, P/B, Beta, Market Cap) ve skora çevirir."""
    # Güvenli Başlatma
    valuation = {}
    financial_health = {"profitability": 50, "value": 50, "growth": 50, "debt": 50}
    
    try:
        from yahooquery import Ticker
        stock = Ticker(fetcher_ticker)
        
        def is_valid_num(v):
            return isinstance(v, (int, float)) and not math.isnan(v) and not math.isinf(v)

        # summary_detail → P/E, Market Cap, Beta
        sd = stock.summary_detail
        if isinstance(sd, dict) and fetcher_ticker in sd:
            detail = sd[fetcher_ticker]
            if isinstance(detail, dict):
                pe = detail.get('trailingPE')
                if is_valid_num(pe): valuation['pe'] = round(pe, 2)
                
                fwd_pe = detail.get('forwardPE')
                if is_valid_num(fwd_pe): valuation['fwd_pe'] = round(fwd_pe, 2)
                
                beta = detail.get('beta')
                if is_valid_num(beta): valuation['beta'] = round(beta, 2)
                
                mcap = detail.get('marketCap')
                if is_valid_num(mcap): valuation['market_cap'] = mcap
                
                div_yield = detail.get('dividendYield')
                if is_valid_num(div_yield): valuation['div_yield'] = round(div_yield * 100, 2)
                
                fifty_two_high = detail.get('fiftyTwoWeekHigh')
                fifty_two_low = detail.get('fiftyTwoWeekLow')
                if is_valid_num(fifty_two_high): valuation['high_52w'] = round(fifty_two_high, 2)
                if is_valid_num(fifty_two_low): valuation['low_52w'] = round(fifty_two_low, 2)
                
        # key_stats → P/B, ROE, EPS
        ks = stock.key_stats
        if isinstance(ks, dict) and fetcher_ticker in ks:
            kd = ks[fetcher_ticker]
            if isinstance(kd, dict):
                pb = kd.get('priceToBook')
                if is_valid_num(pb): valuation['pb'] = round(pb, 2)
                
                roe = kd.get('returnOnEquity')
                if is_valid_num(roe): valuation['roe'] = round(roe * 100, 2)
                
                eps = kd.get('trailingEps')
                if is_valid_num(eps): valuation['eps'] = round(eps, 2)

        # Fintables-style Radar Scores (0-100)
        # 1. Profitability (ROE based)
        if 'roe' in valuation:
            roe_val = valuation['roe']
            if roe_val > 25: financial_health['profitability'] = 90
            elif roe_val > 15: financial_health['profitability'] = 75
            elif roe_val > 0: financial_health['profitability'] = 50
            else: financial_health['profitability'] = 20
            
        # 2. Value (P/E based)
        if 'pe' in valuation:
            pe_val = valuation['pe']
            if 0 < pe_val < 10: financial_health['value'] = 90
            elif 10 <= pe_val < 20: financial_health['value'] = 70
            elif pe_val >= 20: financial_health['value'] = 40
            else: financial_health['value'] = 10 # Negative P/E
            
        # 3. Growth (EPS based simple proxy)
        if 'eps' in valuation:
            eps_val = valuation['eps']
            if eps_val > 5: financial_health['growth'] = 85
            elif eps_val > 1: financial_health['growth'] = 60
            elif eps_val > 0: financial_health['growth'] = 40
            else: financial_health['growth'] = 15

    except Exception as e:
        logger.debug(f"Valuation check failed for {fetcher_ticker}: {e}")
        
    # Her ihtimale karşı re-populate
    result_entry["valuation"] = valuation
    result_entry["radar_score"] = financial_health

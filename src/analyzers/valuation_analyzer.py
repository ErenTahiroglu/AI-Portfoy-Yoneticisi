"""
🧩 Puzzle Parça: Valuation Analyzer (Temel Değerleme)
=====================================================
Hisselerin (Fonsuz) Temel Analiz metriklerini (P/E, P/B, Beta vb.)
çekme ve Fintables-style finansal sağlık skorlaması üretme mantığı.
"""

import logging

logger = logging.getLogger(__name__)

def run_valuation_check(fetcher_ticker: str, result_entry: dict):
    """Temel değerleme metriklerini çeker (P/E, P/B, Beta, Market Cap) ve skora çevirir."""
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
                
                # key_stats → P/B, ROE, EPS
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
                
                # Fintables-style Radar Scores (0-100)
                financial_health = {}
                
                # 1. Profitability (ROE based)
                roe_val = valuation.get('roe', 0)
                if roe_val > 25: financial_health['profitability'] = 90
                elif roe_val > 15: financial_health['profitability'] = 75
                elif roe_val > 0: financial_health['profitability'] = 50
                else: financial_health['profitability'] = 20
                
                # 2. Value (P/E based)
                pe_val = valuation.get('pe', 0)
                if 0 < pe_val < 10: financial_health['value'] = 90
                elif 10 <= pe_val < 20: financial_health['value'] = 70
                elif pe_val >= 20: financial_health['value'] = 40
                else: financial_health['value'] = 10 # Negative P/E
                
                # 3. Growth (EPS based simple proxy)
                eps_val = valuation.get('eps', 0)
                if eps_val > 5: financial_health['growth'] = 85
                elif eps_val > 1: financial_health['growth'] = 60
                elif eps_val > 0: financial_health['growth'] = 40
                else: financial_health['growth'] = 15
                
                # 4. Debt (Will be updated globally if islamic check runs, else neutral)
                financial_health['debt'] = 50
                
                result_entry["valuation"] = valuation
                result_entry["radar_score"] = financial_health

    except Exception as e:
        logger.debug(f"Valuation check failed for {fetcher_ticker}: {e}")

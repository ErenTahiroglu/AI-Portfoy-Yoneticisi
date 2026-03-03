import os
import tempfile
import certifi
import shutil
import pandas as pd
import functools
from yahooquery import Ticker

# --- SSL/CURL SERTİFİKA HATASI KESİN ÇÖZÜMÜ ---
temp_dir = tempfile.gettempdir()
temp_cert_path = os.path.join(temp_dir, 'cacert.pem')

if not os.path.exists(temp_cert_path):
    shutil.copy2(certifi.where(), temp_cert_path)

os.environ['CURL_CA_BUNDLE'] = temp_cert_path
os.environ['REQUESTS_CA_BUNDLE'] = temp_cert_path
os.environ['SSL_CERT_FILE'] = temp_cert_path

def _get_single_stock_data(ticker):
    """Tekil bir hissenin verilerini bulur (Döngü için yardımcı fonksiyon)"""
    try:
        stock = Ticker(ticker)
        inc = stock.income_statement()
        bal = stock.balance_sheet()
        
        if isinstance(inc, str) or isinstance(inc, dict) or inc.empty: 
            return None
        if isinstance(bal, str) or isinstance(bal, dict) or bal.empty: 
            return None
            
        inc, bal = inc.reset_index(), bal.reset_index()
        if 'asOfDate' in inc.columns: 
            inc = inc.sort_values('asOfDate', ascending=False)
        if 'asOfDate' in bal.columns: 
            bal = bal.sort_values('asOfDate', ascending=False)
        
        def get_val(series, keys):
            for k in keys:
                if k in series and pd.notna(series[k]): 
                    return float(series[k])
            return 0.0

        interest_keys = [
            'InterestIncome', 'InterestIncomeNonOperating', 'NetInterestIncome',
            'InterestExpense', 'InterestExpenseNonOperating',
            'NetNonOperatingInterestIncomeExpense'
        ]

        revenue, interest_income, inc_date = 0.0, 0.0, "Bilinmiyor"
        for _, row in inc.iterrows():
            rev = get_val(row, ['TotalRevenue', 'OperatingRevenue'])
            if rev > 0:
                revenue = rev
                interest_income = get_val(row, interest_keys)
                inc_date = str(row.get('asOfDate', 'Bilinmiyor')).split(' ')[0]
                break
        
        # Fallback: if quarterly interest is 0, try annual income statement
        if interest_income == 0.0:
            try:
                inc_annual = stock.income_statement(frequency='a')
                if isinstance(inc_annual, pd.DataFrame) and not inc_annual.empty:
                    inc_annual = inc_annual.reset_index().sort_values('asOfDate', ascending=False)
                    for _, row in inc_annual.iterrows():
                        val = get_val(row, interest_keys)
                        if val != 0.0:
                            interest_income = val
                            break
            except Exception:
                pass
                
        # Use absolute value: some companies report interest as negative expense
        interest_income = abs(interest_income)
        
        total_assets, total_debt, bal_date = 0.0, 0.0, "Bilinmiyor"
        for _, row in bal.iterrows():
            ast = get_val(row, ['TotalAssets'])
            if ast > 0:
                total_assets = ast
                total_debt = get_val(row, ['TotalDebt'])
                if total_debt == 0:
                    total_debt = get_val(row, ['CurrentDebt', 'ShortTermDebt']) + get_val(row, ['LongTermDebt'])
                bal_date = str(row.get('asOfDate', 'Bilinmiyor')).split(' ')[0]
                break
            
        if revenue == 0 or total_assets == 0: 
            return None
            
        return {
            "purification_ratio": (interest_income / revenue) * 100,
            "debt_ratio": (total_debt / total_assets) * 100,
            "revenue": revenue, "interest": interest_income,
            "assets": total_assets, "debt": total_debt,
            "inc_date": inc_date, "bal_date": bal_date
        }
    except Exception:
        return None

@functools.lru_cache(maxsize=128)
def get_financials(ticker):
    """Yahoo API üzerinden bilançoları çeker. ETF ise içindeki hisseleri tarar."""
    try:
        stock = Ticker(ticker)
        inc = stock.income_statement()
        
        is_etf = False
        holdings_df = None
        
        # 1. Aşama: ETF mi (Gelir Tablosu Boş mu) Kontrolü
        if isinstance(inc, str) or isinstance(inc, dict) or inc.empty:
            try:
                holdings_df = stock.fund_top_holdings
                if isinstance(holdings_df, pd.DataFrame) and not holdings_df.empty:
                    is_etf = True
            except Exception:
                pass
            
            if not is_etf:
                return None, f"Veri bulunamadı. ({ticker})"
                
        # 2. Aşama: EĞER ETF İSE İÇİNİ TARAMA MANTIĞI
        if is_etf:
            df = holdings_df
            if not isinstance(df, pd.DataFrame):
                return None, f"Veri bulunamadı. ({ticker})"
                
            if 'symbol' not in getattr(df, 'columns', []):
                df = df.reset_index()
            
            valid_holdings = []
            total_valid_weight = 0.0
            
            # Fonun içindeki en büyük ağırlığa sahip şirketleri tek tek tarar
            for _, row in df.iterrows():
                sub_ticker = row.get('symbol')
                if not isinstance(sub_ticker, str): 
                    continue
                
                weight = float(row.get('holdingPercent', 0))
                if weight <= 0: 
                    continue
                
                sub_data = _get_single_stock_data(sub_ticker)
                if sub_data:
                    valid_holdings.append({
                        "symbol": sub_ticker, "weight": weight,
                        "pur_ratio": sub_data['pur_ratio'] if 'pur_ratio' in sub_data else sub_data.get('purification_ratio', 0),
                        "debt_ratio": sub_data['debt_ratio']
                    })
                    total_valid_weight += weight
                    
            if not valid_holdings:
                return None, f"ETF ({ticker}) içindeki şirketlerin bilançolarına ulaşılamadı."
                
            # Ağırlıklı Ortalamaları Hesapla
            agg_pur, agg_debt, holdings_str = 0.0, 0.0, ""
            
            for h in valid_holdings:
                normalized_weight = h['weight'] / total_valid_weight
                agg_pur += h['pur_ratio'] * normalized_weight
                agg_debt += h['debt_ratio'] * normalized_weight
                holdings_str += f"{h['symbol']}|%{h['weight']*100:.2f}|%{h['pur_ratio']:.2f}|%{h['debt_ratio']:.2f}\n"
                
            is_halal = "Uygun" if (agg_pur <= 5.0 and agg_debt <= 30.0) else "Uygun Değil"
            
            return {
                "is_etf": True,
                "revenue": 0, "interest": 0, "assets": 0, "debt": 0, # ETF toplamı
                "purification_ratio": agg_pur, "debt_ratio": agg_debt,
                "status": is_halal, "holdings_str": holdings_str,
                "inc_date": "Fon Ağırlıklı Veri", "bal_date": "Fon Ağırlıklı Veri"
            }, None
            
        else:
            data = _get_single_stock_data(ticker)
            if not data:
                return None, f"Eksik veri. Güncel rakamlar yayınlanmamış. ({ticker})"
            
            # Tip uyuşmazlığını önlemek için yeni bir sözlük oluşturuyoruz.
            purification = float(data.get('purification_ratio', 0.0))
            debt = float(data.get('debt_ratio', 0.0))
            
            result_data = {
                "is_etf": False,
                "status": "Uygun" if (purification <= 5.0 and debt <= 30.0) else "Uygun Değil",
                "purification_ratio": purification,
                "debt_ratio": debt,
                "revenue": data.get("revenue", 0.0),
                "interest": data.get("interest", 0.0),
                "assets": data.get("assets", 0.0),
                "debt": data.get("debt", 0.0),
                "inc_date": data.get("inc_date", "Bilinmiyor"),
                "bal_date": data.get("bal_date", "Bilinmiyor")
            }
            return result_data, None

    except Exception as e:
        return None, f"Sistem hatası: {str(e)}"
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def run_portfolio_simulation(
    price_df: pd.DataFrame, 
    weights_map: dict, 
    initial_balance: float = 10000.0, 
    monthly_contribution: float = 0.0, 
    rebalancing_freq: str = "none",
    risk_free_rate: float = 0.02
) -> dict:
    """
    Runs a historical backtest for a portfolio given daily prices and parameters.
    Returns tracking history, advanced risk metrics (Sortino, Treynor, Max DD, Calmar).
    """
    if price_df.empty or not weights_map:
        return {}
        
    # Sadece portföyde ağırlığı 0'dan büyük olan varlıkları al
    active_tickers = [t for t, w in weights_map.items() if w > 0 and t in price_df.columns]
    if not active_tickers:
        return {}
        
    df = price_df[active_tickers].copy()
    
    # Zaman Hizalaması ve Boşluk Doldurma (Sadece ileriye dönük)
    df.ffill(inplace=True)
    # Ortak tarih aralığına kırp (En genç varlığın halka arzından itibaren başlar)
    df.dropna(inplace=True)
    
    # 20 Günden az veri varsa simülasyonu iptal et
    if len(df) < 20:
        logger.warning(f"run_portfolio_simulation: Yetersiz ortak tarihsel veri ({len(df)} gün). Simülasyon iptal edildi.")
        return {}
    
    # Normalize weights to sum to 1.0
    total_w = sum(weights_map[t] for t in active_tickers)
    target_weights = {t: weights_map[t]/total_w for t in active_tickers}
    
    # Aydan aya gruplama için
    df['YearMonth'] = df.index.year.astype(str) + "-" + df.index.month.astype(str).str.zfill(2)
    end_of_month_dates = df.groupby('YearMonth').apply(lambda x: x.index[-1]).values
    
    # Başlangıç değerleri
    current_balances = {t: initial_balance * target_weights[t] for t in active_tickers}
    
    history = []
    daily_values = []
    
    # Başlangıç bakiyesini ilk gün olarak ekle
    daily_values.append(sum(current_balances.values()))
    
    last_rebalance_month = df.index[0].month
    
    for prev_date, curr_date in zip(df.index[:-1], df.index[1:]):
        # 1. Fiyat değişimi (günlük)
        for t in active_tickers:
            prev_price = df.loc[prev_date, t]
            curr_price = df.loc[curr_date, t]
            if prev_price > 0:
                ret = (curr_price - prev_price) / prev_price
                current_balances[t] *= (1 + ret)
                
        total_val = sum(current_balances.values())
        daily_values.append(total_val)
        
        # 2. Ay sonu işlemleri (Nakit Akışı ve Rebalance)
        if curr_date in end_of_month_dates:
            # Aylık ekleme/çıkarma
            if monthly_contribution != 0:
                for t in active_tickers:
                    current_balances[t] += monthly_contribution * target_weights[t]
                total_val = sum(current_balances.values())
            
            # Rebalance
            do_rebalance = False
            if rebalancing_freq == "monthly":
                do_rebalance = True
            elif rebalancing_freq == "quarterly" and curr_date.month % 3 == 0:
                do_rebalance = True
            elif rebalancing_freq == "yearly" and curr_date.month == 12:
                do_rebalance = True
                
            if do_rebalance and total_val > 0:
                current_balances = {t: total_val * target_weights[t] for t in active_tickers}
                
            history.append({
                "date": curr_date.strftime("%Y-%m-%d"),
                "balance": round(total_val, 2)
            })

    # Son günü ekle (eğer ay sonu değilse bile)
    final_val = sum(current_balances.values())
    if not history or history[-1]["date"] != df.index[-1].strftime("%Y-%m-%d"):
         history.append({
            "date": df.index[-1].strftime("%Y-%m-%d"),
            "balance": round(final_val, 2)
        })
    
    # Günlük getiriler üzerinden risk metriklerini hesapla
    daily_s = pd.Series(daily_values)
    port_returns = daily_s.pct_change().dropna()
    
    metrics = calculate_advanced_metrics(port_returns, risk_free_rate)
    
    return {
        "history": history,
        "metrics": metrics,
        "final_balance": round(final_val, 2)
    }


def calculate_advanced_metrics(returns: pd.Series, risk_free_rate: float = 0.02) -> dict:
    """Gelişmiş risk metriklerini hesaplar: Max Drawdown, Sortino, Calmar, Treynor"""
    if returns.empty:
        return {}
        
    annual_rf_daily = risk_free_rate / 252
    
    # 1. CAGR (Yıllıklandırılmış Getiri)
    n_years = len(returns) / 252.0
    if n_years > 0:
        total_ret = (1 + returns).prod() - 1
        cagr = (1 + total_ret) ** (1 / n_years) - 1
    else:
        cagr = 0
        
    # 2. Volatilite (Yıllık)
    volatility = returns.std() * np.sqrt(252)
    
    # 3. Sharpe
    excess_ret = returns.mean() - annual_rf_daily
    sharpe = (excess_ret * 252) / volatility if volatility > 0 else 0
    
    # 4. Sortino
    neg_returns = returns[returns < 0]
    downside_std = neg_returns.std() * np.sqrt(252)
    sortino = (excess_ret * 252) / downside_std if downside_std > 0 else 0
    
    # 5. Max Drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_dd = drawdown.min()
    
    # 6. Calmar Oranı
    calmar = cagr / abs(max_dd) if abs(max_dd) > 0 else 0
    
    return {
        "cagr": round(cagr * 100, 2),
        "volatility": round(volatility * 100, 2),
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "max_drawdown": round(max_dd * 100, 2),
        "calmar": round(calmar, 2),
        "drawdown_series": [round(x * 100, 2) for x in drawdown.values[::21]] # Aylık özet (frontend için)
    }

def calculate_factor_regression(port_returns: pd.Series, valid_tickers: list) -> dict:
    """
    US hisseleri için basit Fama-French faktör yaklaşımı (Market, Size, Value).
    """
    if port_returns.empty:
        return {}
        
    # Sadece ABD hisseleri mi?
    is_us_only = True
    for t in valid_tickers:
        if t.get("market") != "US" and t.get("market") != "CRYPTO":
            is_us_only = False
            break
            
    if not is_us_only:
        return {"error": "US_ONLY", "message": "Faktör analizi sadece ABD hisseleri içeren portföyler için çalışır."}
        
    try:
        from yahooquery import Ticker
        
        start_date = port_returns.index[0]
        end_date = port_returns.index[-1]
        
        # Download proxies
        t = Ticker(["SPY", "IJR", "VTV", "VUG"])
        factors_data_raw = t.history(start=start_date, end=end_date, adj_ohlc=True)
        
        if factors_data_raw is None or not isinstance(factors_data_raw, pd.DataFrame) or factors_data_raw.empty:
             return {"error": "FAILED", "message": "Faktör verileri (SPY, IJR, VTV, VUG) indirilemedi."}
             
        # Unstack to get Index=Date, Columns=Symbol
        factors_data = factors_data_raw['close'].unstack(level=0)
        factors_data.columns = [c.upper() for c in factors_data.columns]
        factors_data.index = pd.to_datetime(factors_data.index)
        
        if "SPY" not in factors_data.columns:
            return {"error": "FAILED", "message": "Faktör verileri (SPY) ekli değil."}
            
        f_rets = factors_data.pct_change().dropna()
        
        # Align dates
        aligned = pd.concat([port_returns, f_rets], axis=1, join="inner").dropna()
        if len(aligned) < 30:
            return {"error": "FAILED", "message": f"Faktör analizi için yeterli veri örtüşmesi yok ({len(aligned)} gün)."}
            
        y = aligned.iloc[:, 0].astype(float) # portfolio returns
        
        # Build factors
        MKT = aligned["SPY"].astype(float)
        SMB = (aligned["IJR"] - aligned["SPY"]).astype(float) # proxy for Size
        HML = (aligned["VTV"] - aligned["VUG"]).astype(float) # proxy for Value
        
        # OLS regression using numpy
        X = np.column_stack((np.ones(len(MKT)), MKT.values, SMB.values, HML.values))
        beta, _, _, _ = np.linalg.lstsq(X, y.values, rcond=None)
        
        alpha, mkt_beta, smb_beta, hml_beta = beta
        
        return {
            "alpha_annual": round(float(alpha * 252 * 100), 2),
            "market_beta": round(float(mkt_beta), 2),
            "size_beta": round(float(smb_beta), 2),
            "value_beta": round(float(hml_beta), 2)
        }
    except Exception as e:
        logger.debug(f"Factor regression failed: {e}")
        return {"error": "FAILED", "message": "Faktör verisi çekilemedi."}

import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def calculate_portfolio_risk(returns_df: pd.DataFrame, weights_map: dict) -> dict:
    """
    Portföy için Gelişmiş Risk Metrikleri Hesaplar:
    1. Tarihsel VaR (%95)
    2. Max Drawdown
    3. Beta-Shock Stres Testi (-20%)
    """
    if returns_df.empty or not weights_map:
        return {}
        
    tickers = list(returns_df.columns)
    
    # Normalize weights
    total_w = sum(weights_map.get(t, 0) for t in tickers)
    if total_w <= 0:
        # Fallback to equal weights
        total_w = len(tickers)
        current_weights = {t: 1.0 / len(tickers) for t in tickers}
    else:
        current_weights = {t: weights_map[t] / total_w for t in tickers}

    # 1. Portföy Günlük Getiri Serisi
    weights_vector = np.array([current_weights[t] for t in tickers])
    portfolio_returns = returns_df.dot(weights_vector)
    
    # 2. Tarihsel VaR (%95 Güven Aralığı)
    # VaR: Kayıp serisinin 5. yüzdelik dilimi (Negatif değer)
    try:
        var_95 = np.percentile(portfolio_returns, 5)
    except Exception:
        var_95 = 0.0
        
    # 3. Max Drawdown
    try:
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max
        max_dd = drawdown.min()
    except Exception:
        max_dd = 0.0
        
    # 4. Basit Stres Testi (-%20 Endeks Şoku)
    # Beta hesaplama: beta = Cov(Asset, Market) / Var(Market)
    # Burada basitleştirmek için eşit ağırlıklı borsa endeksi (Market proxy) üretebiliriz
    market_proxy_returns = returns_df.mean(axis=1) # Eşit ağırlıklı endeks kurgusu
    # Beta katsayısını her varlık için bulalım
    betas = {}
    try:
        var_m = market_proxy_returns.var()
        if var_m > 0:
            for t in tickers:
                cov = returns_df[t].cov(market_proxy_returns)
                betas[t] = cov / var_m
        else:
            betas = {t: 1.0 for t in tickers}
    except Exception:
        betas = {t: 1.0 for t in tickers}
        
    weighted_beta = sum(current_weights[t] * betas.get(t, 1.0) for t in tickers)
    
    # Şok Senaryosu: Endeks %20 düşerse
    expected_shock_drop = -20 * weighted_beta

    return {
        "status": "success",
        "var_95": round(float(var_95 * 100), 2), # Yüzdesel (Örn: -2.35)
        "max_drawdown": round(float(max_dd * 100), 2), # Yüzdesel (Örn: -15.4)
        "weighted_beta": round(float(weighted_beta), 2),
        "stress_test_shock_drop": round(float(expected_shock_drop), 2), # Tahmini düşüş (%)
        "risk_level": "Yüksek" if abs(var_95 * 100) > 4 or abs(max_dd * 100) > 25 else "Orta" if abs(var_95 * 100) > 2 else "Düşük"
    }

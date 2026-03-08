import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def optimize_portfolio(returns_df: pd.DataFrame, risk_free_rate: float = 0.0) -> dict:
    """
    Kovaryans matrisi üzerinden Maksimum Sharpe Oranı (Tangent Portfolio) hesaplar.
    scipy yüklü ise SLSQP kullanır, yoksa 5000 iterasyonlu Monte Carlo yaklaşımı uygular.
    """
    tickers = list(returns_df.columns)
    num_assets = len(tickers)
    
    if num_assets < 2:
        return {t: 1.0 for t in tickers}
    
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252
    
    def port_ret(weights):
        return np.sum(mean_returns * weights)
    
    def port_vol(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    
    try:
        import scipy.optimize as sco
        
        def min_func_sharpe(weights):
            return -(port_ret(weights) - risk_free_rate) / port_vol(weights)
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
        bounds = tuple((0.0, 1.0) for _ in range(num_assets))
        init_guess = [1.0 / num_assets] * num_assets
        
        res = sco.minimize(min_func_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        best_w = res.x
        
    except ImportError:
        logger.info("scipy not found, using Monte Carlo method for portfolio optimization.")
        best_sharpe = -100.0
        best_w = np.array([1.0 / num_assets] * num_assets)
        
        for _ in range(5000):
            w = np.random.random(num_assets)
            w /= np.sum(w)
            ret = port_ret(w)
            vol = port_vol(w)
            sharpe = (ret - risk_free_rate) / vol
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_w = w
                
    # Format the output as a dictionary of {ticker: weight_percentage}
    opt_weights = {}
    for i, t in enumerate(tickers):
        weight_pct = round(float(best_w[i]) * 100, 2)
        opt_weights[t] = weight_pct
        
    return opt_weights

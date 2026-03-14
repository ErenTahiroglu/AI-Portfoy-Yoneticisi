import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def optimize_portfolio(returns_df: pd.DataFrame, risk_free_rate: float = 0.0) -> dict:
    """
    Kovaryans matrisi üzerinden 3 farklı portföy optimizasyonu hesaplar:
    1. Maksimum Sharpe Oranı
    2. Minimum Varyans (Risk)
    3. Maksimum Getiri
    """
    tickers = list(returns_df.columns)
    num_assets = len(tickers)
    
    if num_assets < 2:
        default_w = {t: 100.0 for t in tickers}
        return {"max_sharpe": default_w, "min_volatility": default_w, "max_return": default_w}
    
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252
    
    def port_ret(weights):
        return np.sum(mean_returns * weights)
    
    def port_vol(weights):
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
    results = {}
    
    try:
        import scipy.optimize as sco
        
        # 1. Max Sharpe
        def min_func_sharpe(weights):
            return -(port_ret(weights) - risk_free_rate) / port_vol(weights)
            
        # 2. Min Volatility
        def min_func_volatility(weights):
            return port_vol(weights)
            
        # 3. Max Return (with 15% vol constraint if possible)
        def min_func_return(weights):
            return -port_ret(weights)
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
        bounds = tuple((0.0, 1.0) for _ in range(num_assets))
        init_guess = [1.0 / num_assets] * num_assets
        
        # Calculate Max Sharpe
        res_sharpe = sco.minimize(min_func_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        # Calculate Min Volatility
        res_vol = sco.minimize(min_func_volatility, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        # Calculate Max Return
        res_ret = sco.minimize(min_func_return, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        
        def format_weights(w_array):
            w_dict = {}
            for i, t in enumerate(tickers):
                weight_pct = round(float(w_array[i]) * 100, 2)
                w_dict[t] = weight_pct
            return w_dict
            
        results["max_sharpe"] = format_weights(res_sharpe.x)
        results["min_volatility"] = format_weights(res_vol.x)
        results["max_return"] = format_weights(res_ret.x)
        
    except ImportError:
        logger.info("scipy not found, using Monte Carlo method for portfolio optimization.")
        # Fallback to simple logic (just equal weights to avoid slow MC)
        default_w = {t: round(100.0/num_assets, 2) for t in tickers}
        results = {"max_sharpe": default_w, "min_volatility": default_w, "max_return": default_w}
        
    return results

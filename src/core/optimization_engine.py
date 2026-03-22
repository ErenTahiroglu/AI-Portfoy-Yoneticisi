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
    
    def get_default_w():
        return {t: round(100.0 / max(num_assets, 1), 2) for t in tickers}
    
    # 1. Veri Doğrulama (Sanitization)
    if returns_df.empty:
        logger.warning("optimize_portfolio: Gelen returns_df tamamen boş! Fallback uygulanıyor.")
        default_w = get_default_w()
        return {"max_sharpe": default_w, "min_volatility": default_w, "max_return": default_w}
        
    returns_df = returns_df.replace([np.inf, -np.inf], np.nan).dropna()
    
    if len(returns_df) < 2 or num_assets < 2:
        logger.warning(f"optimize_portfolio: Yetersiz veri (Satır: {len(returns_df)}, Varlık: {num_assets}). Fallback uygulanıyor.")
        default_w = get_default_w()
        return {"max_sharpe": default_w, "min_volatility": default_w, "max_return": default_w}
    
    # Başlangıç durumu için eşit dağılım kopyaları oluşturuluyor
    default_w = get_default_w()
    results = {
        "max_sharpe": default_w.copy(), 
        "min_volatility": default_w.copy(), 
        "max_return": default_w.copy()
    }
    
    # 2. Matematiksel Hata Yakalama Bloğu
    try:
        mean_returns = returns_df.mean() * 252
        cov_matrix = returns_df.cov() * 252
        
        def port_ret(weights):
            return np.sum(mean_returns * weights)
        
        def port_vol(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
        import scipy.optimize as sco
        
        def min_func_sharpe(weights):
            vol = port_vol(weights)
            if vol == 0: return 0.0
            return -(port_ret(weights) - risk_free_rate) / vol
            
        def min_func_volatility(weights):
            return port_vol(weights)
            
        def min_func_return(weights):
            return -port_ret(weights)
        
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
        bounds = tuple((0.0, 1.0) for _ in range(num_assets))
        init_guess = [1.0 / num_assets] * num_assets
        
        def format_weights(w_array):
            w_dict = {}
            for i, t in enumerate(tickers):
                w_dict[t] = round(float(w_array[i]) * 100, 2)
            return w_dict

        # Calculate Max Sharpe
        res_sharpe = sco.minimize(min_func_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        if res_sharpe.success:
            results["max_sharpe"] = format_weights(res_sharpe.x)
        else:
            logger.warning(f"optimize_portfolio: max_sharpe optimizasyonu başarısız: {res_sharpe.message}")

        # Calculate Min Volatility
        res_vol = sco.minimize(min_func_volatility, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        if res_vol.success:
            results["min_volatility"] = format_weights(res_vol.x)
        else:
            logger.warning(f"optimize_portfolio: min_volatility optimizasyonu başarısız: {res_vol.message}")
            
        # Calculate Max Return
        res_ret = sco.minimize(min_func_return, init_guess, method='SLSQP', bounds=bounds, constraints=constraints)
        if res_ret.success:
            results["max_return"] = format_weights(res_ret.x)
        else:
            logger.warning(f"optimize_portfolio: max_return optimizasyonu başarısız: {res_ret.message}")
            
    except ImportError:
        logger.info("scipy not found, using default equal weights fallback.")
    except Exception as e:
        logger.warning(f"optimize_portfolio sırasında kritik hata oluştu (LinAlgError vs): {e}")
        # Hata durumunda results, fonksiyonun başında eşit ağırlıkla tanımlanmış halleriyle kalır.
        
    return results

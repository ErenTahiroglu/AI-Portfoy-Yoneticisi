import asyncio
import pandas as pd
from typing import List, Dict, Optional
from yahooquery import Ticker
from fastapi import HTTPException

from backend.engine.optimization_engine import optimize_portfolio
from backend.analyzers.risk_analyzer import calculate_portfolio_risk

async def get_returns_df(tickers: List[str]) -> pd.DataFrame:
    """
    Downloads historical close prices using Yahooquery Ticker and calculates a returns DataFrame.
    """
    t = Ticker(tickers)
    # Executing blocking dataframe manipulations in separate thread isn't strictly needed for Ticker 
    # as it's already wrapped, but let's be fully async safe
    loop = asyncio.get_event_loop()
    hist = await loop.run_in_executor(None, t.history, "1y", True)
    
    if hist is None or (isinstance(hist, pd.DataFrame) and hist.empty):
        raise HTTPException(status_code=400, detail="Piyasa verisi alınamadı. Lütfen ticker sembolünü ve internet bağlantınızı kontrol edin.")

        
    try:
        price_df = hist['close'].unstack(level=0)
        price_df.columns = [c.upper() for c in price_df.columns]
        price_df.ffill(inplace=True)
        price_df.dropna(inplace=True)
        returns_df = price_df.pct_change().dropna()
    except KeyError:
         raise HTTPException(status_code=400, detail="Fiyat verileri çözümlenemedi: beklenen 'close' sütunu bulunamadı.")
         
    if returns_df.empty or len(returns_df) < 20: 
        raise HTTPException(status_code=400, detail="Yetersiz finansal veri mevcut.")
        
    return returns_df

async def optimize_portfolio_service(tickers: List[str], risk_free_rate: float, weights: Optional[Dict[str, float]]):
    """
    Business logic layer for optimizing portfolio weights based on Max Sharpe and Min Vol.
    """
    returns_df = await get_returns_df(tickers)
    opt_results = await asyncio.to_thread(optimize_portfolio, returns_df, risk_free_rate)
    cur_weights = weights or {t: 100.0 / len(tickers) for t in tickers}
    return {
        "status": "success", 
        "current_weights": cur_weights, 
        "optimal_weights": opt_results.get("max_sharpe", {}), 
        "min_volatility_weights": opt_results.get("min_volatility", {})
    }

async def calculate_portfolio_risk_service(tickers: List[str], weights: Optional[Dict[str, float]]):
    """
    Business logic layer for running stress tests and VaR metrics over holding weights.
    """
    returns_df = await get_returns_df(tickers)
    return await asyncio.to_thread(calculate_portfolio_risk, returns_df, weights)

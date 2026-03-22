import asyncio
import logging
import json
import gc
import os
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
import pandas as pd

from backend.api.models import AnalysisRequest, PortfolioOptimizeRequest, PortfolioRiskRequest
from backend.api.rate_limiter import limiter
from backend.api.auth import verify_jwt, SUPABASE_JWT_SECRET
import jwt
from backend.api.dependencies import get_engine
from backend.api.utils import process_tickers_with_weights, tr_lower
from backend.data.constants import POPULAR_TICKERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])

@router.post("/analyze", dependencies=[Depends(limiter.check)])
async def analyze_portfolio(request: AnalysisRequest, req: Request, engine=Depends(get_engine)):
    """Ticker listesiyle portföy analizi (SSE / Streaming)."""
    if not request.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if request.use_ai and not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI analysis")
    
    parsed_tickers, weights_map = process_tickers_with_weights(request.tickers)
    if not parsed_tickers:
        raise HTTPException(status_code=400, detail="No valid tickers provided")

    # Optional Auth for Token Logging
    user_id = None
    auth_header = req.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], options={"verify_aud": True}, audience="authenticated")
                user_id = payload.get("sub")
                
                if request.use_ai:
                     from backend.api.dependencies import check_llm_quota
                     await check_llm_quota(req, payload=payload)
            except HTTPException:
                raise
            except Exception:
                pass 

    async def event_generator():
        semaphore = asyncio.Semaphore(2)  # Render 512MB limit için
        async def analyze_with_semaphore(ticker):
            async with semaphore:
                try:
                    res = await asyncio.to_thread(
                        engine._analyze_single,
                        ticker,
                        check_islamic=request.check_islamic,
                        check_financials=request.check_financials,
                        use_ai=request.use_ai,
                        api_key=request.api_key,
                        model=request.model,
                        lang=request.lang,
                        user_id=user_id
                    )
                    return ticker, res, None
                except Exception as e:
                    return ticker, None, e

        tasks = [asyncio.create_task(analyze_with_semaphore(t)) for t in parsed_tickers]
        try:
            for coro in asyncio.as_completed(tasks):
                if await req.is_disconnected():
                    logger.warning("🚫 SSE istemci bağlantısı koptu.")
                    for t in tasks: t.cancel()
                    break
                ticker, res, err = await coro
                if err:
                    yield f"data: {json.dumps({'ticker': ticker, 'error': str(err)})}\n\n"
                else:
                    res["weight"] = weights_map.get(ticker, 1.0)
                    yield f"data: {json.dumps(res)}\n\n"
        except Exception as e:
            logger.error(f"SSE Hatası: {e}")
        finally:
            gc.collect()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/portfolio-signals")
async def get_portfolio_signals(tickers: str = ""):
    """Teknik sinyalleri tarar."""
    tickers = tickers.strip()
    if not tickers: return []
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list: return []

    from backend.analyzers.technical_analyzer import run_technical_indicators
    async def fetch_signal(ticker):
        res_entry = {"ticker": ticker}
        try:
            await asyncio.to_thread(run_technical_indicators, ticker, res_entry)
            tech = res_entry.get("technicals", {})
            return {"ticker": ticker, "signals": tech.get("signals", []), "gauge_score": tech.get("gauge_score", 50)}
        except Exception as e:
            return {"ticker": ticker, "signals": [], "error": str(e)}
    tasks = [asyncio.create_task(fetch_signal(t)) for t in ticker_list]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r.get("signals")]

@router.get("/search")
async def search_tickers(q: str = ""):
    q = q.strip()
    if not q: return []
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=6&newsCount=0"
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200: return []
            quotes = resp.json().get("quotes", [])
            return [{"symbol": i.get("symbol"), "name": i.get("shortname") or i.get("longname") or "", "exchDisp": i.get("exchDisp") or ""} for i in quotes]
    except Exception: return []

@router.get("/suggest")
async def suggest_tickers(q: str = ""):
    q = q.strip()
    if not q: return {"suggestions": []}
    q_norm = tr_lower(q)
    matches = []
    for ticker, name in POPULAR_TICKERS.items():
        if tr_lower(ticker).startswith(q_norm) or q_norm in tr_lower(ticker):
            matches.append({"ticker": ticker, "name": name})
            if len(matches) >= 15: break
    return {"suggestions": matches[:15]}

@router.post("/optimize-portfolio", dependencies=[Depends(verify_jwt)])
async def optimize_portfolio_endpoint(req_body: PortfolioOptimizeRequest):
    if not req_body.tickers: raise HTTPException(status_code=400, detail="Varlık listesi boş olamaz.")
    try:
        from yahooquery import Ticker
        from backend.core.optimization_engine import optimize_portfolio
        t = Ticker(req_body.tickers)
        hist = t.history(period="1y", adj_ohlc=True)
        if hist is None or (isinstance(hist, pd.DataFrame) and hist.empty): raise HTTPException(status_code=500, detail="Veri indirilemedi.")
        price_df = hist['close'].unstack(level=0)
        price_df.columns = [c.upper() for c in price_df.columns]
        price_df.ffill(inplace=True); price_df.dropna(inplace=True)
        returns_df = price_df.pct_change().dropna()
        if returns_df.empty or len(returns_df) < 20: raise HTTPException(status_code=400, detail="Yetersiz veri.")
        opt_results = optimize_portfolio(returns_df, risk_free_rate=req_body.risk_free_rate)
        return {"status": "success", "current_weights": req_body.weights or {t: 100.0 / len(req_body.tickers) for t in req_body.tickers}, "optimal_weights": opt_results.get("max_sharpe", {}), "min_volatility_weights": opt_results.get("min_volatility", {})}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/risk-analysis", dependencies=[Depends(verify_jwt)])
async def risk_analysis_endpoint(req_body: PortfolioRiskRequest):
    if not req_body.tickers: raise HTTPException(status_code=400, detail="Varlık listesi boş olamaz.")
    try:
        from yahooquery import Ticker
        from backend.analyzers.risk_analyzer import calculate_portfolio_risk
        t = Ticker(req_body.tickers)
        hist = t.history(period="1y", adj_ohlc=True)
        price_df = hist['close'].unstack(level=0)
        price_df.columns = [c.upper() for c in price_df.columns]
        price_df.ffill(inplace=True); price_df.dropna(inplace=True)
        returns_df = price_df.pct_change().dropna()
        return calculate_portfolio_risk(returns_df, req_body.weights)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/predict/{ticker}", dependencies=[Depends(limiter.check)])
async def predict_api(ticker: str):
    from backend.analyzers.ml_predictor import predict_price
    res = await asyncio.to_thread(predict_price, ticker.upper())
    return res

@router.get("/options/{ticker}", dependencies=[Depends(limiter.check)])
async def options_api(ticker: str, expiration: Optional[str] = None):
    from backend.analyzers.options_analyzer import get_options_chain
    res = await asyncio.to_thread(get_options_chain, ticker.upper(), expiration)
    return res

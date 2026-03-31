import asyncio
import logging
import json
import gc
import os
import hashlib
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
import pandas as pd

from backend.api.models import AnalysisRequest, PortfolioOptimizeRequest, PortfolioRiskRequest
from backend.infrastructure.limiter import limiter
from backend.infrastructure.auth import verify_jwt, SUPABASE_JWT_SECRET
import jwt
from backend.api.dependencies import get_orchestrator
from backend.api.utils import process_tickers_with_weights, tr_lower
from backend.data.constants import POPULAR_TICKERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])

@router.get("/status/{job_id}")
async def get_background_job_status(job_id: str):
    """
    Vercel Timeout (10s) sınırını delmek için kullanılan Polling rotası.
    Arkaplandaki (Redis) görevin tamamlanıp tamamlanmadığını söyler.
    """
    from backend.infrastructure.job_queue import get_job_status
    status_data = get_job_status(job_id)
    if status_data.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Job not found or expired.")
    return status_data


async def check_double_submit(request: Request, payload_dict: dict, name: str):
    """Mükerrer istekleri engellemek için 5 saniyelik idempotens süzgeci."""
    from backend.infrastructure import redis_cache
    from backend.infrastructure.limiter import _extract_user_id
    
    auth = request.headers.get("Authorization")
    user_id = _extract_user_id(auth) or (request.client.host if request.client else "unknown")
    
    # Payload'u normalize edip hashle
    payload_str = json.dumps(payload_dict, sort_keys=True)
    p_hash = hashlib.md5(payload_str.encode("utf-8")).hexdigest()
    key = f"idem:{name}:{user_id}:{p_hash}"
    
    existing = await asyncio.to_thread(redis_cache.cache_get, key)
    if existing:
        raise HTTPException(status_code=429, detail="Mükerrer işlem engellendi. Lütfen birkaç saniye bekleyin.")
        
    await asyncio.to_thread(redis_cache.cache_set, key, 1, ttl=5) # 5 sny kilit

@router.post("/analyze", dependencies=[Depends(limiter.check)])
async def analyze_portfolio(request: AnalysisRequest, req: Request):
    """Ticker listesiyle portföy analizi (LangGraph Engine - Streaming)."""
    if not request.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if request.use_ai and not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI analysis")
    
    parsed_tickers, weights_map = process_tickers_with_weights(request.tickers)
    if not parsed_tickers:
        raise HTTPException(status_code=400, detail="No valid tickers provided")

    # Auth for Token Logging & Quota check
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

    from backend.services.chat_orchestrator import orchestrator

    async def event_generator():
        semaphore = asyncio.Semaphore(2) # Parallel limit for Free Tier
        async def run_graph_task(ticker):
            async with semaphore:
                try:
                    input_state = {
                        "ticker": ticker,
                        "messages": [f"{ticker} analizi başlatıldı."],
                        "api_key": request.api_key,
                        "model_name": request.model,
                        "lang": request.lang,
                        "user_id": user_id,
                        "check_financials": request.check_financials,
                        "check_islamic": request.check_islamic
                    }
                    # Synchronized Bridge: Direct ainvoke
                    result = await orchestrator.ainvoke(input_state)
                    # OutputMapper formats for frontend
                    legacy_res = result.get("final_report", {})
                    return ticker, legacy_res, None
                except Exception as e:
                    return ticker, None, e

        tasks = [asyncio.create_task(run_graph_task(t)) for t in parsed_tickers]
        try:
            for coro in asyncio.as_completed(tasks):
                if await req.is_disconnected():
                    for t in tasks: t.cancel()
                    break
                ticker, res, err = await coro
                if err:
                    yield f"data: {json.dumps({'ticker': ticker, 'error': str(err)})}\n\n"
                else:
                    res["weight"] = weights_map.get(ticker, 1.0)
                    yield f"data: {json.dumps(res)}\n\n"
        except Exception as e:
            logger.error(f"Graph SSE Error: {e}")
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
    q = q.strip().upper()
    if not q: return []
    
    import httpx
    from backend.data.constants import POPULAR_TICKERS
    
    local_matches = []
    yahoo_matches = []
    
    # 1. Local Lookup with proper categorization
    us_popular = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "DIS", "BAC", "KO", "PEP", "NFLX", "INTC", "AMD", "CRM", "AVGO", "COST", "ABBV", "MRK", "TMO", "ACN", "LLY", "PYPL", "NKE", "ADBE", "CSCO", "ORCL", "TXN"]
    bist_popular = ["THYAO", "ASELS", "GARAN", "AKBNK", "YKBNK", "EREGL", "BIMAS", "SAHOL", "KCHOL", "SISE", "TUPRS", "FROTO", "TOASO", "TCELL", "PGSUS", "TAVHL", "EKGYO", "KOZAL", "SASA", "TTKOM", "ARCLK", "MGROS", "PETKM", "SOKM", "VESTL", "HALKB", "VAKBN", "GUBRF", "KOZAA", "ODAS", "KRDMD", "AEFES", "ENKAI", "DOHOL", "ISCTR", "ALARK"]
    crypto_popular = ["BTC", "ETH", "XRP", "SOL", "ADA", "DOGE", "TRX", "DOT", "MATIC", "LTC", "SHIB", "AVAX", "LINK", "UNI", "BCH", "OP", "ARB", "XLM", "NEAR"]
    
    for ticker, name in POPULAR_TICKERS.items():
        if q in ticker.upper() or q in name.upper():
            exch_label = "US" if ticker in us_popular else ("BIST" if ticker in bist_popular else "TEFAS")
            local_matches.append({"symbol": ticker, "name": name, "exchDisp": exch_label})

    # 2. Yahoo Finance Search
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=10&newsCount=0"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                quotes = resp.json().get("quotes", [])
                for i in quotes:
                    symbol = i.get("symbol", "").upper()
                    exch = i.get("exchDisp", "").upper()
                    quote_type = i.get("quoteType", "").upper()
                    
                    if any(m["symbol"] == symbol for m in local_matches): continue

                    if symbol.endswith(".IS"):
                        yahoo_matches.append({"symbol": symbol, "name": i.get("shortname") or i.get("longname") or "", "exchDisp": "BIST"})
                    elif quote_type == "CRYPTOCURRENCY" or i.get("typeDisp") == "cryptocurrency":
                        yahoo_matches.append({"symbol": symbol, "name": i.get("shortname") or i.get("longname") or "", "exchDisp": "Crypto"})
                    elif any(u in exch for u in ["NYSE", "NASDAQ", "BATS", "NMS", "NYQ", "NGM", "PCX", "AMEX"]):
                        yahoo_matches.append({"symbol": symbol, "name": i.get("shortname") or i.get("longname") or "", "exchDisp": exch})
                    elif i.get("shortname"):
                         yahoo_matches.append({"symbol": symbol, "name": i.get("shortname"), "exchDisp": exch or "Stock"})
    except Exception as e:
        logger.error(f"Yahoo Search error: {e}")

    # 3. Final Combination
    seen = set()
    combined = []
    for m in local_matches + yahoo_matches:
        if m["symbol"] not in seen:
            seen.add(m["symbol"])
            combined.append(m)

    # 4. Speculative TEFAS (As a last resort if strictly 3 letters and NOT found yet)
    if len(q) == 3 and q.isalpha() and q not in seen:
        is_crypto = q in crypto_popular
        combined.append({
            "symbol": q if not is_crypto else f"{q}-USD",
            "name": f"{q} TEFAS Fonu (Olası)" if not is_crypto else f"{q} Kripto Para",
            "exchDisp": "TEFAS" if not is_crypto else "Crypto"
        })

    return combined[:12]

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
async def optimize_portfolio_endpoint(req_body: PortfolioOptimizeRequest, request: Request):
    if not req_body.tickers: raise HTTPException(status_code=400, detail="Varlık listesi boş olamaz.")
    
    # Double-submit koruması
    await check_double_submit(request, req_body.model_dump(), "optimize")
    
    try:
        from backend.services.analysis_service import optimize_portfolio_service
        return await optimize_portfolio_service(req_body.tickers, req_body.risk_free_rate, req_body.weights)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/risk-analysis", dependencies=[Depends(verify_jwt)])
async def risk_analysis_endpoint(req_body: PortfolioRiskRequest, request: Request):
    if not req_body.tickers: raise HTTPException(status_code=400, detail="Varlık listesi boş olamaz.")
    
    # Double-submit koruması
    await check_double_submit(request, req_body.model_dump(), "risk")
    
    try:
        from backend.services.analysis_service import calculate_portfolio_risk_service
        return await calculate_portfolio_risk_service(req_body.tickers, req_body.weights)
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

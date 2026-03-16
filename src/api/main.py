"""
🧩 Puzzle Parça: API Katmanı — v3.0
============================================
FastAPI endpoint tanımları, request/response modelleri ve middleware.
İş mantığı analysis_engine.py'de yaşar.

v3.0 Yenilikler:
  • Export endpoint'leri (Excel, PDF, DOCX)
  • Ticker suggestion / autocomplete endpoint'i

Kullanım:
    uvicorn main:app --host 127.0.0.1 --port 8000
"""

import logging

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from src.api.rate_limiter import limiter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import asyncio
import json
import gc

# ── Modül importları ──────────────────────────────────────────────────────
# ── Modül importları ──────────────────────────────────────────────────────
from src.core.analysis_engine import AnalysisEngine

# ── FastAPI uygulaması ────────────────────────────────────────────────────
app = FastAPI(title="Portföy Analiz Platformu", version="3.0")

# ── Analiz motoru (singleton) ─────────────────────────────────────────────
engine = AnalysisEngine()

# ── Statik dosya servisi (Frontend) ───────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.join(os.path.dirname(base_dir), "frontend")

if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")

# ── Cache-Control middleware (tarayıcı eski dosyaları kullanmasın) ─────────
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/ui"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

# ── CORS middleware ───────────────────────────────────────────────────────
origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
origins = [o.strip() for o in origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Portföy Analiz API aktif"}

# ══════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELLERİ
# ══════════════════════════════════════════════════════════════════════════

class AnalysisRequest(BaseModel):
    tickers: List[str]
    use_ai: bool = False
    api_key: Optional[str] = None
    av_api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    check_islamic: bool = False
    check_financials: bool = True
    lang: str = "tr"
    initial_balance: float = 10000.0
    monthly_contribution: float = 0.0
    rebalancing_freq: str = "none"

# TextAnalysisRequest kaldırıldı (Kullanılmıyor)

# ══════════════════════════════════════════════════════════════════════════
# TICKER SUGGESTION DATA
# ══════════════════════════════════════════════════════════════════════════

from src.data.constants import POPULAR_TICKERS


# ══════════════════════════════════════════════════════════════════════════
# API ENDPOINT'LERİ
# ══════════════════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    return RedirectResponse(url="/ui")

def process_tickers_with_weights(raw_tickers: List[str]):
    parsed = []
    weights_map = {}
    for rt in raw_tickers:
        parts = rt.split(":")
        ticker = parts[0].strip().upper()
        if not ticker: continue
        weight = 1.0
        if len(parts) > 1:
            try:
                weight = float(parts[1])
            except ValueError:
                pass
        parsed.append(ticker)
        weights_map[ticker] = weight
    return parsed, weights_map

@app.post("/api/analyze", dependencies=[Depends(limiter.check)])
async def analyze_portfolio(request: AnalysisRequest, req: Request):
    """Ticker listesiyle portföy analizi (SSE / Streaming)."""
    if not request.tickers:
        raise HTTPException(status_code=400, detail="No tickers provided")
    if request.use_ai and not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI analysis")
    
    parsed_tickers, weights_map = process_tickers_with_weights(request.tickers)
    if not parsed_tickers:
        raise HTTPException(status_code=400, detail="No valid tickers provided")

    async def event_generator():
        semaphore = asyncio.Semaphore(2)  # Render 512MB limit için eşzamanlılık limiti

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
                        lang=request.lang
                    )
                    return ticker, res, None
                except Exception as e:
                    return ticker, None, e

        # Görevleri oluştur
        tasks = [asyncio.create_task(analyze_with_semaphore(t)) for t in parsed_tickers]

        try:
            for coro in asyncio.as_completed(tasks):
                # Her adımda bağlantı kesilmesi kontrol edilir
                if await req.is_disconnected():
                    logger.warning("🚫 SSE istemci bağlantısı koptu. Çalışan analizler iptal ediliyor.")
                    for t in tasks:
                        if not t.done():
                            t.cancel()
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
            # Stream bitince bellek temizliği
            gc.collect()

    return StreamingResponse(event_generator(), media_type="text/event-stream")



@app.get("/api/portfolio-signals")
async def get_portfolio_signals(tickers: str = ""):
    """Kullanıcı portföyündeki hisseler için teknik sinyalleri tarar."""
    tickers = tickers.strip()
    if not tickers:
        return []
    
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return []

    from src.analyzers.technical_analyzer import run_technical_indicators
    import asyncio

    async def fetch_signal(ticker):
        res_entry = {"ticker": ticker}
        try:
            await asyncio.to_thread(run_technical_indicators, ticker, res_entry)
            tech = res_entry.get("technicals", {})
            return {
                "ticker": ticker,
                "signals": tech.get("signals", []),
                "gauge_score": tech.get("gauge_score", 50)
            }
        except Exception as e:
            return {"ticker": ticker, "signals": [], "error": str(e)}

    tasks = [asyncio.create_task(fetch_signal(t)) for t in ticker_list]
    results = await asyncio.gather(*tasks)
    
    # Sadece sinyal üreten hisseleri filtrele
    triggered = [r for r in results if r.get("signals") and len(r["signals"]) > 0]
    return triggered

# ══════════════════════════════════════════════════════════════════════════
# TICKER SUGGESTION ENDPOINT
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/search")
async def search_tickers(q: str = ""):
    """Yahoo Finance Arama API'sine hafif bir proxy sağlar."""
    q = q.strip()
    if not q:
        return []
    
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={q}&quotesCount=6&newsCount=0"
    
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                logger.error(f"Yahoo Search API Hatası: {resp.status_code}")
                return []
            
            data = resp.json()
            quotes = data.get("quotes", [])
            
            results = []
            for item in quotes:
                # Sadece hisse, ETF veya fonları al (opsiyonel filtreleme istersen)
                results.append({
                    "symbol": item.get("symbol"),
                    "name": item.get("shortname") or item.get("longname") or "",
                    "exchDisp": item.get("exchDisp") or ""
                })
            return results
    except Exception as e:
        logger.error(f"Arama Hatası: {e}")
        return []

# ── Yardımcı Fonksiyonlar ────────────────────────────────────────────────
def tr_lower(text: str) -> str:
    """Türkçe karakter duyarlı küçük harfe çevirme."""
    return text.replace('İ', 'i').replace('I', 'ı').lower()

def tr_upper(text: str) -> str:
    """Türkçe karakter duyarlı büyük harfe çevirme."""
    return text.replace('i', 'İ').replace('ı', 'I').upper()

@app.get("/api/suggest")
async def suggest_tickers(q: str = ""):
    """Ticker autocomplete önerileri döndürür."""
    q = q.strip()
    if not q:
        return {"suggestions": []}
    
    q_norm = tr_lower(q)
    matches = []
    
    # 1. Ticker üzerinden arama (Sembol)
    for ticker, name in POPULAR_TICKERS.items():
        ticker_norm = tr_lower(ticker)
        if ticker_norm.startswith(q_norm) or q_norm in ticker_norm:
            matches.append({"ticker": ticker, "name": name})
            if len(matches) >= 15: break

    # 2. İsim üzerinden arama (Eğer liste dolmadıysa)
    if len(matches) < 10:
        for ticker, name in POPULAR_TICKERS.items():
            if any(m["ticker"] == ticker for m in matches): continue
            name_norm = tr_lower(name)
            if q_norm in name_norm:
                matches.append({"ticker": ticker, "name": name})
                if len(matches) >= 15: break
    
    return {"suggestions": matches[:15]}


# ══════════════════════════════════════════════════════════════════════════
# AI WIZARD & NEWS ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════

class WizardRequest(BaseModel):
    prompt: str
    api_key: str
    model: str = "gemini-2.5-flash"
    lang: str = "tr"

class NewsRequest(BaseModel):
    tickers: List[str]
    api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    lang: str = "tr"

class ChatRequest(BaseModel):
    messages: List[dict]
    portfolio_context: dict
    api_key: str
    model: str = "gemini-2.5-flash"
    lang: str = "tr"

class MacroRequest(BaseModel):
    portfolio: dict
    api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    lang: str = "tr"

@app.post("/api/analyze-macro", dependencies=[Depends(limiter.check)])
async def analyze_macro_endpoint(request: MacroRequest):
    """
    Tüm portföyün makro AI analizi için StreamingResponse (SSE) akışı sağlar.
    """
    api_key = request.api_key
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key is required for Macro Analysis")

    from src.core.ai_agent import generate_macro_advice

    def event_generator():
        try:
            for chunk in generate_macro_advice(request.portfolio, api_key, request.model, request.lang):
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/wizard")
async def wizard_api(request: WizardRequest):
    """Metinsel komuttan portföy üretir."""
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI Wizard")
    try:
        from src.core.ai_agent import generate_wizard_portfolio
        portfolio = generate_wizard_portfolio(request.prompt, request.api_key, request.model, request.lang)
        return {"portfolio": portfolio}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/news")
async def news_api(request: NewsRequest):
    """Ticker listesi için önemli haberleri çeker ve AI ile filtreler."""
    if not request.tickers: return {"news": []}
    try:
        from src.data.news_fetcher import fetch_and_filter_news
        data = fetch_and_filter_news(request.tickers, request.api_key, request.model, request.lang)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_api(request: ChatRequest):
    """Floating Copilot Chatbot Endpoint."""
    if not request.api_key:
        raise HTTPException(status_code=400, detail="API key is required for AI Copilot")
    try:
        from src.core.ai_agent import generate_chat_response
        reply = generate_chat_response(request.messages, request.portfolio_context, request.api_key, request.model, request.lang)
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ══════════════════════════════════════════════════════════════════════════
# EXPORT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════


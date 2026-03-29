import logging
import json
import re
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from backend.api.models import ChatRequest, NewsRequest
from backend.infrastructure.limiter import limiter
from backend.infrastructure.auth import verify_jwt
from backend.engine.execution_engine import execute_paper_trades
from backend.api.dependencies import check_llm_quota

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])

@router.post("/analyze-macro", dependencies=[Depends(limiter.check), Depends(check_llm_quota)])
async def analyze_macro_endpoint(request: Request):
    """Tüm portföyün makro AI analizi için StreamingResponse (SSE) akışı sağlar."""
    try:
        body = await request.json()
        portfolio = body.get("portfolio", {})
        api_key = body.get("api_key")
        model = body.get("model", "gemini-2.5-flash")
        lang = body.get("lang", "tr")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="Gemini API Key is required")

        user = getattr(request.state, "user", None)
        user_id = user["sub"] if user else None

        from backend.nodes.ai_agent import generate_macro_advice

        def event_generator():
            try:
                for chunk in generate_macro_advice(portfolio, api_key, model, lang, user_id=user_id):
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wizard", dependencies=[Depends(check_llm_quota)])
async def wizard_api(request: Request, background_tasks: BackgroundTasks):
    """Metinsel komuttan portföy üretir. (Vercel Timeout Bypass = HTTP 202)"""
    try:
        body = await request.json()
        prompt = body.get("prompt")
        api_key = body.get("api_key")
        model = body.get("model", "gemini-2.5-flash")
        lang = body.get("lang", "tr")
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required")
            
        user = getattr(request.state, "user", None)
        user_id = user["sub"] if user else None
            
        from backend.nodes.ai_agent import generate_wizard_portfolio
        from backend.infrastructure.job_queue import spawn_background_job
        
        # OOM/Timeout crash protection: Background spawn
        job_id = spawn_background_job(background_tasks, generate_wizard_portfolio, prompt, api_key, model, lang, user_id=user_id)
        
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=202, content={"status": "accepted", "job_id": job_id})
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
             raise HTTPException(status_code=429, detail="Yapay Zeka (LLM) kota veya limit sınırına ulaşıldı. Lütfen birkaç dakika sonra tekrar deneyin.")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/news", dependencies=[Depends(check_llm_quota)])
async def news_api(request: NewsRequest):
    """Ticker listesi için önemli haberleri çeker ve AI ile filtreler."""
    if not request.tickers: return {"news": []}
    try:
        from backend.data.news_fetcher import fetch_and_filter_news
        data = fetch_and_filter_news(request.tickers, request.api_key, request.model, request.lang)
        return data
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
             raise HTTPException(status_code=429, detail="Haber analiz servisi limit sınırına takıldı. Lütfen biraz bekleyin.")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/chat", dependencies=[Depends(check_llm_quota)])
async def chat_api(request: Request, body: ChatRequest, background_tasks: BackgroundTasks):
    """Floating Copilot Chatbot Endpoint (Thin Facade Bridge)."""
    if not body.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
        
    try:
        user = getattr(request.state, "user", None)
        user_id = user["sub"] if user else None

        from backend.services.chat_orchestrator import orchestrator
        from fastapi.responses import JSONResponse
        
        # OOM/Timeout protection: Background spawn
        job_id = spawn_background_job(
            background_tasks, 
            orchestrator.process_chat,
            body.messages,
            body.portfolio_context,
            body.api_key,
            body.model,
            body.lang,
            user_id=user_id,
            user_profile=body.user_profile
        )
        
        return JSONResponse(status_code=202, content={"status": "accepted", "job_id": job_id})
    except Exception as e:
        logger.error(f"Chat API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

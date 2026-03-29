import logging
import json
import re
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from backend.api.models import ChatRequest, NewsRequest
from backend.api.rate_limiter import limiter
from backend.api.auth import verify_jwt
from backend.core.execution_engine import execute_paper_trades
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

        from backend.core.ai_agent import generate_macro_advice

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
async def wizard_api(request: Request):
    """Metinsel komuttan portföy üretir."""
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
            
        from backend.core.ai_agent import generate_wizard_portfolio
        portfolio = generate_wizard_portfolio(prompt, api_key, model, lang, user_id=user_id)
        return {"portfolio": portfolio}
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
async def chat_api(request: Request, body: ChatRequest, background_tasks: fastapi.BackgroundTasks):
    """Floating Copilot Chatbot Endpoint with downstream Execution trigger."""
    if not body.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    try:
        user = getattr(request.state, "user", None)
        user_id = user["sub"] if user else None

        from backend.core.ai_agent import generate_chat_response
        reply = await generate_chat_response(body.messages, body.portfolio_context, body.api_key, body.model, body.lang, user_id=user_id, user_profile=body.user_profile)
        
        # --- SHADOW DEPLOYMENT TRIGGER ---
        # Portfolio_context'ten veya mesajdan tahmini bir ticker yakalayabiliriz. Şimdilik Genel Context
        # Fire-and-forget: Kullanıcı bu işlemi asenkron beklemez (Latency 0 ms)
        try:
            from backend.core.graph.shadow_mode import run_shadow_graph
            background_tasks.add_task(run_shadow_graph, reply, body.portfolio_context, "BIST_HINT")
        except Exception as e:
            logger.error(f"Shadow Trigger failed: {e}")
        # ---------------------------------
        
        if user_id and body.messages:
             user_msg = ""
             for msg in reversed(body.messages):
                  if msg.get("role") == "user":
                       user_msg = msg.get("content", "")
                       break
             
             match_current = re.search(r'Mevcut Varlık Dağılımım:\s*(\{.*?\})', user_msg)
             match_optimal = re.search(r'Matematiksel Optimum Dağılım:\s*(\{.*?\})', user_msg)
             
             if match_current and match_optimal:
                  import json
                  try:
                       curr_weights = json.loads(match_current.group(1).replace("'", '"'))
                       opt_weights = json.loads(match_optimal.group(1).replace("'", '"'))
                       
                       order_log = await execute_paper_trades(curr_weights, opt_weights, user_id)
                       reply += f"\n\n---\n**📊 [Sanal Emir İletim Sistemi]**\n{order_log}"
                  except Exception as ex:
                       logger.error(f"Paper trade execution from CIO failed: {ex}")

        return {"reply": reply}
    except Exception as e:
        logger.error(f"Chat API Hatası: {e}")
        error_msg = str(e)
        if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
             raise HTTPException(status_code=429, detail="Yapay Zeka (CIO) geçici olarak kullanım sınırına takıldı. Lütfen birazdan tekrar deneyin.")
        raise HTTPException(status_code=500, detail=error_msg)

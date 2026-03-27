import os
import httpx
from fastapi import Request, HTTPException, Depends
from datetime import datetime, timedelta

from backend.core.analysis_engine import AnalysisEngine
from backend.api.auth import verify_jwt

# Singleton instance of analysis engine
engine = AnalysisEngine()

def get_engine() -> AnalysisEngine:
    """Dependency Injection provider for AnalysisEngine."""
    return engine

async def check_llm_quota(request: Request, payload=Depends(verify_jwt)):
    """Kullanıcının LLM token kullanım miktarını kontrol eder, limit aşımında 402 döner."""
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
         raise HTTPException(status_code=500, detail="Supabase configs missing.")

    async with httpx.AsyncClient() as client:
        headers = { "apikey": key, "Authorization": f"Bearer {key}" }
        
        # 1. Get User Subscription Tier & Billing Cycle Start
        sett_resp = await client.get(
            f"{url}/rest/v1/user_settings?user_id=eq.{user_id}&select=subscription_tier,billing_cycle_start",
            headers=headers
        )
        sett_data = sett_resp.json()
        
        tier = 'free'
        # Default to 30 days ago if no setting row yet
        cycle_start = (datetime.utcnow() - timedelta(days=30)).isoformat() 
        
        if sett_data:
            tier = sett_data[0].get("subscription_tier", "free")
            cycle_start = sett_data[0].get("billing_cycle_start") or cycle_start

        # 2. Sum Tokens in current cycle
        usage_resp = await client.get(
            f"{url}/rest/v1/llm_usage_logs?user_id=eq.{user_id}&timestamp=gte.{cycle_start}&select=prompt_tokens,completion_tokens",
            headers=headers
        )
        usages = usage_resp.json()
        
        total_tokens = sum((u.get("prompt_tokens") or 0) + (u.get("completion_tokens") or 0) for u in usages)
        limit = 50000 if tier == 'free' else 1000000
        
        if total_tokens >= limit:
            raise HTTPException(
                status_code=402, 
                detail=f"Token Limit Exceeded ({total_tokens}/{limit}). Please upgrade to Pro."
            )
            
        return user_id

async def get_current_user(request: Request) -> dict:
    """JWT Token'ı doğrular ve içindeki kullanıcı verisini (payload) döner."""
    payload = await verify_jwt(request)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired session.")
    return payload

def get_supabase_client():
    """Supabase client (PostgREST) instance'ı döner (Synchronous wrappers are common in FastAPI DI)."""
    from supabase import create_client, Client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("Supabase configuration missing.")
    return create_client(url, key)

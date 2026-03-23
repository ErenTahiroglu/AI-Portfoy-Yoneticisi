import logging
import os
import httpx
from fastapi import APIRouter, HTTPException, Depends, Request
from backend.api.models import UserSettingsRequest
from backend.api.auth import verify_jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["User"])

@router.get("/alerts", dependencies=[Depends(verify_jwt)])
async def get_alerts(request: Request):
    """Kullanıcının Supabase alerts tablosundaki okunmamış son 10 bildirimini getir."""
    user = getattr(request.state, "user", None)
    if not user or "sub" not in user:
        raise HTTPException(status_code=401, detail="User Identity Not Found")

    user_id = user["sub"]
    supa_url = os.getenv('SUPABASE_URL', '')
    supa_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    
    url = f"{supa_url}/rest/v1/alerts?user_id=eq.{user_id}&is_read=eq.false&order=created_at.desc&limit=10"
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
        return []
    except Exception as e:
        logger.error(f"Alerts fetch failed: {e}")
        return []

@router.post("/alerts/read", dependencies=[Depends(verify_jwt)])
async def mark_alerts_read(request: Request):
    """Kullanıcının tüm okunmamış bildirimlerini okundu olarak işaretler."""
    user = getattr(request.state, "user", None)
    if not user or "sub" not in user:
        raise HTTPException(status_code=401, detail="User Identity Not Found")

    user_id = user["sub"]
    supa_url = os.getenv('SUPABASE_URL', '')
    supa_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    
    url = f"{supa_url}/rest/v1/alerts?user_id=eq.{user_id}&is_read=eq.false"
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    payload = {"is_read": True}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.patch(url, headers=headers, json=payload)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Mark alerts read failed: {e}")
        raise HTTPException(status_code=500, detail=f"DB Error: {e}")

@router.get("/user-settings", dependencies=[Depends(verify_jwt)])
async def get_user_settings(request: Request):
    user = getattr(request.state, "user", None)
    if not user or "sub" not in user:
        raise HTTPException(status_code=401, detail="User Identity Not Found")

    user_id = user["sub"]
    supa_url = os.getenv('SUPABASE_URL', '')
    supa_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    
    url = f"{supa_url}/rest/v1/user_settings?user_id=eq.{user_id}"
    headers = { "apikey": supa_key, "Authorization": f"Bearer {supa_key}" }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data: return data[0]
        return {"telegram_chat_id": "", "risk_tolerance": "Orta"}
    except Exception as e:
        logger.error(f"User settings fetch failed: {e}")
        return {"telegram_chat_id": "", "risk_tolerance": "Orta"}

@router.post("/user-settings", dependencies=[Depends(verify_jwt)])
async def update_user_settings(settings: UserSettingsRequest, request: Request):
    user = getattr(request.state, "user", None)
    if not user or "sub" not in user:
        raise HTTPException(status_code=401, detail="User Identity Not Found")

    user_id = user["sub"]
    supa_url = os.getenv('SUPABASE_URL', '')
    supa_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    
    url = f"{supa_url}/rest/v1/user_settings"
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    payload = {
        "user_id": user_id,
        "telegram_chat_id": settings.telegram_chat_id,
        "risk_tolerance": settings.risk_tolerance
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code not in [200, 201]:
                raise HTTPException(status_code=500, detail=f"DB Error: {resp.text}")
        return {"status": "success"}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        logger.error(f"User settings update failed: {e}")
        raise HTTPException(status_code=500, detail=f"DB Error: {e}")

@router.get("/paper-trades", dependencies=[Depends(verify_jwt)])
async def get_paper_trades(request: Request):
    user = getattr(request.state, "user", None)
    if not user or "sub" not in user: raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = user["sub"]
    supa_url = os.getenv('SUPABASE_URL', '')
    supa_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    if not supa_url or not supa_key: return []

    url = f"{supa_url}/rest/v1/paper_trades?user_id=eq.{user_id}&order=timestamp.desc&limit=50"
    headers = { "apikey": supa_key, "Authorization": f"Bearer {supa_key}" }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200: return resp.json()
        return []
    except Exception as e:
        logger.error(f"Paper trades fetch failed: {e}")
        return []

@router.get("/portfolio/history", dependencies=[Depends(verify_jwt)])
async def get_portfolio_history(request: Request):
    """Kullanıcının geçmiş portföy snapshot verilerini (son 30 gün) getirir."""
    user = getattr(request.state, "user", None)
    if not user or "sub" not in user: raise HTTPException(status_code=401, detail="Unauthorized")
    user_id = user["sub"]
    supa_url = os.getenv('SUPABASE_URL', '')
    supa_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    if not supa_url or not supa_key: return []

    url = f"{supa_url}/rest/v1/portfolio_snapshots?user_id=eq.{user_id}&order=timestamp.desc&limit=30"
    headers = { "apikey": supa_key, "Authorization": f"Bearer {supa_key}" }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200: 
                data = resp.json()
                return data[::-1]  # Kronolojik sıra (eskiden yeniye)
        return []
    except Exception as e:
        logger.error(f"Portfolio history fetch failed: {e}")
        return []

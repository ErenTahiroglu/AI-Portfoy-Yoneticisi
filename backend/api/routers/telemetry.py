import logging
import os
import httpx
from fastapi import APIRouter, HTTPException, Depends, Request
from backend.api.models import TelemetryEventRequest
from backend.api.auth import verify_jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

@router.post("/event", dependencies=[Depends(verify_jwt)])
async def log_telemetry_event(body: TelemetryEventRequest, request: Request):
    """
    Frontend veya AI Agent tarafından tetiklenen olayları (events) veritabanına kaydeder.
    Özellikle Behavioral Brake etkileşimlerini takip etmek için kullanılır.
    """
    user = getattr(request.state, "user", None)
    if not user or "sub" not in user:
        raise HTTPException(status_code=401, detail="User Identity Not Found")

    user_id = user["sub"]
    supa_url = os.getenv("SUPABASE_URL", "")
    supa_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    if not supa_url or not supa_key:
        logger.error("Supabase configuration missing for telemetry.")
        raise HTTPException(status_code=500, detail="Telemetry Config Missing")

    payload = {
        "user_id": user_id,
        "event_type": body.event_type,
        "event_metadata": body.event_metadata or {}
    }

    url = f"{supa_url}/rest/v1/user_events"
    headers = {
        "apikey": supa_key,
        "Authorization": f"Bearer {supa_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code not in (200, 201):
                logger.error(f"Telemetry log failed in DB: {resp.text}")
                # Telemetry kritik bir yol değilse kullanıcıyı bloklamayabiliriz 
                # ancak talepte "hata yakalama mekanizmaları dahil" dendiği için hata dönüyoruz.
                raise HTTPException(status_code=500, detail="Telemetry Database Error")
                
        return {"status": "success"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Telemetry endpoint exception: {e}")
        raise HTTPException(status_code=500, detail="Internal Telemetry Error")

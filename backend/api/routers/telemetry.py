from fastapi import APIRouter, Depends, HTTPException
from backend.api.dependencies import get_current_user, get_supabase_client
from backend.api.models import TelemetryEventRequest
import logging

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])
logger = logging.getLogger(__name__)

@router.post("/event")
async def log_event(
    request: TelemetryEventRequest,
    current_user: dict = Depends(get_current_user),
    supabase = Depends(get_supabase_client)
):
    """
    Kullanıcı etkileşimlerini (örn: Behavioral Brake tepkileri) loglayan telemetri endpoint'i.
    Hata durumunda sessizce fail etmek yerine 500 döner (İstekte belirtildiği üzere).
    """
    try:
        user_id = current_user.get("sub")
        data = {
            "user_id": user_id,
            "event_type": request.event_type,
            "event_metadata": request.event_metadata
        }
        # Supabase'e kaydet
        supabase.table("user_events").insert(data).execute()
        return {"status": "success", "message": "Olay başarıyla kaydedildi."}
    except Exception as e:
        logger.error(f"Telemetri loglama hatası: {str(e)}")
        # Loglama işlemi ana akışı bozmamalı, ancak endpoint bazında hata dönüyoruz.
        raise HTTPException(status_code=500, detail="Olay kaydedilemedi.")

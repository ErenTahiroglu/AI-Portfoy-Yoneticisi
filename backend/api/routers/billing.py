import os
import httpx
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime

from backend.api.auth import verify_jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["Billing"])

@router.post("/upgrade", dependencies=[Depends(verify_jwt)])
async def upgrade_subscription(request: Request):
    """
    Kullanıcı aboneliğini 'pro' tier'a yükseltir (Mock Simulation).
    billing_cycle_start değerini günceller.
    """
    user = getattr(request.state, "user", None)
    user_id = user["sub"] if user else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication failed.")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
         raise HTTPException(status_code=500, detail="Supabase configs missing.")

    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            payload = {
                "subscription_tier": "pro",
                "billing_cycle_start": datetime.utcnow().isoformat()
            }
            # Upsert into user_settings
            # We can use upsert if user_id is PK
            resp = await client.post(
                f"{url}/rest/v1/user_settings",
                json={**payload, "user_id": user_id},
                headers=headers
            )
            # If item does not exist, post does insert. If exists, it might fail if row PK already exists unlees Prefer: resolution is specified.
            # PostgREST Upsert syntax: Prefer: resolution=merge-duplicates ON CONFLICT (user_id) 
            # Or use PATCH on id equality!
            # Let's use PATCH since user_settings has to exist usually
            patch_resp = await client.patch(
                f"{url}/rest/v1/user_settings?user_id=eq.{user_id}",
                json=payload,
                headers=headers
            )
            
            # If row doesn't exist, PATCH does nothing (204 or 404 depending on config)
            # Safe boundary check:
            # Let's do a GET first, then patch or post
            get_resp = await client.get(f"{url}/rest/v1/user_settings?user_id=eq.{user_id}", headers=headers)
            if get_resp.json():
                 await client.patch(f"{url}/rest/v1/user_settings?user_id=eq.{user_id}", json=payload, headers=headers)
            else:
                 await client.post(f"{url}/rest/v1/user_settings", json={**payload, "user_id": user_id}, headers=headers)
                 
            return {"status": "success", "message": "Aboneliğiniz başarıyla Pro sürümüne yükseltildi!", "tier": "pro"}

    except Exception as e:
        logger.error(f"Upgrade failed: {e}")
        raise HTTPException(status_code=500, detail="Abonelik işlemi gerçekleştirilemedi.")

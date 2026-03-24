import os
import httpx
import logging
import hashlib
import hmac
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from datetime import datetime

from backend.api.auth import verify_jwt

logger = logging.getLogger(__name__)

# Canlıda bu ENV'den okunmalıdır
WEBHOOK_SECRET = os.getenv("BILLING_WEBHOOK_SECRET", "superior_mock_webhook_secret_123")

router = APIRouter(prefix="/api/billing", tags=["Billing"])

@router.post("/upgrade", dependencies=[Depends(verify_jwt)])
async def upgrade_subscription(request: Request):
    """
    Kullanıcı aboneliğini 'pro' tier'a yükseltir (Simulation).
    NOT: Bu rota ödeme gateway'i (Stripe vb.) entegre edilene kadar simülasyondur.
    """
    user = getattr(request.state, "user", None)
    user_id = user["sub"] if user else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication failed.")

    logger.info(f"Billing: Processing mock upgrade for user {user_id}")
    return await _process_upgrade_db(user_id)


@router.post("/webhook")
async def billing_webhook(
    request: Request, 
    x_webhook_signature: str = Header(None),
    x_webhook_timestamp: str = Header(None)
):
    """
    Simüle edilmiş Ödeme Sağlayıcı (Stripe/Iyzico) Webhook Alıcısı.
    • 🛡️ Kriptografik İmza Doğrulaması (Signature Verification)
    • 🛡️ Replay Attack (Zaman Damgası) Koruması
    • 🛡️ Idempotens (Mükerrer İşlem) Engelleme
    """
    body = await request.body()
    
    if not x_webhook_signature or not x_webhook_timestamp:
         logger.warning("Billing Webhook: Missing required verification headers.")
         raise HTTPException(status_code=400, detail="Missing signature headers.")

    # 1. 🛡️ Replay Attack Protection (Timestamp Validity)
    try:
        req_ts = int(x_webhook_timestamp)
        now_ts = int(datetime.utcnow().timestamp())
        if abs(now_ts - req_ts) > 300: # 5 Dakikadan eski talepleri reddet
            logger.warning("Billing Webhook: Replay attack detected (Expired timestamp).")
            raise HTTPException(status_code=400, detail="Request timestamp expired.")
    except Exception:
         raise HTTPException(status_code=400, detail="Invalid timestamp format.")

    # 2. 🛡️ Cryptographic Signature Verification (HMAC-SHA256)
    expected_string = f"{x_webhook_timestamp}.{body.decode('utf-8')}"
    valid_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        expected_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(valid_signature, x_webhook_signature):
         logger.warning("Billing Webhook: Cryptographic Signature Mismatch! Fraud Attempt blocked.")
         raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    event_id = payload.get("event_id")
    user_id = payload.get("user_id")

    if not event_id or not user_id:
         raise HTTPException(status_code=400, detail="Invalid payload: Missing event_id or user_id")

    # 3. 🛡️ Idempotency / Double Submit Check (Redis)
    from backend.core.redis_cache import cache_get, cache_set
    processed_key = f"webhook:processed:{event_id}"
    if cache_get(processed_key):
         logger.info(f"Billing Webhook: Event {event_id} already processed. Skipping.")
         return {"status": "success", "message": "Already processed"}

    # İşleme Devam Et
    res = await _process_upgrade_db(user_id)
    
    # Event_ID'yi 24 saatliğine cache'e kaydet (Replay engellemek için)
    cache_set(processed_key, "true", ttl=86400)
    
    logger.info(f"Billing Webhook: Successfully processed event {event_id} for user {user_id}")
    return res


async def _process_upgrade_db(user_id: str):
    """DB üzerinde aboneliği pro'ya çeviren yardımcı metot."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
         raise HTTPException(status_code=500, detail="Supabase configs missing.")

    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            }
            payload = {
                "subscription_tier": "pro",
                "billing_cycle_start": datetime.utcnow().isoformat()
            }
            # UPSERT Simulation (Read first)
            get_resp = await client.get(f"{url}/rest/v1/user_settings?user_id=eq.{user_id}", headers=headers)
            if get_resp.json():
                 await client.patch(f"{url}/rest/v1/user_settings?user_id=eq.{user_id}", json=payload, headers=headers)
            else:
                 await client.post(f"{url}/rest/v1/user_settings", json={**payload, "user_id": user_id}, headers=headers)
                 
            return {"status": "success", "message": "İşlem Başarılı!", "tier": "pro"}
    except Exception as e:
         logger.error(f"Subscription process failed: {e}")
         raise HTTPException(status_code=500, detail="Abonelik işlemi gerçekleştirilemedi.")

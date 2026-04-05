import os
import jwt
import logging
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

# Supabase Auth Settings -> JWT Secret (E.g. from Dashboard)
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

def verify_token_string(token: str) -> dict:
    """
    Ham JWT token string'ini doğrular. 
    WebSocket ve harici akışlar için yardımcı fonksiyondur.
    """
    if not SUPABASE_JWT_SECRET:
         logger.error("❌ SUPABASE_JWT_SECRET is not set. Auth will fail.")
         raise HTTPException(
             status_code=500, 
             detail="Server configuration error: Auth secret missing."
         )

    # 🛡️ REDIS BLOCKLIST KONTROLÜ
    try:
         from backend.infrastructure.redis_cache import cache_get
         # Token çalıntı/kapatılmış mı sorgula
         if cache_get(f"jwt_blacklist:{token}"):
              logger.warning("Zero Trust: Revoked token presented.")
              raise HTTPException(status_code=401, detail="This session has been signed out.")
    except HTTPException:
         # Yeniden fırlat (Auth blacklist vb. durumlar)
         raise
    except Exception as e:
         # Redis hatası auth akışını bozmamalı (Fallback)
         logger.warning(f"Auth Redis check failed: {e}. Proceeding with standard JWT check.")
         pass

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": True},
            audience="authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Zero Trust: Token expired.")
        raise HTTPException(status_code=401, detail="Token has expired. Please sign in again.")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Zero Trust: Invalid token context -> {str(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid authentication token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected Auth Error: {e}")
        raise HTTPException(status_code=401, detail="Authentication processing error.")


async def verify_jwt(request: Request):
    """
    Supabase'ten dönen Authorization: Bearer <token> bilgisini kontrol eder.
    Sıfır Güven (Zero Trust) IAM Katmanı.
    """
    authorization = request.headers.get("Authorization")
    
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Zero Trust: Missing or invalid Authorization header.")
        raise HTTPException(status_code=401, detail="Authentication required (Bearer token missing).")

    token = authorization.split(" ")[1]
    payload = verify_token_string(token)
    request.state.user = payload
    return payload

import os
import jwt
import logging
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

# Supabase Auth Settings -> JWT Secret (E.g. from Dashboard)
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

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
    
    # Secret yoksa dahi token onayı verilemez (Zero Trust)
    if not SUPABASE_JWT_SECRET:
        logger.error("Zero Trust Error: SUPABASE_JWT_SECRET is not set in environment.")
        raise HTTPException(status_code=500, detail="Server IAM configuration error.")

    try:
        # Supabase JWT token imzasını doğrula (HS256)
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": True},
            audience="authenticated"
        )
        # Token geçerli, payload'u (user_id vb.) request state'e göm
        request.state.user = payload
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Zero Trust: Token expired.")
        raise HTTPException(status_code=401, detail="Token has expired. Please sign in again.")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Zero Trust: Invalid token context -> {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid authentication token.")

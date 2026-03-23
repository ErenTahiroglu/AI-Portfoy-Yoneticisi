"""
🔐 JWT Bazlı Rate Limiter — P2 Öncelik Matrisi
===============================================
Sliding Window Algoritması.
• Kimliği doğrulanmış kullanıcılar (Supabase JWT): user_id bazlı limit
• Anonim kullanıcılar: IP bazlı limit (geriye dönük uyumlu)

Sorun çözüldü: Tüm Vercel trafiği aynı egress IP'yi paylaşıyordu,
bu nedenle bir kullanıcı diğerlerini throttle edebiliyordu.
"""
import asyncio
import base64
import json
import logging
import time
from typing import Optional

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


def _extract_user_id(authorization: Optional[str]) -> Optional[str]:
    """JWT'nin payload kısmından user ID'yi decode eder (signature doğrulaması olmadan).
    Güvenlik: Bu yalnızca rate-limit key oluşturma için kullanılır.
    Supabase'in kendi signature doğrulaması zaten client tarafında yapılır."""
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        return None
    auth_str: str = authorization
    token = auth_str[7:]
    try:
        # JWT = header.payload.signature — payload'ı base64 decode et
        parts = token.split(".")
        if len(parts) != 3:
            return None
        # Padding tamamla
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload.get("sub")  # Supabase user UUID
    except Exception:
        return None


class RateLimiter:
    """
    Bellek dostu asenkron Rate Limiter (Sliding Window Algorithm).
    JWT user ID bazlı (authenticated) + IP bazlı (anonymous) hibrit.
    Redis destekli (Cluster ve Multi-Worker uyumlu).
    """

    def __init__(self, requests_limit: int = 3, period: int = 60):
        self.limit = requests_limit
        self.period = period
        self.lock = asyncio.Lock()

    async def check(self, request: Request):
        from backend.core import redis_cache

        # ── Kimlik Anahtarı Belirleme (Proxy Trust Hardening) ──────────────
        auth_header = request.headers.get("Authorization")
        user_id = _extract_user_id(auth_header)

        if user_id:
            limit_key = f"rate_limit:user:{user_id}"
            identifier_type = "user"
        else:
            # X-Real-IP Render ve Vercel'de güvenilirdir.
            client_ip = request.headers.get("X-Real-IP")
            if not client_ip:
                 forwarded = request.headers.get("X-Forwarded-For")
                 client_ip = forwarded.split(",")[-1].strip() if forwarded else (request.client.host if request.client else "unknown")
            
            if client_ip == "unknown":
                return
            limit_key = f"rate_limit:ip:{client_ip}"
            identifier_type = "ip"

        now = time.time()

        async with self.lock:
            # 1. Cache'den geçmişi oku (Redis veya In-memory L1 Fallback)
            history_data = await asyncio.to_thread(redis_cache.cache_get, limit_key)
            timestamps = history_data if isinstance(history_data, list) else []

            # 2. Süresi dolmuş timestamp'leri temizle
            timestamps = [t for t in timestamps if now - t < self.period]

            # 3. Limit Kontrolü
            if len(timestamps) >= self.limit:
                logger.warning(f"Rate Limit aşıldı [{identifier_type}]: {limit_key}")
                raise HTTPException(
                    status_code=429,
                    detail="API Kotasını aştınız, lütfen 1 dakika bekleyin",
                )

            # 4. Yeni isteği ekle ve kaydet
            timestamps.append(now)
            await asyncio.to_thread(redis_cache.cache_set, limit_key, timestamps, ttl=self.period)


# Varsayılan limit: 1 dakikada 3 analiz isteği
limiter = RateLimiter(requests_limit=3, period=60)

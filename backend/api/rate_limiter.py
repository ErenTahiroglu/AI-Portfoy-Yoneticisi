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
    """

    def __init__(self, requests_limit: int = 3, period: int = 60):
        self.limit = requests_limit
        self.period = period
        self.history: dict = {}  # {key: [timestamp, ...]}
        self.lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def _cleanup_loop(self):
        """Arka plan temizlik döngüsü (eski timestamp'leri ve boş key'leri siler)."""
        while True:
            await asyncio.sleep(60)
            now = time.time()
            async with self.lock:
                to_remove = []
                for k, timestamps in self.history.items():
                    self.history[k] = [t for t in timestamps if now - t < self.period]
                    if not self.history[k]:
                        to_remove.append(k)
                for k in to_remove:
                    self.history.pop(k, None)

    async def check(self, request: Request):
        # Arka plan temizlik görevini bir kez başlat (Race condition korumalı)
        if not self._cleanup_task:
            async with self.lock:
                if not self._cleanup_task:
                    self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        # ── Kimlik Anahtarı Belirleme ──────────────────────────────────────
        auth_header = request.headers.get("Authorization")
        user_id = _extract_user_id(auth_header)

        if user_id:
            # Authenticated: user UUID bazlı limit (Vercel IP bypass problemi çözüldü)
            limit_key = f"user:{user_id}"
            identifier_type = "user"
        else:
            # Anonymous: IP bazlı fallback
            forwarded = request.headers.get("X-Forwarded-For")
            client_ip = (
                forwarded.split(",")[0].strip()
                if forwarded
                else (request.client.host if request.client else "unknown")
            )
            if client_ip == "unknown":
                return  # IP tespit edilemezse limiti atla
            limit_key = f"ip:{client_ip}"
            identifier_type = "ip"

        now = time.time()

        async with self.lock:
            if limit_key not in self.history:
                self.history[limit_key] = []

            # Süresi dolmuş timestamp'leri temizle
            self.history[limit_key] = [
                t for t in self.history[limit_key] if now - t < self.period
            ]

            if len(self.history[limit_key]) >= self.limit:
                logger.warning(
                    f"Rate Limit aşıldı [{identifier_type}]: {limit_key}"
                )
                raise HTTPException(
                    status_code=429,
                    detail="API Kotasını aştınız, lütfen 1 dakika bekleyin",
                )

            self.history[limit_key].append(now)


# Varsayılan limit: 1 dakikada 3 analiz isteği
limiter = RateLimiter(requests_limit=3, period=60)

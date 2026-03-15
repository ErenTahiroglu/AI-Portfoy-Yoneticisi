import time
import asyncio
import logging
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Bellek dostu asenkron Rate Limiter (Sliding Window Algorithm).
    Redis olmadan Render.com free tier gibi ortamlarda calismak icin tasarlanmistir.
    """
    def __init__(self, requests_limit: int = 3, period: int = 60):
        self.limit = requests_limit
        self.period = period
        self.history = {} # {ip: [timestamp, ...]}
        self.lock = asyncio.Lock()

    async def check(self, request: Request):
        # Reverse proxy (Render/Vercel) arkasindaki IP'yi yakala
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
        
        if client_ip == "unknown":
            return # IP tespit edilemezse limiti atla (guvenlik acigi olmamasi icin logla)
            
        now = time.time()
        
        async with self.lock:
            if client_ip not in self.history:
                self.history[client_ip] = []
                
            # Süresi dolmuş (eski) zaman damgalarını temizle
            self.history[client_ip] = [t for t in self.history[client_ip] if now - t < self.period]
            
            if len(self.history[client_ip]) >= self.limit:
                logger.warning(f"Rate Limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=429, 
                    detail="API Kotasını aştınız, lütfen 1 dakika bekleyin"
                )
                
            self.history[client_ip].append(now)

# Varsayılan limit: 1 dakikada 3 analiz isteği
limiter = RateLimiter(requests_limit=3, period=60)

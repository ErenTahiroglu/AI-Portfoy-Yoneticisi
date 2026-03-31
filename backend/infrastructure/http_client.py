import httpx
from typing import Optional

# Global Singleton HTTP Client for TCP Connection Pooling
# Prevent Socket Exhaustion during async Fan-Out requests (Zombie connections on Free Tiers)
global_http_client: Optional[httpx.AsyncClient] = None

def init_global_http_client():
    global global_http_client
    if global_http_client is None:
        global_http_client = httpx.AsyncClient(
            # 🛡️ Sıkılaştırılmış Free-Tier Limitleri (Render & Supabase Koruması)
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            timeout=httpx.Timeout(15.0) # Cold start / Slow response tolerance
        )

async def close_global_http_client():
    global global_http_client
    if global_http_client is not None:
        await global_http_client.aclose()
        global_http_client = None

def get_http_client() -> httpx.AsyncClient:
    global global_http_client
    if global_http_client is None:
        init_global_http_client()
    return global_http_client

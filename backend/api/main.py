"""
🧩 Puzzle Parça: API Giriş Noktası (Entrypoint) — v4.0
======================================================
FastAPI uygulamasını başlatır, middleware'leri tanımlar ve
dekuple edilmiş router'ları include eder.
"""

import os
import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from backend.infrastructure.scheduler import start_alert_scheduler
from backend.api.websocket import register_websocket_routes
from backend.utils.logger import setup_logging, CorrelationIdMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import sys

def validate_critical_env():
    """Kritik ortam değişkenlerini başlatmadan önce doğrular (Fail-Fast)."""
    if "pytest" in sys.modules:
        return # Test çalışırken validation atla
        
    critical_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [v for v in critical_vars if not os.getenv(v)]
    if missing:
        # 🛡️ Gevşetilmiş hata (Sistemin kalkmasına izin verir, ama log'a basar)
        print(f"⚠️ UYARI: Kritik ortam değişkenleri eksik: {', '.join(missing)}")
        print("Sistem işlevleri (Örn: DB, Auth) kısıtlı çalışabilir.")

validate_critical_env()


# ── Logging Setup ─────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)


# ── Lifespan (Background Tasks) ───────────────────────────────────────────
from backend.infrastructure.redis_cache import cache_close
from backend.infrastructure.http_client import init_global_http_client, close_global_http_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # API kalktığında HTTP Client havuzunu başlat
    init_global_http_client()
    
    # API kalktığında otonom tarayıcıyı ayağa kaldır
    task = asyncio.create_task(start_alert_scheduler())
    yield
    # API kapandığında memory leak olmaması için iptal et
    task.cancel()
    # Redis ve HTTP havuzunu kapat (Graceful Shutdown)
    try:
        await close_global_http_client()
        cache_close()
        logger.info("✅ Redis & HTTP Sessions safely closed.")
    except Exception as e:
         logger.warning(f"Error during shutdown closures: {e}")

# ── FastAPI Uygulaması ────────────────────────────────────────────────────
is_prod = os.getenv("ENVIRONMENT", "production").lower() == "production"

app = FastAPI(
    title="Portföy Analiz Platformu", 
    version="4.0", 
    lifespan=lifespan,
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc"
)

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# ── Middleware: No-Cache ──────────────────────────────────────────────────
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/ui"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(NoCacheMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ── Middleware: CORS ──────────────────────────────────────────────────────
origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500,https://ai-destekli-portfoy-yoneticisi.vercel.app")
origins = [o.strip() for o in origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── WebSocket Entegrasyonu ────────────────────────────────────────────────
register_websocket_routes(app)

# ── Sub-Routers Include ───────────────────────────────────────────────────
from backend.api.routers import analysis, chat, user, admin, billing, telemetry

app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(billing.router)
app.include_router(telemetry.router)

# ── Root Redirect & Static Files (Frontend) ───────────────────────────────
@app.get("/api/health")
async def health_check():
    """
    Sistem Sağlık Kontrolü (Liveness Probe).
    🛡️ Render/K8s çökme döngüsünü engeller, DB & Redis denetler.
    """
    health_status = {"status": "ok", "redis": "connected", "supabase": "connected"}
    
    # 1. Redis Check
    from backend.infrastructure.redis_cache import cache_is_redis_active
    if not cache_is_redis_active():
        health_status["redis"] = "disconnected (fallback active)"

    # 2. Supabase Check
    try:
        import httpx
        from backend.infrastructure.scheduler import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
        }
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Basit bir limit=1 query atarak bağlantıyı test edelim
            resp = await client.get(f"{SUPABASE_URL}/rest/v1/portfolios?limit=1", headers=headers)
            if resp.status_code not in (200, 206):
                health_status["supabase"] = f"error (HTTP {resp.status_code})"
                health_status["status"] = "degraded"
    except Exception as e:
         health_status["supabase"] = f"error: {str(e)}"
         health_status["status"] = "critical"

    return health_status

@app.get("/api/metrics")
async def get_metrics():
    """
    📊 Uygulama Telemetri Verileri (Monitoring).
    🛡️ Anlık aktif WebSocket bağlantı sayılarını ve sağlık özetini döner.
    """
    from backend.api.websocket import _clients
    from datetime import datetime, timezone
    return {
        "active_websocket_connections": len(_clients),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/")
def read_root():
    return RedirectResponse(url="/ui")

base_dir = os.path.dirname(os.path.abspath(__file__))
# In Monorepo, /frontend is at the root, 2 levels up from backend/api/
frontend_path = os.path.join(os.path.dirname(os.path.dirname(base_dir)), "frontend")


if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")
else:
    logger.warning(f"Frontend Static path not found at {frontend_path}")

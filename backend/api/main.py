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

from backend.core.scheduler import start_alert_scheduler
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
        print(f"❌ KRİTİK HATA: Aşağıdaki ortam değişkenleri eksik: {', '.join(missing)}")
        print("Sistem Fail-Fast prensibiyle başlatmayı reddediyor.")
        sys.exit(1)

validate_critical_env()


# ── Logging Setup ─────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)


# ── Lifespan (Background Tasks) ───────────────────────────────────────────
from backend.core.redis_cache import cache_close

@asynccontextmanager
async def lifespan(app: FastAPI):
    # API kalktığında otonom tarayıcıyı ayağa kaldır
    task = asyncio.create_task(start_alert_scheduler())
    yield
    # API kapandığında memory leak olmaması için iptal et
    task.cancel()
    # Redis kapat (Graceful Shutdown)
    try:
        cache_close()
        logger.info("✅ Redis session safely closed.")
    except Exception as e:
         logger.warning(f"Error during Redis close: {e}")

# ── FastAPI Uygulaması ────────────────────────────────────────────────────
is_prod = os.getenv("ENVIRONMENT", "production").lower() == "production"

app = FastAPI(
    title="Portföy Analiz Platformu", 
    version="4.0", 
    lifespan=lifespan,
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc"
)

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
from backend.api.routers import analysis, chat, user, admin, billing

app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(billing.router)

# ── Root Redirect & Static Files (Frontend) ───────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Portföy Analiz API aktif"}

@app.get("/")
def read_root():
    return RedirectResponse(url="/ui")

base_dir = os.path.dirname(os.path.abspath(__file__))
# In Monorepo, /frontend is at the root, 2 levels up from backend/api/
frontend_path = os.path.join(os.path.dirname(os.path.dirname(base_dir)), "frontend")
LineNumber:86


if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")
else:
    logger.warning(f"Frontend Static path not found at {frontend_path}")

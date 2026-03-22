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

from src.core.scheduler import start_alert_scheduler
from src.api.websocket import register_websocket_routes
from starlette.middleware.base import BaseHTTPMiddleware

# ── Logging Setup ─────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Lifespan (Background Tasks) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # API kalktığında otonom tarayıcıyı ayağa kaldır
    task = asyncio.create_task(start_alert_scheduler())
    yield
    # API kapandığında memory leak olmaması için iptal et
    task.cancel()

# ── FastAPI Uygulaması ────────────────────────────────────────────────────
app = FastAPI(title="Portföy Analiz Platformu", version="4.0", lifespan=lifespan)

# ── Middleware: No-Cache ──────────────────────────────────────────────────
class NoCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/ui"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

app.add_middleware(NoCacheMiddleware)

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
from src.api.routers import analysis, chat, user

app.include_router(analysis.router)
app.include_router(chat.router)
app.include_router(user.router)

# ── Root Redirect & Static Files (Frontend) ───────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Portföy Analiz API aktif"}

@app.get("/")
def read_root():
    return RedirectResponse(url="/ui")

base_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.join(os.path.dirname(base_dir), "frontend")

if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="ui")
else:
    logger.warning(f"Frontend Static path not found at {frontend_path}")

import logging
import json
import uuid
import contextvars
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

# ── Correlation ID Context ───────────────────────────────────────────────
correlation_id_ctx = contextvars.ContextVar("correlation_id", default="")

# ── FastAPI Middleware ───────────────────────────────────────────────────
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract from header or generate new
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        token = correlation_id_ctx.set(corr_id)
        
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = corr_id
            return response
        finally:
            correlation_id_ctx.reset(token)

# ── JSON Formatter ───────────────────────────────────────────────────────
class JsonFormatter(logging.Formatter):
    def format(self, record):
        correlation_id = correlation_id_ctx.get()
        
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)

# ── Logger Setup ──────────────────────────────────────────────────────────
def setup_logging(level=logging.INFO):
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)
    
    # Prevent uvicorn from overriding our formatter for access logs
    uvicorn_logger = logging.getLogger("uvicorn")
    if uvicorn_logger.handlers:
        uvicorn_logger.handlers[0].setFormatter(JsonFormatter())
    uvicorn_access = logging.getLogger("uvicorn.access")
    if uvicorn_access.handlers:
        uvicorn_access.handlers[0].setFormatter(JsonFormatter())

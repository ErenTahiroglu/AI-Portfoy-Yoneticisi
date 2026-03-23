import logging
import json
import uuid
import contextvars
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import os
from logging.handlers import RotatingFileHandler

# ── Correlation ID Context ───────────────────────────────────────────────
correlation_id_ctx = contextvars.ContextVar("correlation_id", default="")

# ── Audit Logger (Log Rotation) ───────────────────────────────────────────
audit_logger = logging.getLogger("audit_trail")
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False # Console'a basmasın

# Avoid duplicates
if not audit_logger.handlers:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "ai_audit_trail.log")
    
    # maxBytes=5MB, backupCount=3 (Total ~20MB safety cap)
    rot_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    rot_handler.setFormatter(logging.Formatter('%(message)s'))
    audit_logger.addHandler(rot_handler)

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
        message = record.getMessage()
        
        # Hassas Veri Maskeleme (PII / Secret Masking)
        import re
        sensitive_patterns = [
            (r'(?i)(bearer\s+)[a-zA-Z0-9\.\-_]+', r'\1********'),
            (r'(?i)(password["\']?\s*[:=]\s*["\']?)[^"\'\s,]+', r'\1********'),
            (r'(?i)(api[_-]?key["\']?\s*[:=]\s*["\']?)[^"\'\s,]+', r'\1********'),
        ]
        for pattern, repl in sensitive_patterns:
            message = re.sub(pattern, repl, message)

        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
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

"""
🔴 Redis Cache Adaptörü — P1 Öncelik Matrisi
============================================
Upstash Redis (REST API) → dışsal dağıtık cache.
UPSTASH_REDIS_REST_URL ayarlanmadıysa sessizce
in-memory sözlüğe fallback yapar.

Mimari Not:
  • Upstash: serverless HTTP tabanlı Redis (bağlantı havuzu gereksiz)
  • TTL: Redis tarafında native EX komutuyla yönetilir
  • In-Process Fallback: Production ortamında Redis bağlanamazsa sistem çökmez
"""
import json
import logging
import os
import time
import httpx
import threading
from typing import Optional, Any

logger = logging.getLogger(__name__)

# ── In-Memory Fallback ────────────────────────────────────────────────────
# KESİN UYARI: Bu in-memory fallback yapısı sadece SINGLE-WORKER (tek işçi) ortamlarında çalışır.
# Çoklu worker (Gunicorn/Uvicorn workers > 1) veya serverless (Vercel) gibi ortamlarda state paylaşılamaz
# ve polling (Durum kontrol) işlemleri tutarsızlıklarla (404 Not Found) sonuçlanır.
_LOCAL: dict = {}

# ── Standard Redis (TCP) & Upstash (REST) Client ───────────────────────────
try:
    import redis
except ImportError:
    redis = None

_UPSTASH_URL: Optional[str] = os.getenv("UPSTASH_REDIS_REST_URL")
_UPSTASH_TOKEN: Optional[str] = os.getenv("UPSTASH_REDIS_REST_TOKEN")
_REDIS_URL: Optional[str] = os.getenv("REDIS_URL") # e.g. redis://localhost:6379

_redis_available: bool = False
_redis_mode: Optional[str] = None # "standard" or "upstash"
_SESSION: Optional[httpx.Client] = None
_REDIS_CONN: Optional[Any] = None

# 1. Try Standard Redis (TCP) - Best for Local/Docker
if _REDIS_URL and redis:
    try:
        _REDIS_CONN = redis.from_url(_REDIS_URL, decode_responses=True, socket_timeout=2.0)
        _REDIS_CONN.ping()
        _redis_available = True
        _redis_mode = "standard"
        logger.info(f"✅ Standard Redis (TCP) bağlantısı hazır: {_REDIS_URL}")
    except Exception as e:
        logger.warning(f"⚠️ Standard Redis fail: {e}")

# 2. Try Upstash (REST) - Best for Serverless/Render
if not _redis_available and _UPSTASH_URL and _UPSTASH_TOKEN:
    try:
        _SESSION = httpx.Client(timeout=2.0)
        _redis_available = True
        _redis_mode = "upstash"
        logger.info("✅ Upstash Redis (REST) bağlantısı hazır.")
    except Exception as e:
        _redis_available = False
        logger.warning(f"⚠️ Upstash setup error: {e} — in-memory fallback aktif.")

if not _redis_available:
    logger.info("ℹ️ Redis tanımlı değil veya bağlanılamadı — in-memory cache kullanılıyor.")


def _upstash_headers() -> dict:
    return {
        "Authorization": f"Bearer {_UPSTASH_TOKEN}",
        "Content-Type": "application/json",
    }


def cache_get(key: str) -> Optional[dict]:
    """Cache'den veri okur. Redis varsa Redis'i, yoksa in-memory'yi kullanır."""
    if _redis_available:
        if _redis_mode == "standard" and _REDIS_CONN:
            try:
                res = _REDIS_CONN.get(key)
                if res:
                    logger.debug(f"💾 Standard Redis cache hit: {key}")
                    return json.loads(res)
            except Exception as e:
                logger.warning(f"Standard Redis GET error: {e}")
                
        elif _redis_mode == "upstash" and _UPSTASH_URL and _SESSION:
            try:
                resp = _SESSION.get(
                    f"{_UPSTASH_URL}/get/{key}",
                    headers=_upstash_headers()
                )
                resp.raise_for_status() # Limitlere/hatalara takılırsa in-memory'ye düşür
                if resp.status_code == 200:
                    result = resp.json().get("result")
                    if result:
                        logger.debug(f"💾 Upstash Redis cache hit: {key}")
                        return json.loads(result)
            except Exception as e:
                logger.warning(f"Upstash GET hatası ({key}): {e} — in-memory fallback.")

    # In-memory fallback
    entry = _LOCAL.get(key)
    if entry and time.time() - entry["ts"] < entry["ttl"]:
        logger.debug(f"💾 In-memory cache hit: {key}")
        return entry["data"]
    if key in _LOCAL:
        del _LOCAL[key]
    return None


def cache_set(key: str, data: dict, ttl: int = 300) -> None:
    """Cache'e veri yazar. Redis varsa Redis'e, her durumda in-memory'ye de yazar."""
    serialized = json.dumps(data, ensure_ascii=False)

    if _redis_available:
        if _redis_mode == "standard" and _REDIS_CONN:
            try:
                _REDIS_CONN.set(key, serialized, ex=ttl)
                logger.debug(f"✍️ Standard Redis cache set: {key} (TTL={ttl}s)")
            except Exception as e:
                logger.warning(f"Standard Redis SET error: {e}")
                
        elif _redis_mode == "upstash" and _UPSTASH_URL and _SESSION:
            try:
                resp = _SESSION.post(
                    f"{_UPSTASH_URL}/set/{key}",
                    headers=_upstash_headers(),
                    content=json.dumps([serialized, "EX", ttl])
                )
                resp.raise_for_status()
                logger.debug(f"✍️ Upstash Redis cache set: {key} (TTL={ttl}s)")
            except Exception as e:
                logger.warning(f"Upstash SET hatası ({key}): {e} — sadece in-memory yazıldı.")

    # Her zaman in-memory'ye de yaz (ultra-hız için L1 cache gibi)
    _LOCAL[key] = {"ts": time.time(), "ttl": ttl, "data": data}

    # In-memory boyutunu 150 entry ile sınırla
    if len(_LOCAL) > 150:
        try:
            oldest = next(iter(_LOCAL))
            del _LOCAL[oldest]
        except StopIteration:
            pass


def cache_delete(key: str) -> None:
    """Belirli bir cache entry'sini geçersiz kılar."""
    _LOCAL.pop(key, None)
    if _redis_available:
        if _redis_mode == "standard" and _REDIS_CONN:
            try:
                _REDIS_CONN.delete(key)
            except Exception:
                pass
        elif _redis_mode == "upstash" and _UPSTASH_URL and _SESSION:
            try:
                _SESSION.get(f"{_UPSTASH_URL}/del/{key}", headers=_upstash_headers())
            except Exception:
                pass


def cache_is_redis_active() -> bool:
    """Redis'in aktif olup olmadığını döndürür (health check için)."""
    return _redis_available

def cache_close() -> None:
    """Modül sonlanırken açık HTTP Client oturumunu kapatır (Graceful Shutdown)."""
    global _SESSION
    if _SESSION:
        try:
            _SESSION.close()
        except Exception:
            pass

# ── Cache Stampede (İzdiham) Koruması ────────────────────────────────────
_locks = {}
_lock_access = threading.Lock()

def cache_get_lock(key: str) -> threading.Lock:
    """
    🛡️ Cache Stampede Mutex (Önleme Kilidi).
    Ağır hesaplamalar öncesinde `with cache_get_lock(key):` kullanılarak
    aynı anda yüzlerce thread'in DB'ye vurması engellenir.
    """
    with _lock_access:
        if key not in _locks:
            _locks[key] = threading.Lock()
        return _locks[key]

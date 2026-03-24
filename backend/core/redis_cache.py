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
from typing import Optional

logger = logging.getLogger(__name__)

# ── In-Memory Fallback ────────────────────────────────────────────────────
_LOCAL: dict = {}

# ── Upstash REST Client ───────────────────────────────────────────────────
import httpx

_UPSTASH_URL: Optional[str] = os.getenv("UPSTASH_REDIS_REST_URL")
_UPSTASH_TOKEN: Optional[str] = os.getenv("UPSTASH_REDIS_REST_TOKEN")
_redis_available: bool = False
_SESSION: Optional[httpx.Client] = None

if _UPSTASH_URL and _UPSTASH_TOKEN:
    try:
        _redis_available = True
        _SESSION = httpx.Client(timeout=2.0) # Connection Pool setup
        logger.info("✅ Upstash Redis bağlantısı (Connection Pool) hazır.")
    except Exception as e:
        logger.warning(f"⚠️ Redis setup error: {e} — in-memory fallback aktif.")
else:
    logger.info("ℹ️ UPSTASH_REDIS_REST_URL tanımlı değil — in-memory cache kullanılıyor.")


def _upstash_headers() -> dict:
    return {
        "Authorization": f"Bearer {_UPSTASH_TOKEN}",
        "Content-Type": "application/json",
    }


def cache_get(key: str) -> Optional[dict]:
    """Cache'den veri okur. Redis varsa Redis'i, yoksa in-memory'yi kullanır."""
    if _redis_available and _UPSTASH_URL and _SESSION:
        try:
            resp = _SESSION.get(
                f"{_UPSTASH_URL}/get/{key}",
                headers=_upstash_headers()
            )
            if resp.status_code == 200:
                result = resp.json().get("result")
                if result:
                    logger.debug(f"💾 Redis cache hit: {key}")
                    return json.loads(result)
        except Exception as e:
            logger.warning(f"Redis GET hatası ({key}): {e} — in-memory fallback.")

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

    if _redis_available and _UPSTASH_URL and _SESSION:
        try:
            _SESSION.post(
                f"{_UPSTASH_URL}/set/{key}",
                headers=_upstash_headers(),
                content=json.dumps([serialized, "EX", ttl])
            )
            logger.debug(f"✍️ Redis cache set: {key} (TTL={ttl}s)")
        except Exception as e:
            logger.warning(f"Redis SET hatası ({key}): {e} — sadece in-memory yazıldı.")

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
    if _redis_available and _UPSTASH_URL and _SESSION:
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
import threading
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

import uuid
import json
import logging
from fastapi import BackgroundTasks
from backend.infrastructure import redis_cache

logger = logging.getLogger(__name__)

def spawn_background_job(background_tasks: BackgroundTasks, execute_func, *args, **kwargs) -> str:
    """
    Vercel Timeout sınırını (10s) delmek için ağır işlem taşıyıcı.
    Bir Job_ID üretir, durumu PENDING yapar ve asıl görevi arka plana atar.
    """
    job_id = str(uuid.uuid4())
    # Redis'te min 10 dakika yaşasın
    redis_cache.cache_set(f"job:{job_id}:status", {"status": "PENDING"}, ttl=600)
    
    # Asenkron Wrapper
    background_tasks.add_task(_job_runner, job_id, execute_func, *args, **kwargs)
    return job_id

async def _job_runner(job_id: str, execute_func, *args, **kwargs):
    """Arkaplanda çalışan, hataları yakalayıp Redis'e sonucu gömen koruyucu işçi."""
    try:
        redis_cache.cache_set(f"job:{job_id}:status", {"status": "RUNNING"}, ttl=600)
        
        # Orijinal fonksiyonu çalıştır
        import inspect
        if inspect.iscoroutinefunction(execute_func):
            result = await execute_func(*args, **kwargs)
        else:
            import asyncio
            result = await asyncio.to_thread(execute_func, *args, **kwargs)
            
        # Sonucu JSON formatında serialize et
        redis_cache.cache_set(f"job:{job_id}:result", {"data": result}, ttl=600)
        redis_cache.cache_set(f"job:{job_id}:status", {"status": "COMPLETED"}, ttl=600)
        logger.info(f"✅ Job {job_id} successfully completed in background.")
    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}")
        redis_cache.cache_set(f"job:{job_id}:status", {"status": "ERROR"}, ttl=600)
        redis_cache.cache_set(f"job:{job_id}:error", {"message": str(e)}, ttl=600)

def get_job_status(job_id: str) -> dict:
    """
    Frontend tarafından 3 saniyede bir (Polling) çağrılacak uç nokta okuyucusu.
    """
    raw_status = redis_cache.cache_get(f"job:{job_id}:status")
    status = "NOT_FOUND"
    if isinstance(raw_status, dict):
        status = raw_status.get("status", "NOT_FOUND")
    
    response = {"job_id": job_id, "status": status}
    
    if status == "COMPLETED":
        res_data = redis_cache.cache_get(f"job:{job_id}:result")
        if isinstance(res_data, dict):
             response["result"] = res_data.get("data")
    elif status == "ERROR":
        err_data = redis_cache.cache_get(f"job:{job_id}:error")
        if isinstance(err_data, dict):
            response["error"] = err_data.get("message", "Bilinmeyen hata")
        else:
            response["error"] = "Bilinmeyen hata"
        
    return response

"""
🌪️ Chaos & Resilience Engineering Test Suite
========================================
Bu dosya sistemin hata toleransını, backoff zincirlerini ve spam dayanımını test eder.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

# ── 1. Rate Limiter Spam Concurrency Test ───────────────────────────────────

@pytest.mark.asyncio
@patch("backend.core.redis_cache.cache_get")
@patch("backend.core.redis_cache.cache_set")
async def test_rate_limiter_concurrency_spam(mock_set, mock_get):
    """1.000 paralel istekte asenkron Lock stabilizasyonunu test eder."""
    from backend.api.rate_limiter import RateLimiter
    
    # 5 istek limitli rate limiter
    limiter = RateLimiter(requests_limit=5, period=60)
    mock_request = MagicMock()
    mock_request.headers.get.return_value = None
    mock_request.client.host = "127.0.0.1"
    
    # State mock listesi: Okunduğunda mevcut state'i, set edildiğinde mutate edilen state'i döner.
    mock_history = []
    mock_get.side_effect = lambda key: mock_history.copy()
    def side_effect_set(key, val, ttl=None):
        nonlocal mock_history
        mock_history = val
    mock_set.side_effect = side_effect_set

    # 10 adet eşzamanlı (concurrent) istek gönderimi
    tasks = [limiter.check(mock_request) for _ in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # İlk 5'i Lock sayesinde sırayla history'e eklenir (İzin verilir - r is None)
    # Sonraki 5'i Limit'i aştığı için HTTPException fırlatır.
    successes = [r for r in results if r is None]
    failures = [r for r in results if isinstance(r, HTTPException) and r.status_code == 429]
    
    assert len(successes) == 5
    assert len(failures) == 5


# ── 2. Scraper HTTP Retry/Exp-Backoff Chaos Test ─────────────────────────────

@pytest.mark.asyncio
@patch("backend.data.tefas_scraper.httpx.AsyncClient.post")
async def test_tefas_scraper_retry_chaos(mock_post):
    """Tefas scraper'ın üst üste çökmelerde Retry loop döngüsünü test eder."""
    from backend.data.tefas_scraper import _fetch_chunk
    
    # Başarısız mock yanıtlar
    mock_resp_fail = MagicMock()
    mock_resp_fail.status_code = 500
    mock_resp_fail.text = "Internal Server Error"
    
    # Sırasıyla Network hatası -> HTTP 500 -> En sonunda başarılı HTTP 200 dönsün.
    mock_post.side_effect = [
        Exception("Network Dropped"), 
        mock_resp_fail, 
        MagicMock(status_code=200, json=lambda: {"data": []})
    ]
    
    # Testleri bekletmemek için asyncio.sleep'i mockluyoruz.
    with patch("backend.data.tefas_scraper.asyncio.sleep", return_value=None):
        res = await _fetch_chunk("2024-01-01", "2024-01-01", chunk_idx=1)
        
    assert res == [] # Success patika dönüşü
    assert mock_post.call_count == 3 # 3 kez tetiklendiği doğrulaması


# ── 3. Negative API Verification (Edge Case Payloads) ───────────────────────

@pytest.mark.asyncio
async def test_api_analytics_bad_types():
    """Analiz endpoint'lerine bozuk şema/tip beslendiğinde Pydantic koruması."""
    from backend.api.main import app
    from httpx import AsyncClient, ASGITransport
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Tickers listesinde string yerine integer var (Dengesiz veri)
        payload = {
            "tickers": [123, None], 
            "use_ai": "Evvet" # Boolean yerine string
        }
        response = await ac.post("/api/analyze", json=payload)
        
        # FastAPI'nin 500 crash yerine 422 Unprocessable Entity vermesi beklenir.
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_api_analytics_empty_tickers():
    """Boş tickers listesi verildiğinde guard'ın patlamadan 400/422 döndürmesi."""
    from backend.api.main import app
    from httpx import AsyncClient, ASGITransport
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
         response = await ac.post("/api/analyze", json={"tickers": []})
         assert response.status_code in [400, 422]

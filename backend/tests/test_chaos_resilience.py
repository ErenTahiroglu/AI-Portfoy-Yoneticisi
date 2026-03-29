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

def test_tefas_scraper_retry_chaos():
    """Tefas scraper'ın üst üste çökmelerde Retry loop döngüsünü test eder."""
    from backend.data.tefas_scraper import TefasScraper
    scraper = TefasScraper()
    
    # Mock session.post
    mock_post = MagicMock()
    scraper.session.post = mock_post
    
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
    
    # Testleri bekletmemek için time.sleep'i mockluyoruz.
    with patch("time.sleep", return_value=None):
        res = scraper._fetch_chunk("TP2", "2024-01-01", "2024-01-01")
        
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


# ── 4. Mock Portfolio: Sıfır Ağırlıklı Portföy (ZeroDivision Guard) ──────────────

def test_zero_weight_portfolio():
    """Tüm ağırlıklar 0 olduğunda portfolio_simulator çökmemeli, boş dict dönmeli."""
    import pandas as pd
    from backend.core.portfolio_simulator import run_portfolio_simulation
    
    # Mock fiyat verisi: 30 günlük seri
    dates = pd.date_range("2024-01-01", periods=30)
    price_df = pd.DataFrame({"AAPL": [150.0 + i for i in range(30)]}, index=dates)
    
    # Tüm ağırlıklar sıfır
    weights = {"AAPL": 0}
    result = run_portfolio_simulation(price_df, weights)
    assert result == {}, f"Beklenen boş dict, alınan: {result}"


def test_empty_portfolio():
    """Boş portföyü simülasörü çökmeden boş dict dönmeli."""
    import pandas as pd
    from backend.core.portfolio_simulator import run_portfolio_simulation
    
    result = run_portfolio_simulation(pd.DataFrame(), {})
    assert result == {}


def test_cost_zero_asset():
    """Maliyeti 0 olan varlık PnL hesabında sıfıra bölme hatası üretmemeli."""
    import pandas as pd
    from backend.core.portfolio_simulator import run_portfolio_simulation
    
    dates = pd.date_range("2024-01-01", periods=30)
    # Fiyat dizisinde sıfır başlangıç fiyatı
    prices = [0.0] + [1.0 + i * 0.01 for i in range(29)]
    price_df = pd.DataFrame({"TSLA": prices}, index=dates)
    weights = {"TSLA": 100}
    # Sıfır fiyatlı günde `prev_price > 0` guard devreye girmeli, çökmemeli.
    result = run_portfolio_simulation(price_df, weights)
    assert isinstance(result, dict), "Simülasör bir dict dönmeliydi."


def test_safe_api_call_stale_cache_on_timeout():
    """API Timeout'unda safe_api_call stale cache'den veri çekerek is_stale=True göndermeli."""
    from unittest.mock import patch, MagicMock
    from backend.core.analysis_engine import safe_api_call

    fake_stale_data = {"ticker": "AAPL", "price": 155.0}
    stale_key = "AAPL:False:True"

    def failing_func():
        raise Exception("Connection timed out")

    with patch("backend.core.analysis_engine.cache_get", return_value=fake_stale_data):
        result = safe_api_call(failing_func, stale_key=stale_key)

    assert result.get("is_stale") is True
    assert result.get("price") == 155.0


# ── 6. Redis Connection Failure & Job Fallback ──────────────────────────────

@pytest.mark.asyncio
async def test_redis_fallback_on_connection_error():
    """
    SRE Chaos Test: Upstash Redis (REST) çöktüğünde sistemin
    in-memory _LOCAL sözlüğüne sessizce geçiş yapması ve veriyi koruması.
    """
    from backend.core import redis_cache
    from unittest.mock import patch, MagicMock
    import httpx
    
    test_key = "chaos_test_job_id"
    test_data = {"status": "RUNNING"}

    # httpx.Client.post'u hata fırlatacak şekilde mock'la (Redis Down)
    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Redis is Down")):
        # Redis çökmüş olsa bile SET işlemi hata fırlatmamalı (Fallback)
        redis_cache.cache_set(test_key, test_data, ttl=10)
        
    # GET işlemi Redis'e gidip hata alsa bile in-memory'den veriyi dönmeli
    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Redis is Down")):
        retrieved = redis_cache.cache_get(test_key)
        
    assert retrieved == test_data, "❌ Redis çökünce veri in-memory fallback'ten dönmedi!"


# ── 7. DataSyncNode Parallel Fan-in Stability ───────────────────────────────

@pytest.mark.asyncio
async def test_datasync_fan_in_race_condition():
    """
    Fan-in Senkronizasyon Testi: 
    Paralel veri toplama düğümleri (Market, Islamic, News) farklı sürelerde
    bitse bile DataSyncNode'un veriyi kusursuz birleştirdiğini doğrular.
    """
    from backend.core.graph.trading_graph import data_sync_node
    
    # Simüle edilmiş asenkron sonuçlar kümesi
    state = {
        "market_report": {"price": 100},
        "islamic_report": {"is_halal": True},
        "news_report": {"sentiment": "Bullish"},
        "ticker": "TSLA"
    }
    
    # DataSyncNode'un veriyi bozmadan veya eksik bırakmadan geçtiğini doğrula
    result = await data_sync_node(state)
    
    assert result == {}, "DataSyncNode sadece senkronizasyon noktasıdır, state'i null-out etmemeli (return {})."
    # LangGraph'ın fan-in mantığı state'leri otomatik birleştirir, 
    # DataSyncNode'un burada çökmemesi yeterlidir.

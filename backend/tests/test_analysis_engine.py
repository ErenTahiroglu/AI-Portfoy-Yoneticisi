"""Tests for analysis_engine.py — Analiz motoru modülü."""

import pytest
from core.analysis_engine import _friendly_error, _cache_key, _get_cached, _set_cache
from core.redis_cache import _LOCAL as _CACHE


class TestFriendlyError:
    """Kullanıcı dostu hata mesajları testleri."""

    def test_rate_limit(self):
        msg = _friendly_error("RESOURCE_EXHAUSTED: limit reached")
        assert "Gemini" in msg or "kota" in msg.lower()

    def test_ssl_error(self):
        msg = _friendly_error("SSLError: certificate verify failed")
        assert "SSL" in msg or "bağlantı" in msg.lower()

    def test_timeout(self):
        msg = _friendly_error("Timeout: request timed out")
        assert "yanıt" in msg.lower() or "Timeout" in msg

    def test_unknown_error(self):
        msg = _friendly_error("SomeRandomError: blah blah")
        assert "Analiz hatası" in msg


class TestCache:
    """TTL cache testleri."""

    def setup_method(self):
        _CACHE.clear()

    def test_cache_set_and_get(self):
        key = _cache_key("AAPL", True, True)
        data = {"ticker": "AAPL", "status": "Uygun"}
        _set_cache(key, data)
        result = _get_cached(key)
        assert result is not None
        assert result["ticker"] == "AAPL"

    def test_cache_miss(self):
        result = _get_cached("nonexistent:True:True")
        assert result is None

    def test_cache_key_format(self):
        key = _cache_key("THYAO", False, True)
        assert "THYAO" in key
        assert "False" in key


from unittest.mock import patch, MagicMock
from core.analysis_engine import AnalysisEngine
from api.rate_limiter import RateLimiter

class TestAnalysisEngineRun:
    """Motor çalıştırma ve strateji testleri."""

    @pytest.fixture
    def engine(self):
        return AnalysisEngine()

    @patch("data.market_detector.detect_market")
    def test_analyze_single_isolated(self, mock_detect, engine):
        """Analyze tekli çağrısının izolasyon testi."""
        mock_detect.return_value = ("TR", "THYAO.IS", False)
        
        # Mock Analyzer
        mock_analyzer = MagicMock()
        mock_analyzer.analiz_et.return_value = {"finansal": "Olumlu"}
        engine._analyzers["TR"] = mock_analyzer

        result_entry = engine._analyze_single("THYAO", check_islamic=True, check_financials=True, use_ai=False, api_key="fake", model="fake", lang="tr")

        assert result_entry["ticker"] == "THYAO"
        assert result_entry["market"] == "TR"


class TestRateLimiterAsync:
    """Rate Limiter asenkron testleri (Redis Mocklu)."""

    @pytest.mark.asyncio
    @patch("backend.core.redis_cache.cache_get")
    @patch("backend.core.redis_cache.cache_set")
    async def test_rate_limiter_allows(self, mock_set, mock_get):
        limiter = RateLimiter(requests_limit=1, period=60)
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "127.0.0.1"
        
        # Mock Redis empty history
        mock_get.return_value = []
        
        await limiter.check(mock_request)
        # Verify it writes state update
        assert mock_set.called

    @pytest.mark.asyncio
    @patch("backend.core.redis_cache.cache_get")
    @patch("backend.core.redis_cache.cache_set")
    async def test_rate_limiter_blocks(self, mock_set, mock_get):
        limiter = RateLimiter(requests_limit=1, period=60)
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "127.0.0.1"
        
        # Mock Redis gives FULL history
        import time
        mock_get.return_value = [time.time()]
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await limiter.check(mock_request)
            
        assert exc.value.status_code == 429

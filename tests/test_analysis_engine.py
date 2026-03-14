"""Tests for analysis_engine.py — Analiz motoru modülü."""

import pytest
from core.analysis_engine import _friendly_error, _cache_key, _get_cached, _set_cache, _CACHE


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

import pytest
import json
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from src.api.main import app

@pytest.mark.asyncio
async def test_api_search():
    """Autocomplete Endpoint testi."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/search?q=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "symbol" in data[0]

@pytest.mark.asyncio
async def test_api_analyze_sse():
    """SSE Stream Endpoint testi (Mocklanmış AI)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "tickers": ["AAPL"],
            "use_ai": False,
            "check_islamic": True,
            "check_financials": True,
            "api_key": "fake_api_key"
        }
        
        # We can stream response accurately
        async with ac.stream("POST", "/api/analyze", json=payload) as response:
            assert response.status_code == 200
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:])
                    assert "ticker" in data
                    break

@pytest.mark.asyncio
async def test_ai_agent_mock_sentiment():
    """Mock Gemini Sentiment test."""
    from src.core.ai_agent import analyze_news_sentiment
    
    with patch("src.core.ai_agent.ChatGoogleGenerativeAI") as MockLLM:
        mock_instance = MockLLM.return_value
        # Simulate structured JSON response
        mock_instance.invoke.return_value.content = '{"score": 80, "sentiment_label": "Açgözlülük", "islamic_risk_flag": false, "risk_reason": "Sorun yok"}'
        
        res = analyze_news_sentiment([{"title": "Good News"}], check_islamic=True, api_key="fake")
        assert res["score"] == 80
        assert res["sentiment_label"] == "Açgözlülük"
        assert res["islamic_risk_flag"] is False

@pytest.mark.asyncio
async def test_api_news_endpoint():
    """Haber filtreleme API Endpoint testi."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "tickers": ["AAPL"],
            "api_key": "fake_key",
            "model": "gemini-2.5-flash",
            "lang": "tr"
        }
        with patch("src.data.news_fetcher.filter_impactful_news") as mock_filter:
            mock_filter.return_value = [{"title": "News Title", "link": "#", "sentiment": "Neutral", "reason": "none"}]
            
            response = await ac.post("/api/news", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert "news" in data

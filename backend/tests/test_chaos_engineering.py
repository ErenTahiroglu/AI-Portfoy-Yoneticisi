import pytest
from unittest.mock import patch, MagicMock
from typing import cast
from backend.engine.graph import summarizer_node, SummarizedDebate
from backend.engine.agent_states import GraphState

# ── 1. LLM Hallucinated Input Injection ─────────────────────────────────────

@pytest.mark.asyncio
async def test_summarizer_resilience_garbage_json():
    """
    LLM'in Pydantic şemamı bozup saçma sapan metin döndürdüğü durum.
    Sistem 2 kez dener, başarısız olursa güvenli modda durur.
    """
    from pydantic import ValidationError
    
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    # Pydantic validation error simülasyonu
    try:
        SummarizedDebate.model_validate({"invalid_field": "garbage"})
    except ValidationError as e:
        mock_structured.ainvoke.side_effect = e
    
    mock_llm.with_structured_output.return_value = mock_structured
    
    state = {
        "messages": ["test"],
        "investment_debate_state": {"history": ["a", "b", "c", "d"]},
        "risk_debate_state": {"history": []}
    }

    with patch("backend.engine.graph.get_quick_think_llm", return_value=mock_llm):
        result = await summarizer_node(cast(GraphState, state))
        
    # Kritik: Sistem kilitlenmemeli, '[HOLD]' kararı ile durmalı.
    assert "[HOLD]" in result["final_trade_decision"]
    assert mock_structured.ainvoke.call_count == 2 # 2 retries inside

# ── 2. API Rate Limit / Connection Drop ──────────────────────────────────────

@pytest.mark.asyncio
@patch("backend.infrastructure.llm_factory.get_quick_think_llm")
async def test_api_rate_limit_timeout_handling(mock_get_llm):
    """
    GPT/Gemini API Limit (429) veya Timeout (504) yediğinde sistemin davranışı.
    """
    mock_llm = MagicMock()
    # API Down simülasyonu
    mock_llm.with_structured_output.side_effect = Exception("HTTP 429: Rate Limit Exceeded")
    mock_get_llm.return_value = mock_llm
    
    state = {
        "investment_debate_state": {"history": ["a", "b", "c", "d"]},
        "risk_debate_state": {"history": []}
    }
    
    # summarizer_node exception yakalayıp güvenli 'HOLD' dönmeli
    result = await summarizer_node(cast(GraphState, state))
    
    assert "HOLD" in result["final_trade_decision"]
    assert "Sistem güvenlik amacıyla işlemi askıya aldı" in result["final_trade_decision"]

# ── 3. Memory Leak / Deadlock Prevention ─────────────────────────────────────

@pytest.mark.asyncio
async def test_deadlock_on_infinite_loop_breaker():
    """
    Ajanlar arası diyalog sonsuz döngüye girerse (Loop), route logic 
    bunu kesmeli. Note: Bu test graph router'larını kontrol eder.
    """
    from backend.engine.graph import route_investment_debate, MAX_TURNS
    
    state = {"turn_count": MAX_TURNS + 1}
    route = route_investment_debate(cast(GraphState, state))
    
    # 3 turdan sonra zorla Research Manager'a gitmeli
    assert route == "Research Manager"

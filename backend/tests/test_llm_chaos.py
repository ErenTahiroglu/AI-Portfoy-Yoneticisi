import pytest
from unittest.mock import patch, MagicMock
from backend.engine.graph import summarizer_node, SummarizedDebate

# ── 1. Summarizer Node Garbage/Validation Failure Tests ─────────────────────

@pytest.mark.asyncio
async def test_summarizer_validation_failure_hold_mode():
    """
    Summarizer'ın üst üste 2 kez bozuk JSON dönmesi durumunda 
    sistemi güvenli 'HOLD' moduna aldığını doğrular.
    """
    from pydantic import ValidationError
    
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    
    # Pydantic validation error simülasyonu (Gerçek hata üreterek)
    try:
        # Invalid data to trigger ValidationError
        SummarizedDebate.model_validate({"korunan_metrikler": "not_a_list"})
    except ValidationError as e:
        mock_structured.ainvoke.side_effect = e
        
    mock_llm.with_structured_output.return_value = mock_structured

    state = {
        "messages": ["test msg"],
        "investment_debate_state": {"history": ["a", "b", "c", "d"]}, # Trigger condition len >= 4
        "risk_debate_state": {"history": []}
    }

    with patch("backend.engine.graph.get_quick_think_llm", return_value=mock_llm):
        result = await summarizer_node(state)
        
    assert "HOLD" in result["final_trade_decision"]
    assert "şema doğrulama (validation) kalıcı olarak çöktü" in result["messages"][0].lower()
    # 2 deneme yapmalı (max_retries=2)
    assert mock_structured.ainvoke.call_count == 2

@pytest.mark.asyncio
async def test_summarizer_empty_history_noop():
    """Tartışma geçmişi çok kısaysa Summarizer'ın hiçbir şey yapmadan {} dönmesini doğrular."""
    state = {
        "investment_debate_state": {"history": ["short"]},
        "risk_debate_state": {"history": []}
    }
    result = await summarizer_node(state)
    assert result == {}

# ── 2. LLM Timeout / Exception Resilience ───────────────────────────────────

@pytest.mark.asyncio
async def test_summarizer_unexpected_exception():
    """Beklenmedik bir Runtime hatasında Summarizer'ın HOLD moduna geçmesi."""
    mock_llm = MagicMock()
    mock_llm.with_structured_output.side_effect = Exception("OpenAI is Down")
    
    state = {
        "investment_debate_state": {"history": ["a", "b", "c", "d"]},
        "risk_debate_state": {"history": []}
    }

    with patch("backend.engine.graph.get_quick_think_llm", return_value=mock_llm):
        result = await summarizer_node(state)

    assert "[HOLD]" in result["final_trade_decision"]

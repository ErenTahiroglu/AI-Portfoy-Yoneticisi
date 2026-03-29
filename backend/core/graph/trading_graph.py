import logging
from langgraph.graph import START, END, StateGraph

from backend.core.graph.agent_states import GraphState
from backend.core.llm_factory import get_quick_think_llm

from backend.core.agents.data_nodes import (
    market_data_node,
    islamic_node,
    news_node
)
from backend.core.graph.circuit_breaker import evaluate_risk_circuit_breaker
from backend.core.agents.adversarial_agents import (
    bull_researcher_node,
    bear_researcher_node,
    research_manager_node,
    trader_node,
    aggressive_analyst_node,
    conservative_analyst_node,
    neutral_analyst_node,
    portfolio_manager_node
)

logger = logging.getLogger(__name__)

MAX_TURNS = 3
TOKEN_LIMIT = 4000

def route_investment_debate(state: GraphState) -> str:
    turn_count = state.get("turn_count", 0)
    
    if turn_count >= MAX_TURNS:
        logger.info(f"[LOOP BREAKER] Investment Debate max tur limitine ({MAX_TURNS}) ulaştı. Yargıca (Manager) aktarılıyor.")
        return "Research Manager"
        
    return "Bull Researcher"
    

def route_risk_debate(state: GraphState) -> str:
    turn_count = state.get("turn_count", 0)
    
    if turn_count >= MAX_TURNS:
        logger.info(f"[LOOP BREAKER] Risk Debate max tur limitine ({MAX_TURNS}) ulaştı. Nihai Kararcıya (CIO) aktarılıyor.")
        return "Portfolio Manager"
        
    return "Aggressive Analyst"


def route_circuit_breaker(state: GraphState) -> str:
    decision = evaluate_risk_circuit_breaker(state)
    logger.info(f"[ROUTER] Circuit Breaker decision: {decision}")
    if decision == "bypass_risk_debate":
        return "Portfolio Manager"
    return "Aggressive Analyst"


from pydantic import BaseModel, Field
from typing import List

class SummarizedDebate(BaseModel):
    korunan_metrikler: List[str] = Field(description="Her iki tartışma dalından (Bull/Bear veya Risk) gelen kesin rakamsal veriler (RSI, vaR, % büyüme vb.)")
    boga_argumanlari: List[str] = Field(description="İyimser/Agresif tarafın temel argüman maddeleri")
    ayi_argumanlari: List[str] = Field(description="Kötümser/Defansif tarafın temel argüman ve risk maddeleri")
    uzlasma_noktalari: str = Field(description="Tarafların ortak kabullendiği piyasa gerçekleri")

async def summarizer_node(state: GraphState) -> dict:
    messages = state.get("messages", [])
    inv_hist = state.get("investment_debate_state", {}).get("history", [])
    risk_hist = state.get("risk_debate_state", {}).get("history", [])
    
    if len(inv_hist) < 4 and len(risk_hist) < 4:
        return {}
        
    prompt = f"""
    Sen sistemin DİKKATLİ ÖZETLEYİCİSİSİN (Strict State Summarizer).
    Görevin: Aşağıda geçen uzun tartışmayı kompakt bir Pydantic JSON yapısına çevirmek.
    
    [YATIRIM TARTIŞMASI]:
    {chr(10).join(inv_hist[-6:]) if inv_hist else 'Yok'}
    
    [RİSK TARTIŞMASI]:
    {chr(10).join(risk_hist[-6:]) if risk_hist else 'Yok'}
    """
    
    llm = get_quick_think_llm(model_name="gemini-2.5-flash")
    structured_llm = llm.with_structured_output(SummarizedDebate)
    
    try:
        res = await structured_llm.ainvoke(prompt)
        summary_text = f"[SIKIŞTIRILMIŞ BAĞLAM]\nMetrikler: {res.korunan_metrikler}\nBoğa: {res.boga_argumanlari}\nAyı: {res.ayi_argumanlari}\nUzlaşma: {res.uzlasma_noktalari}"
        logger.info("[PRUNING] State context strictly compressed via Pydantic Schema.")
        
        return {
            "messages": [summary_text]
        }
    except Exception as e:
        logger.error(f"Summarizer failed: {e}")
        return {}


def compile_trading_graph():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("MarketNode", market_data_node)
    workflow.add_node("IslamicNode", islamic_node)
    workflow.add_node("NewsNode", news_node)
    
    async def join_and_circuit_node(state: GraphState) -> dict:
        t = state.get("turn_count", 0)
        return {"turn_count": t + 1}
        
    workflow.add_node("DataJoinAndCircuit", join_and_circuit_node)
    
    workflow.add_node("Bull Researcher", bull_researcher_node)
    workflow.add_node("Bear Researcher", bear_researcher_node)
    workflow.add_node("Research Manager", research_manager_node)
    workflow.add_node("Trader", trader_node)
    
    workflow.add_node("Aggressive Analyst", aggressive_analyst_node)
    workflow.add_node("Conservative Analyst", conservative_analyst_node)
    workflow.add_node("Neutral Analyst", neutral_analyst_node)
    workflow.add_node("Portfolio Manager", portfolio_manager_node)
    workflow.add_node("SummarizerPruner", summarizer_node)

    workflow.add_edge(START, "MarketNode")
    workflow.add_edge(START, "IslamicNode")
    workflow.add_edge(START, "NewsNode")
    
    workflow.add_edge("MarketNode", "DataJoinAndCircuit")
    workflow.add_edge("IslamicNode", "DataJoinAndCircuit")
    workflow.add_edge("NewsNode", "DataJoinAndCircuit")
    
    workflow.add_edge("DataJoinAndCircuit", "Bull Researcher")
    workflow.add_edge("Bull Researcher", "Bear Researcher")

    workflow.add_conditional_edges(
        "Bear Researcher",
        route_investment_debate,
        {
            "Bull Researcher": "Bull Researcher",
            "Research Manager": "Research Manager"
        }
    )
    
    workflow.add_edge("Research Manager", "Trader")
    
    workflow.add_conditional_edges(
        "Trader",
        route_circuit_breaker,
        {
            "Aggressive Analyst": "Aggressive Analyst",
            "Portfolio Manager": "Portfolio Manager" 
        }
    )
    
    workflow.add_edge("Aggressive Analyst", "Conservative Analyst")
    workflow.add_edge("Conservative Analyst", "Neutral Analyst")
    
    workflow.add_conditional_edges(
        "Neutral Analyst",
        route_risk_debate,
        {
            "Aggressive Analyst": "Aggressive Analyst",
            "Portfolio Manager": "Portfolio Manager"
        }
    )
    
    workflow.add_edge("Portfolio Manager", "SummarizerPruner")
    workflow.add_edge("SummarizerPruner", END)
    
    return workflow.compile()

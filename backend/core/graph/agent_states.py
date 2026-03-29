import operator
from typing import Annotated, TypedDict, List, Dict

def merge_dicts(left: dict, right: dict) -> dict:
    if not left: return right.copy()
    if not right: return left.copy()
    left.update(right)
    return left

class GraphState(TypedDict):
    ticker: str
    market: str
    company_of_interest: str
    turn_count: int
    
    messages: Annotated[List[str], operator.add]
    
    market_report: Annotated[Dict, merge_dicts]
    fundamentals_report: Annotated[Dict, merge_dicts]
    news_report: Annotated[Dict, merge_dicts]
    islamic_report: Annotated[Dict, merge_dicts]
    
    investment_debate_state: Annotated[Dict, merge_dicts]
    trader_investment_plan: str
    
    skip_risk_debate: bool
    circuit_breaker_reason: str
    
    risk_debate_state: Annotated[Dict, merge_dicts]
    final_trade_decision: str

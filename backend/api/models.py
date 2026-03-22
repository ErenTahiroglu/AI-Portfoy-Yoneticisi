from pydantic import BaseModel
from typing import List, Optional, Dict

class AnalysisRequest(BaseModel):
    tickers: List[str]
    use_ai: bool = False
    api_key: Optional[str] = None
    av_api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    check_islamic: bool = False
    check_financials: bool = True
    lang: str = "tr"
    initial_balance: float = 10000.0
    monthly_contribution: float = 0.0
    rebalancing_freq: str = "none"

class UserSettingsRequest(BaseModel):
    telegram_chat_id: Optional[str] = None
    risk_tolerance: Optional[str] = "Orta"

class PortfolioOptimizeRequest(BaseModel):
    tickers: List[str]
    weights: Optional[Dict[str, float]] = None
    risk_free_rate: float = 0.02

class PortfolioRiskRequest(BaseModel):
    tickers: List[str]
    weights: Dict[str, float]

# Chat ve News Modelleri
class NewsRequest(BaseModel):
    tickers: List[str]
    lang: str = "tr"
    api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    portfolio_context: Optional[dict] = None
    api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    lang: str = "tr"

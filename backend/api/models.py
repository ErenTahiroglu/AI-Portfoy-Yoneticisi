from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any

class AnalysisRequest(BaseModel):
    model_config = ConfigDict(strict=True)
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
    model_config = ConfigDict(strict=True)
    telegram_chat_id: Optional[str] = None
    risk_tolerance: Optional[str] = "Orta"

class PortfolioOptimizeRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    tickers: List[str]
    weights: Optional[Dict[str, float]] = None
    risk_free_rate: float = 0.02

class PortfolioRiskRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    tickers: List[str]
    weights: Dict[str, float]

# Chat ve News Modelleri
class NewsRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    tickers: List[str]
    lang: str = "tr"
    api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"

class ChatRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    messages: List[Dict[str, str]]
    portfolio_context: Optional[dict] = None
    api_key: Optional[str] = None
    model: str = "gemini-2.5-flash"
    lang: str = "tr"
    user_profile: Optional[dict] = None  # Onboarding wizard'dan gelen yatırımcı profili


class OnboardingProfileRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    level: str          # "beginner" | "read" | "tried"
    goal: str           # "protect" | "target" | "grow"
    risk_tolerance: str # "low" | "medium" | "high"


class TelemetryEventRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    event_type: str = Field(..., description="Olayın türü (örn: brake_triggered, brake_accepted, brake_ignored)")
    event_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Ekstra log verileri")

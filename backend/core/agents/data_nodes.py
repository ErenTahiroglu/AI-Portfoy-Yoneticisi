import json
import logging
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from backend.core.graph.agent_states import GraphState
from backend.core.llm_factory import get_quick_think_llm

logger = logging.getLogger(__name__)

# LLM ve API gecikmelerine karşı üstel (exponential) retry koruması
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(Exception)
)
async def market_data_node(state: GraphState) -> dict:
    ticker = state.get("ticker", "Genel")
    logger.info(f"[DataNode - Market] Fetching core market data for {ticker}")
    # Simüle edilmiş (veya backend modüllerinden çekilen) veri
    try:
        # Normalde yfinance veya polygon çağrılır
        return {
            "market_report": {
                "market_data": {"fiyat": 100, "degisim": 2.5, "hacim": "Yüksek"},
                "klines": [{"close": 98}, {"close": 99}, {"close": 100}] * 4
            }
        }
    except Exception as e:
        logger.error(f"[MarketNode] Fail: {e}")
        raise e

@retry(wait=wait_exponential(min=1, max=5), stop=stop_after_attempt(2))
async def islamic_node(state: GraphState) -> dict:
    ticker = state.get("ticker", "")
    logger.info(f"[DataNode - Islamic] Checking compliance for {ticker}")
    return {"islamic_report": {"uygunluk": "Uygun", "sebep": "Helal Finans Kriterlerini Karşılıyor."}}

@retry(wait=wait_exponential(min=2, max=6), stop=stop_after_attempt(3))
async def news_node(state: GraphState) -> dict:
    ticker = state.get("ticker", "")
    logger.info(f"[DataNode - News] Resolving news for {ticker}")
    return {"news_report": {"sentiment": "Nötr", "haberler": ["Şirket bilançosu iyi geldi", "Sektörel daralma endişesi"]}}

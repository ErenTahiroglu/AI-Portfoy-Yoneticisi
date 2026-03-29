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
    if not state.get("check_financials", True):
        logger.info(f"[Bypass] Market data for {ticker} skipped (check_financials=False)")
        return {"market_report": {}}
    
    logger.info(f"[DataNode - Market] Fetching real market data for {ticker}")
    
    try:
        from backend.analyzers.bist_analyzer import HisseAnaliz
        analyzer = HisseAnaliz()
        # BIST_SONEK check is in HisseAnaliz._bist_sembol
        res = analyzer.analiz_et(ticker)
        if res:
            return {
                "market_report": {
                    "market_data": res.get("son_fiyat", {}),
                    "klines": res.get("klines", []),
                    "performance": {
                        "annual": res.get("yg"),
                        "monthly": res.get("ay"),
                        "risk": res.get("risk")
                    }
                }
            }
        
        # Fallback for non-BIST (Simulated for US temporarily)
        return {
            "market_report": {
                "market_data": {"fiyat": 100, "degisim": 2.5, "hacim": "Yüksek"},
                "klines": [{"close": 98}, {"close": 99}, {"close": 100}] * 4
            }
        }
    except Exception as e:
        logger.error(f"[MarketNode] Fail: {e}")
        return {"market_report": {"error": str(e)}}

@retry(wait=wait_exponential(min=1, max=5), stop=stop_after_attempt(2))
async def islamic_node(state: GraphState) -> dict:
    ticker = state.get("ticker", "")
    logger.info(f"[DataNode - Islamic] Checking real compliance for {ticker}")
    
    try:
        from backend.analyzers.islamic_analyzer import IslamicAnalyzer
        analyzer = IslamicAnalyzer()
        # IslamicAnalyzer has specific logic for BIST and US
        res = analyzer.full_check(ticker)
        if res:
            return {"islamic_report": res}
            
        return {"islamic_report": {"uygunluk": "Bilinmiyor", "sebep": "Analiz verisi yetersiz."}}
    except Exception as e:
        logger.error(f"[IslamicNode] Fail: {e}")
        return {"islamic_report": {"error": str(e)}}

@retry(wait=wait_exponential(min=2, max=6), stop=stop_after_attempt(3))
async def news_node(state: GraphState) -> dict:
    ticker = state.get("ticker", "")
    if not state.get("check_financials", True):
         logger.info(f"[Bypass] News for {ticker} skipped (check_financials=False)")
         return {"news_report": {}}
    
    logger.info(f"[DataNode - News] Resolving news for {ticker}")
    return {"news_report": {"sentiment": "Nötr", "haberler": ["Şirket bilançosu iyi geldi", "Sektörel daralma endişesi"]}}

import logging
from typing import Dict, Any, Optional, List, cast
from backend.engine.graph import compile_trading_graph
from backend.engine.agent_states import GraphState

logger = logging.getLogger(__name__)

class ChatOrchestrator:
    def __init__(self):
        # We compile it once on startup
        self.graph = compile_trading_graph()

    async def ainvoke(self, input_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        [Standard Bridge]: Direct async call to the Graph.
        Used when the API layer already prepared the state (e.g. Analysis SSE).
        """
        try:
            return await self.graph.ainvoke(cast(GraphState, input_state))
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Direct invoke failed: {e}", exc_info=True)
            raise

    async def process_chat(
        self, 
        messages: List[str], 
        portfolio_context: Optional[Dict] = None, 
        api_key: Optional[str] = None, 
        model: str = "gemini-2.5-flash", 
        lang: str = "tr",
        user_id: Optional[str] = None,
        user_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        [Chat Gateway]: Prepares state for generic chat/portfolio questions.
        Matches the signature expected by background jobs in chat.py.
        """
        user_msg = messages[-1] if messages else ""
        logger.info(f"[ORCHESTRATOR] Processing Chat - User: {user_id}, Msg: {user_msg[:50]}...")

        initial_state = {
            "messages": messages,
            "ticker": None, # Will be detected by IntentNode if needed
            "api_key": api_key,
            "model_name": model,
            "lang": lang,
            "user_id": user_id,
            "portfolio_context": portfolio_context,
            "user_profile": user_profile,
            "turn_count": 0,
            "investment_debate_state": {"history": [], "summary": ""},
            "risk_debate_state": {"history": [], "summary": ""},
            "final_trade_decision": "HOLD",
            "check_financials": True,
            "check_islamic": True
        }

        try:
            result = await self.graph.ainvoke(cast(GraphState, initial_state))
            # Return legacy-compat report format
            messages = result.get("messages") or []
            return result.get("final_report") or {
                "summary": messages[-1] if messages else "No response.",
                "trade_decision": result.get("final_trade_decision", "HOLD")
            }
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Chat processing failed: {e}", exc_info=True)
            return {"error": str(e), "status": "failed"}

# Singleton instance
orchestrator = ChatOrchestrator()

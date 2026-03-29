import re
import logging
from typing import Optional, Dict, Any
from fastapi import BackgroundTasks
from backend.core.job_queue import spawn_background_job
from backend.core.graph.trading_graph import compile_trading_graph

logger = logging.getLogger(__name__)

class ChatOrchestrator:
    """
    🧩 Puzzle Mimari: Chat Facade (Ince Cephe)
    ==========================================
    Bu sınıf sadece API Router ile LangGraph arasındaki köprüdür.
    Sorumlulukları:
      1. Girdi validasyonu başlatmak (Basit kontroller).
      2. LangGraph ainvoke() çağrısını koordine etmek.
      3. Sonuçları (Paper trade vb.) post-process etmek (şimdi Graph State içinde).
    
    UYARI: İş mantığı (Regex, Karar Verme) burada değil, GRAPH içinde kalmalıdır.
    """
    
    def __init__(self):
        # Grafı bir kez compile et (veya her seferinde builder ile dinamik ör)
        self.graph = compile_trading_graph()

    async def process_chat(self, 
                           messages: list, 
                           portfolio_context: Optional[dict], 
                           api_key: str, 
                           model: str, 
                           lang: str, 
                           user_id: Optional[str] = None, 
                           user_profile: Optional[dict] = None) -> str:
        
        # 1. State Hazırla
        input_state = {
            "messages": [m["content"] for m in messages if m.get("content")],
            "ticker": "PORTFOLIO_GENERAL",
            "api_key": api_key, # llm_factory'ye paslanacak
            "model_name": model,
            "lang": lang,
            "user_id": user_id,
            "user_profile": user_profile,
            "portfolio_context": portfolio_context
        }
        
        # 2. Graph Invoke (Ajanlar işini yapsın)
        try:
            # Not: Graph'un düğümleri içinde Regex niyet okuma (Intent Detection) yapılacak.
            result = await self.graph.ainvoke(input_state)
            
            # 3. Sonuç Döndür
            # Graph final_trade_decision veya messages günceller.
            final_reply = result.get("final_trade_decision") or (result.get("messages")[-1] if result.get("messages") else "Üzgünüm, bir hata oluştu.")
            return final_reply
            
        except Exception as e:
            logger.error(f"ChatOrchestrator Graph Invoke Error: {e}")
            raise e

# Singleton instance
orchestrator = ChatOrchestrator()

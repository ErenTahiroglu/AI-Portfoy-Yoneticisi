import logging
import time
import asyncio
import os
import httpx
from backend.core.graph.trading_graph import compile_trading_graph
from backend.api.metrics import SHADOW_DIVERGENCE_TOTAL, GLOBAL_TIMEOUT_SHIELD_TOTAL

logger = logging.getLogger(__name__)

async def run_shadow_graph(old_decision: str, portfolio_context: dict, ticker_hint: str = "BIST_HINT"):
    """
    Gölge Dağıtım (Shadow Mode) Taskı - DIVERGENCE METRICS & PnL
    Eski motor vs Yeni motor karar sapmasını loglar ve Supabase'e T0 kaydını atar.
    """
    start_time = time.time()
    
    try:
        # Ajanların timeout/çöküşüne karşı global kalkan (Global Fallback)
        async def _run_graph():
            app = compile_trading_graph()
            initial_state = {
                "ticker": ticker_hint,
                "market": "US",  
                "company_of_interest": ticker_hint,
                "turn_count": 0,
                "messages": []
            }
            config = {"configurable": {"thread_id": "shadow_thread"}}
            return await app.ainvoke(initial_state, config)
            
        final_state = await asyncio.wait_for(_run_graph(), timeout=30.0)
        
        new_decision_full = final_state.get("final_trade_decision", "[HOLD] Karar Üretilemedi")
        
        # Etiket (Label) Kategorizasyonu (BUY, SELL, HOLD)
        old_cat = "BUY" if "al" in old_decision.lower() else "SELL" if "sat" in old_decision.lower() else "HOLD"
        new_cat = "BUY" if "al" in new_decision_full.lower() and "bekle" not in new_decision_full.lower() else "SELL" if "sat" in new_decision_full.lower() else "HOLD"
        
        elapsed = time.time() - start_time
        
        # Sadece karar ayrışması varsa logla ve Veritabanına T0 fırlat
        if old_cat != new_cat:
            logger.warning(f"🚨 DIVERGENCE DETECTED: Old ({old_cat}) vs New ({new_cat})")
            
            # Prometheus Metrics Update
            SHADOW_DIVERGENCE_TOTAL.labels(old_decision=old_cat, new_decision=new_cat, ticker=ticker_hint).inc()
            
            # Supabase Insert for Shadow PnL Tracking
            await _log_divergence_to_supabase(ticker_hint, old_cat, new_cat, old_decision, new_decision_full)
        else:
            logger.info(f"✅ CONCURRENCE: Her iki motor da {new_cat} kararı verdi.")

    except asyncio.TimeoutError:
        logger.error("🛡️ [GLOBAL KALKAN] Gölge Graf 30 saniyede yanıt vermedi. Sıkı Hold Mode devreye girdi.")
        GLOBAL_TIMEOUT_SHIELD_TOTAL.inc()
    except Exception as e:
        logger.error(f"🛡️ [ERROR ISOLATION] Gölge Graf çalışma sırasında çöktü: {e}")

async def _log_divergence_to_supabase(ticker: str, old_cat: str, new_cat: str, old_desc: str, new_desc: str):
    """
    Supabase'ye REST API üzerinden ayrışma kaydını atar (T0 anında).
    T1, T3, T7 güncellemeleri pg_cron & shadow_pnl_tracker.py tarafından yapılacaktır.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
         return
         
    try:
         headers = {
             "apikey": key,
             "Authorization": f"Bearer {key}",
             "Content-Type": "application/json",
             "Prefer": "return=minimal"
         }
         # Mock price fetch for T0 (Real setup would ask yfinance via DataNode)
         # Using a placeholder T0 = 100.0 for logic completeness
         payload = {
             "ticker": ticker,
             "old_decision": old_cat,
             "new_decision": new_cat,
             "old_rationale": old_desc[:250],
             "new_rationale": new_desc[:250],
             "t0_price": 100.0
         }
         async with httpx.AsyncClient(timeout=5.0) as client:
              resp = await client.post(f"{url}/rest/v1/shadow_divergence_logs", headers=headers, json=payload)
              if resp.status_code not in (201, 204):
                   logger.warning(f"Failed to log divergence to DB: {resp.status_code}")
    except Exception as e:
         logger.warning(f"Divergence insert async error: {e}")

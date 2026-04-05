import logging
from backend.engine.agent_states import GraphState

logger = logging.getLogger(__name__)

def evaluate_risk_circuit_breaker(state: GraphState) -> str:
    """
    LLM maliyeti/gecikmesi YARATMAYAN, salt deterministik Risk Filtresi.
    Data Node'lardan gelen piyasa/temel verileri analiz eder.
    Eğer piyasa sakin ve işlem rutinse -> "Portfolio Manager" a atlar (bypass_risk_debate).
    Eğer volatilite yüksekse, hacim patlamışsa veya RSI aşırı oynaksa -> "Risk Debate" 3'lü döngüsünü tetikler.
    """
    try:
        should_bypass = True
        reason = "Piyasa koşulları normal seyrediyor, risk tartışması pass geçildi."
        
        market_opt = state.get("market_report", {})
        if not market_opt or "error" in market_opt:
            return "trigger_risk_debate"
            
        market_data = market_opt.get("market_data", {})
        klines = market_opt.get("klines", [])
        
        change_pct = market_data.get("degisim", 0.0)
        if abs(change_pct) > 10.0:
            should_bypass = False
            reason = f"Aşırı günlük fiyat oynaması tespit edildi (%{change_pct}). Risk Tartışması tetikleniyor."
            
        if should_bypass and len(klines) > 10:
            last_close = float(klines[-1].get("close", 0))
            avg_close = sum(float(k.get("close", 0)) for k in klines[-10:]) / 10
            if avg_close > 0:
                deviation = abs((last_close - avg_close) / avg_close * 100)
                if deviation > 15.0:
                    should_bypass = False
                    reason = f"10 günlük hareketli ortalamadan sert sapma (%{deviation:.1f}). Risk Tartışması tetikleniyor."
                    
        fund_opt = state.get("fundamentals_report", {})
        fin_data = fund_opt.get("financials", {})
        beta = float(fin_data.get("beta", 1.0) or 1.0)
        if should_bypass and beta > 2.0:
            should_bypass = False
            reason = "Piyasa korelasyonu (Beta > 2.0) son derece yüksek olan volatil bir varlık. Risk Tartışması tetikleniyor."
            
        state["skip_risk_debate"] = should_bypass
        state["circuit_breaker_reason"] = reason
        
        logger.info(f"[CIRCUIT BREAKER] {state.get('ticker')}: {reason}")
        
        if should_bypass:
            return "bypass_risk_debate"
        return "trigger_risk_debate"
        
    except Exception as e:
        logger.error(f"Circuit Breaker error: {e}")
        return "trigger_risk_debate"

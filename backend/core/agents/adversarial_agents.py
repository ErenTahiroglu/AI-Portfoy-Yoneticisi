import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage

from backend.core.graph.agent_states import GraphState
from backend.core.llm_factory import get_quick_think_llm, get_deep_think_llm

logger = logging.getLogger(__name__)

def _stringify_state_reports(state: GraphState) -> str:
    market = state.get("market_report", {})
    fund = state.get("fundamentals_report", {})
    islam = state.get("islamic_report", {})
    news = state.get("news_report", {})
    if "klines" in market:
        del market["klines"]
    
    comp = {
        "Market": market,
        "Fundamentals": fund,
        "Islamic": islam,
        "News": news,
    }
    return json.dumps(comp, indent=2, ensure_ascii=False)

async def bull_researcher_node(state: GraphState) -> dict:
    ticker = state.get("company_of_interest", state.get("ticker"))
    reports_str = _stringify_state_reports(state)
    history = state.get("investment_debate_state", {}).get("history", [])
    
    mode = "ISLAMIC-ONLY" if not state.get("check_financials", True) else "FULL-ANALYSIS"
    
    prompt = f"""
    Sen 'Bull (İyimser) Araştırmacı' ajansın. 
    [MOD]: {mode}
    
    Görevin: {ticker} sembolü için piyasada sadece GÜÇLÜ FIRSATLARI ve BÜYÜME POTANSİYELİNİ savunmak.
    {'NOT: Finansal veriler (RSI, Fiyat vb.) bu modda devre dışıdır. Sadece İslami uygunluk ve haber duyarlılığına odaklan.' if mode == "ISLAMIC-ONLY" else ''}
    
    [VERİ TABANIN]:
    {reports_str}
    """
    
    messages = [SystemMessage(content=prompt)]
    for past_turn in history:
        messages.append(HumanMessage(content=past_turn))
        
    llm = get_quick_think_llm(model_name="gemini-2.5-flash")
    response = await llm.ainvoke(messages)
    content = str(response.content)
    
    return {
        "investment_debate_state": {
            "bull_history": [content],
            "history": [f"[BULL]: {content}"],
            "current_response": content
        }
    }

async def bear_researcher_node(state: GraphState) -> dict:
    ticker = state.get("company_of_interest", state.get("ticker"))
    reports_str = _stringify_state_reports(state)
    history = state.get("investment_debate_state", {}).get("history", [])
    
    mode = "ISLAMIC-ONLY" if not state.get("check_financials", True) else "FULL-ANALYSIS"
    
    prompt = f"""
    Sen 'Bear (Kötümser) Araştırmacı' ajansın. 
    [MOD]: {mode}
    
    Görevin: {ticker} sembolündeki GİZLİ TEHLİKELERİ ve EN KÖTÜ SENARYOLARI ortaya çıkarmak.
    {'NOT: Finansal metrikler kapalıdır. İslami risklere ve olumsuz haber başlıklarına odaklan.' if mode == "ISLAMIC-ONLY" else ''}
    
    [VERİ TABANIN]:
    {reports_str}
    """
    
    messages = [SystemMessage(content=prompt)]
    for past_turn in history:
        messages.append(HumanMessage(content=past_turn))
        
    llm = get_quick_think_llm(model_name="gemini-2.5-flash")
    response = await llm.ainvoke(messages)
    content = str(response.content)
    
    return {
        "investment_debate_state": {
            "bear_history": [content],
            "history": [f"[BEAR]: {content}"],
            "current_response": content
        }
    }

async def research_manager_node(state: GraphState) -> dict:
    ticker = state.get("company_of_interest", state.get("ticker"))
    debate_history = state.get("investment_debate_state", {}).get("history", [])
    
    prompt = f"""
    Sen 'Araştırma Yöneticisi' (Judge) ajansın. {ticker} üzerine Bull ve Bear ajanlarının münazarasını okudun.
    Görevin: Bu tartışmanın kazananını ilan etmek ve uygulanacak 'Teklif (Proposal)' sunmaktır.
    Formatın net, analitik ve tarafsız olsun.
    
    [KUTUPLAŞMIŞ TARTIŞMA GEÇMİŞİ]:
    {chr(10).join(debate_history)}
    """
    
    llm = get_deep_think_llm(model_name="gemini-2.5-pro")
    response = await llm.ainvoke([SystemMessage(content=prompt)])
    content = str(response.content)
    
    return {
        "investment_debate_state": {
            "judge_decision": content
        }
    }

async def trader_node(state: GraphState) -> dict:
    judge_decision = state.get("investment_debate_state", {}).get("judge_decision", "Karar Yok")
    
    prompt = f"""
    Sen 'Uygulayıcı Trader' ajansın. Yöneticinin kararına (Judge_Decision) uygun olarak, 
    risk oranını, alınacak veya satılacak partileri netleştiren spesifik bir İşlem Planı (Execution Plan) taslağı hazırla.
    Judge Kararı: {judge_decision}
    """
    
    llm = get_quick_think_llm(model_name="gemini-2.5-flash")
    response = await llm.ainvoke([SystemMessage(content=prompt)])
    
    return {
        "trader_investment_plan": str(response.content)
    }

async def aggressive_analyst_node(state: GraphState) -> dict:
    plan = state.get("trader_investment_plan", "")
    prompt = f"Sen Agresif (High-Risk) Analistsin. Trader'ın planını maks kâr odaklı nasıl patlatırız onu savun.\n[PLAN]: {plan}"
    res = await get_quick_think_llm().ainvoke([SystemMessage(content=prompt)])
    return {"risk_debate_state": {"aggressive_history": [str(res.content)], "history": [f"[AGRESSIVE]: {res.content}"]}}

async def conservative_analyst_node(state: GraphState) -> dict:
    plan = state.get("trader_investment_plan", "")
    hist = state.get("risk_debate_state", {}).get("history", [])
    prompt = f"Sen Muhafazakar (Zero-Risk) Analistsin. Agresifin teklifini reddet, en güvenli defansif planı savun.\n[PLAN/HISTORY]: {plan}\n{hist}"
    res = await get_quick_think_llm().ainvoke([SystemMessage(content=prompt)])
    return {"risk_debate_state": {"conservative_history": [str(res.content)], "history": [f"[CONSERVATIVE]: {res.content}"]}}

async def neutral_analyst_node(state: GraphState) -> dict:
    plan = state.get("trader_investment_plan", "")
    hist = state.get("risk_debate_state", {}).get("history", [])
    prompt = f"Sen Nötr (Dengeleyici) Analistsin. Hem agresif kârı hem defansif riski harmanla.\n[HISTORY]: {hist}"
    res = await get_quick_think_llm().ainvoke([SystemMessage(content=prompt)])
    return {"risk_debate_state": {"neutral_history": [str(res.content)], "history": [f"[NEUTRAL]: {res.content}"]}}

async def portfolio_manager_node(state: GraphState) -> dict:
    judge = state.get("investment_debate_state", {}).get("judge_decision", "")
    plan = state.get("trader_investment_plan", "")
    
    skip_risk = state.get("skip_risk_debate", False)
    cb_reason = state.get("circuit_breaker_reason", "")
    
    risk_debate = state.get("risk_debate_state", {}).get("history", [])
    
    context = f"""
    Yatırım Yargıcı: {judge}
    Trader Planı: {plan}
    
    {'RİSK TARTIŞMASI DEVRE KESİCİ (CIRCUIT BREAKER) TARAFINDAN ESNESİL (BYPASS) EDİLDİ NEDENİ: ' + cb_reason if skip_risk else 'AĞIR RİSK TARTIŞMASI SONUÇLARI: ' + chr(10).join(risk_debate)}
    """
    
    mode = "ISLAMIC-ONLY" if not state.get("check_financials", True) else "FULL-ANALYSIS"
    
    prompt = f"""
    Sen BAŞ YATIRIM YÖNETİCİSİSİN (Portfolio Manager - CIO).
    [MOD]: {mode}
    
    Alt ajanlarının ürettiği yatırım kararını inceleyerek NİHAİ BAĞLAYICI EMRİ ver.
    {'NOT: Bu analiz İslami odaklıdır. Teknik göstergelerin yokluğunu bir eksiklik olarak görme, fıkhi uyuma ve duyarlılığa odaklan.' if mode == "ISLAMIC-ONLY" else ''}
    
    [TÜM BAĞLAM VE GEÇMİŞ]:
    {context}
    """
    
    res = await get_deep_think_llm("gemini-2.5-pro").ainvoke([SystemMessage(content=prompt)])
    content = str(res.content)
    
    return {
        "final_trade_decision": content,
        "messages": [f"[PORTFOLIO MANAGER]: {content}"]
    }

import os
import sys
import httpx
import asyncio
import logging
from datetime import datetime, timezone, timedelta
import yfinance as yf

# Standalone execution configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ShadowPnLTracker")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

async def update_missing_pnl():
    """
    Idempotent PnL Updater. Supabase veritabanındaki Divergence Loglarını çeker.
    Eğer T+1, T+3 veya T+7 güncel fiyatları eskiyse (ve hesaplanmamışsa) yfinance üzerinden
    hisse durumunu günceller ve Old/New motorun kimin haklı çıktığını hesaplar.
    Bu script dışarıdan pg_cron üzerinden her gece tetiklenmek üzere tasarlanmıştır.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Eksik Supabase servis rolü veya URL anahtarı!")
        sys.exit(1)
        
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. Bekleyen (Null olan) PnL kayıtlarını al (T1, T3, T7)
    async with httpx.AsyncClient() as client:
        # Son 10 gündeki kayıtları çek, çok eskileri bırak
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/shadow_divergence_logs?select=*&order=created_at.desc&limit=50",
            headers=headers
        )
        if resp.status_code != 200:
            logger.error(f"Kayıtlar çekilemedi: {resp.status_code}")
            return
            
        logs = resp.json()
        now = datetime.now(timezone.utc)
        
        for idx, log in enumerate(logs):
            created_at = datetime.fromisoformat(log["created_at"].replace("Z", "+00:00"))
            days_passed = (now - created_at).days
            
            ticker = log["ticker"]
            t0 = log.get("t0_price", 1.0)
            
            updates = {}
            # T+1 Check
            if days_passed >= 1 and log.get("t1_price") is None:
                updates["t1_price"], updates["winner_t1"] = await _evaluate_pnl(ticker, t0, log["old_decision"], log["new_decision"])
            
            # T+3 Check
            if days_passed >= 3 and log.get("t3_price") is None:
                updates["t3_price"], updates["winner_t3"] = await _evaluate_pnl(ticker, t0, log["old_decision"], log["new_decision"])
                
            # T+7 Check
            if days_passed >= 7 and log.get("t7_price") is None:
                updates["t7_price"], updates["winner_t7"] = await _evaluate_pnl(ticker, t0, log["old_decision"], log["new_decision"])
                
            # DB Write if needed
            if updates:
                await client.patch(
                    f"{SUPABASE_URL}/rest/v1/shadow_divergence_logs?id=eq.{log['id']}",
                    headers=headers,
                    json=updates
                )
                logger.info(f"[{ticker}] PnL güncellendi: {updates}")
                
        logger.info(f"🎉 Tüm T+1/T+3/T+7 PnL kontrol zinciri tamamlandı. ({len(logs)} kayıt tarandı)")

async def _evaluate_pnl(ticker: str, t0: float, old_dec: str, new_dec: str):
    """
    yfinance üzerinden güncel hisse fiyatını çeker ve T0 anındaki karar
    ile T+n'i match ederek kimin kazandığını döner (Old vs New).
    """
    try:
        data = yf.Ticker(ticker)
        # Sadece son günlük kapanış fiyatı (mocking API delays via async sleep)
        await asyncio.sleep(0.5) 
        hist = data.history(period="1d")
        if hist.empty:
            return None, None
            
        tn = float(hist["Close"].iloc[-1])
        
        gain = tn - t0
        winner = "TIE"
        
        # BUY kâr getirir, HOLD/SELL zarardan / düşüşten korur
        old_dir = 1 if "BUY" in old_dec else -1
        new_dir = 1 if "BUY" in new_dec else -1
        
        old_perf = old_dir * gain
        new_perf = new_dir * gain
        
        if new_perf > old_perf:
            winner = "NEW"
        elif old_perf > new_perf:
            winner = "OLD"
            
        return tn, winner
    except Exception as e:
        logger.warning(f"Tracker Yfinance fetch failed for {ticker}: {e}")
        return None, None

if __name__ == "__main__":
    asyncio.run(update_missing_pnl())

import asyncio
import os
import httpx
import logging
from datetime import datetime, timezone

from src.core.analysis_engine import AnalysisEngine

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

async def start_alert_scheduler():
    """Arka planda otonom çalışan portföy tarayıcısı (Zero Trust - Service Role)."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("Autonomous Scheduler: Supabase kimlikleri eksik. Uyarı sistemi devre dışı.")
        return

    logger.info("Autonomous Scheduler: Otonom tetikleyici aktif. 12 Saatte bir çalışacak.")
    engine = AnalysisEngine()
    
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    # API ilk kalkışında 1 dakika bekle (sistemin ısınması için)
    await asyncio.sleep(60)

    while True:
        try:
            logger.info("Autonomous Scheduler: Piyasayı izlemek üzere taramaya başlanıyor...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Tüm kullanıcıların ayarlarını çek (Telegram ID vb.)
                resp_settings = await client.get(f"{SUPABASE_URL}/rest/v1/user_settings", headers=headers)
                user_settings_map = {}
                if resp_settings.status_code == 200:
                    for us in resp_settings.json():
                        user_settings_map[us.get("user_id")] = us

                # Cross-Tenant yetkisi: Service Role ile tüm portföyleri çek
                resp = await client.get(f"{SUPABASE_URL}/rest/v1/portfolios?select=user_id,tickers", headers=headers)
                
                if resp.status_code != 200:
                    logger.error(f"Scheduler DB Hatası: {resp.text}")
                    await asyncio.sleep(43200)
                    continue
                
                portfolios = resp.json()
                for portfolio in portfolios:
                    user_id = portfolio.get("user_id")
                    tickers = portfolio.get("tickers", [])
                    chat_id = user_settings_map.get(user_id, {}).get("telegram_chat_id")
                    
                    if not user_id or not tickers:
                        continue
                    
                    for ticker in tickers:
                        if isinstance(ticker, dict): # Eğer frontend'den weight vb. dict geldiyse string'i ayıkla
                            ticker = ticker.get("ticker", str(ticker))
                            
                        try:
                            # Ana motora otonom analiz yaptır
                            res = await asyncio.to_thread(engine._analyze_single, ticker)
                            if not res or ("error" in res and res["error"]):
                                continue
                            
                            alerts = []
                            
                            # Kural 1: %5'ten fazla düşüş
                            fin = res.get("financials", {})
                            son = fin.get("son_fiyat")
                            onceki = fin.get("onceki_kapanis")
                            if son and onceki and onceki > 0:
                                degisim = (son - onceki) / onceki
                                if degisim <= -0.05:
                                    alerts.append(f"{ticker} günlük %{abs(degisim*100):.1f} değer kaybetti!")
                                    
                            # Kural 2: MACD Bearish (Teknik Satım)
                            tech = res.get("technicals", {})
                            tech_signals = tech.get("signals", [])
                            for s in tech_signals:
                                if s.get("signal") == "BEARISH" and "MACD" in s.get("reason", ""):
                                    alerts.append(f"{ticker} teknik analizinde MACD Satım sinyali tespit edildi.")
                            
                            # Kural 3: Karlılık Düşüşü (Temel Analiz Radarı)
                            radar = res.get("radar_score", {})
                            if radar.get("profitability", 50) < 30:
                                alerts.append(f"{ticker} değerlemesinde karlılık skoru alarm seviyesine düştü ({radar.get('profitability')}/100).")
                            
                            # Alarmları DB'ye yaz (Eski notificationları da duplike etmemek için kontrol yapılabilir, şimdilik direkt yazıyoruz)
                            for alert_msg in set(alerts):
                                payload = {
                                    "user_id": user_id,
                                    "ticker": ticker,
                                    "message": alert_msg,
                                    "created_at": datetime.now(timezone.utc).isoformat(),
                                    "is_read": False
                                }
                                await client.post(f"{SUPABASE_URL}/rest/v1/alerts", headers=headers, json=payload)
                                
                                # Telegram push (Senkronizasyonu bozmamak için try-except)
                                if chat_id and TELEGRAM_BOT_TOKEN:
                                    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                                    try:
                                        await client.post(tg_url, json={"chat_id": chat_id, "text": f"🔔 Otonom Uyarı ({ticker}):\n{alert_msg}"})
                                    except Exception as tg_err:
                                        logger.error(f"Telegram Webhook Hatası ({user_id}): {tg_err}")
                            
                        except Exception as e:
                            logger.error(f"Scheduler Ticker Analiz Hatası ({ticker}): {e}")
                        
                        # Rate Limiting Koruması: Her hisse arasında 4 saniye bekle
                        await asyncio.sleep(4)
                        
        except asyncio.CancelledError:
            logger.info("Autonomous Scheduler kapatılıyor (FastAPI Shutdown)...")
            break
        except Exception as e:
            logger.error(f"Autonomous Scheduler Çöktü: {e}")
        
        # 12 Saat bekle (43200 saniye)
        logger.info("Autonomous Scheduler: Tarama bitti. Ukuya geçiliyor (12 Saat).")
        await asyncio.sleep(43200)

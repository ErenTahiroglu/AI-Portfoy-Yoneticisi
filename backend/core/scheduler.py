import asyncio
import os
import httpx
import logging
from datetime import datetime, timezone

from backend.core.analysis_engine import AnalysisEngine

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
                    
                    portfolio_return_sum = 0.0
                    total_weight = 0.0
                    
                    for item in tickers:
                        # Extract ticker and weight safely
                        ticker = item.get("ticker", str(item)) if isinstance(item, dict) else item
                        weight = float(item.get("weight", 1.0)) if isinstance(item, dict) else 1.0
                        
                        try:
                            # Ana motora otonom analiz yaptır
                            res = await asyncio.to_thread(engine._analyze_single, ticker)
                            if not res or ("error" in res and res["error"]):
                                continue
                            
                            alerts = []
                            
                            fin = res.get("financials", {})
                            son = fin.get("son_fiyat")
                            onceki = fin.get("onceki_kapanis")
                            
                            # Snapshot için Getiri Hesapla
                            if son and onceki and onceki > 0:
                                degisim = (son - onceki) / onceki
                                portfolio_return_sum += degisim * weight
                                total_weight += weight
                                
                                # Kural 1: %5'ten fazla düşüş
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
                            
                            # Alarmları DB'ye yaz
                            for alert_msg in set(alerts):
                                payload = {
                                    "user_id": user_id,
                                    "ticker": ticker,
                                    "message": alert_msg,
                                    "created_at": datetime.now(timezone.utc).isoformat(),
                                    "is_read": False
                                }
                                await client.post(f"{SUPABASE_URL}/rest/v1/alerts", headers=headers, json=payload)
                                
                                # Telegram push
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

                    # --- PORTFOLIO SNAPSHOT (Equity Curve) ---
                    if total_weight > 0:
                        try:
                            avg_weighted_return = portfolio_return_sum / total_weight
                            
                            # Son snapshot'ı çek
                            hist_url = f"{SUPABASE_URL}/rest/v1/portfolio_snapshots?user_id=eq.{user_id}&order=timestamp.desc&limit=1"
                            hist_resp = await client.get(hist_url, headers=headers)
                            
                            prev_total_value = 10000.0  # Varsayılan başlangıç
                            prev_cash = 0.0
                            
                            if hist_resp.status_code == 200:
                                hist_data = hist_resp.json()
                                if hist_data:
                                    prev_total_value = float(hist_data[0].get("total_value", 10000.0))
                                    prev_cash = float(hist_data[0].get("cash_balance", 0.0))
                            
                            # Yeni Toplam Değer Hesabı (Bileşik Getiri)
                            new_total_value = prev_total_value * (1 + avg_weighted_return)
                            
                            # DB'ye yaz
                            snap_payload = {
                                "user_id": user_id,
                                "total_value": round(new_total_value, 2),
                                "cash_balance": round(prev_cash, 2),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                            await client.post(f"{SUPABASE_URL}/rest/v1/portfolio_snapshots", headers=headers, json=snap_payload)
                            logger.info(f"Snapshot alındı: {user_id} -> {new_total_value:.2f}")
                        except Exception as snap_err:
                            logger.error(f"Snapshot Hatası ({user_id}): {snap_err}")
                        
        except asyncio.CancelledError:
            logger.info("Autonomous Scheduler kapatılıyor (FastAPI Shutdown)...")
            break
        except Exception as e:
            logger.error(f"Autonomous Scheduler Çöktü: {e}")
        
        # 12 Saat bekle (43200 saniye)
        logger.info("Autonomous Scheduler: Tarama bitti. Ukuya geçiliyor (12 Saat).")
        await asyncio.sleep(43200)

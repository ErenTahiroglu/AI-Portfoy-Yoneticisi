import os
import httpx
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

async def execute_paper_trades(current_weights: dict, optimal_weights: dict, user_id: str) -> str:
    """
    Karşılaştırmalı ağırlık farklarını hesaplayıp Supabase'e sanal emirleri iletir.
    """
    supa_url = os.getenv('SUPABASE_URL', '')
    # Service role key kullanarak bypass yapıyoruz row level security'yi backend server üzerinden
    supa_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
    
    if not supa_url or not supa_key:
        return "Sanal Emir İletimi Başarısız: Supabase env değişkenleri eksik."

    orders = []
    log_messages = []
    
    all_tickers = set(list(current_weights.keys()) + list(optimal_weights.keys()))
    
    for ticker in all_tickers:
        cur = current_weights.get(ticker, 0.0)
        opt = optimal_weights.get(ticker, 0.0)
        delta = opt - cur
        
        if abs(delta) < 0.5:  # %0.5'ten küçük oynamaları önemsiz say
            continue
            
        order_type = "BUY" if delta > 0 else "SELL"
        
        order_obj = {
            "user_id": user_id,
            "symbol": ticker.upper(),
            "order_type": order_type,
            "target_weight": round(opt, 2),
            "execution_price": 0.0,  # Sanal fiyat placeholder
            "timestamp": datetime.now().isoformat()
        }
        orders.append(order_obj)
        log_messages.append(f"- **{ticker.upper()}**: {'ALIM' if order_type == 'BUY' else 'SATIŞ'} (Hedef Ağırlık: %{round(opt, 1)})")

    if not orders:
        return "Mevcut pozisyonlarda dengeleme gerektirecek anlamlı bir ağırlık farkı (%0.5+) bulunamadı."

    try:
        url = f"{supa_url}/rest/v1/paper_trades"
        headers = {
            "apikey": supa_key,
            "Authorization": f"Bearer {supa_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=orders, headers=headers)
            if resp.status_code in [201, 200]:
                return f"✅ **{len(orders)} adet sanal emir iletildi:**\n" + "\n".join(log_messages)
            else:
                return f"❌ **Sanal Emir İletim Hatası (DB)**: {resp.status_code} - {resp.text}"
    except Exception as e:
        return f"❌ **Sanal Emir İletim Hatası**: {str(e)}"

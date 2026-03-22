import os
import httpx
import logging
import jwt
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timedelta

from backend.api.auth import verify_jwt, SUPABASE_JWT_SECRET

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# ── Role Verification Dependency ─────────────────────────────────────────
async def verify_admin_role(request: Request, payload=Depends(verify_jwt)):
    """Sadece 'admin' rolünü taşıyan kullanıcıların geçişine izin verir."""
    user_id = payload.get("sub")
    if not user_id:
         raise HTTPException(status_code=403, detail="Kullanıcı kimliği bulunamadı.")
         
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Bypasses RLS to read role
    
    if not url or not key:
         logger.error("Admin Auth: Missing Supabase Env Credentials.")
         raise HTTPException(status_code=500, detail="Sistem yetkilendirme yapılandırması eksik.")

    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "apikey": key,
                "Authorization": f"Bearer {key}",
            }
            # user_settings tablosundaki rolü oku
            resp = await client.get(
                f"{url}/rest/v1/user_settings?user_id=eq.{user_id}&select=role",
                headers=headers
            )
            data = resp.json()
            if not data or data[0].get("role") != "admin":
                 logger.warning(f"Unauthorized Admin Access Attempt: {user_id}")
                 raise HTTPException(status_code=403, detail="Yönetici yetkiniz bulunmamaktadır.")
                 
            return user_id # Admin confirmed
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin verification error: {e}")
        raise HTTPException(status_code=500, detail="Rol doğrulanamadı.")

# ── Admin Metrics Endpoint ───────────────────────────────────────────────
@router.get("/metrics", dependencies=[Depends(verify_admin_role)])
async def get_admin_metrics():
    """
    Süper Yönetici Paneli için kritik metrikleri toplar:
    - Toplam Kullanıcı Sayısı
    - Toplam Sanal Bakiye (AUM)
    - Son 24 Saatte Total LLM Cost ($)
    - En Aktif 5 Kullanıcı
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase configs missing.")
        
    async with httpx.AsyncClient() as client:
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
        }
        
        try:
            # 1. Total Users Count (from user_settings rows)
            # PostgREST count='exact' in header: Prefer: count=exact
            cnt_resp = await client.get(
                f"{url}/rest/v1/user_settings?select=user_id",
                headers={**headers, "Prefer": "count=exact"}
            )
            # Get count from range header '0-9/10' -> total is 10
            total_users = 0
            if "Content-Range" in cnt_resp.headers:
                 total_users = int(cnt_resp.headers["Content-Range"].split("/")[-1])
            else:
                 total_users = len(cnt_resp.json())

            # 2. Total Virtual Balance (AUM)
            # Fetch all snapshots and compute latest sum per user in Python
            snap_resp = await client.get(
                f"{url}/rest/v1/portfolio_snapshots?select=user_id,total_value,timestamp&order=timestamp.desc",
                headers=headers
            )
            snapshots = snap_resp.json()
            
            latest_values = {}
            for snap in snapshots:
                uid = snap["user_id"]
                val = float(snap["total_value"])
                if uid not in latest_values: # Order desc ensures the first is latest
                    latest_values[uid] = val
                    
            aum = sum(latest_values.values())

            # 3. Son 24 Saat LLM Maliyeti
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
            usage_resp = await client.get(
                f"{url}/rest/v1/llm_usage_logs?timestamp=gte.{yesterday}&select=cost_usd,user_id",
                headers=headers
            )
            usages = usage_resp.json()
            cost_24h = sum(float(u.get("cost_usd", 0)) for u in usages)

            # 4. En Aktif 5 Kullanıcı (LLM logs count per user)
            all_usage_resp = await client.get(
                f"{url}/rest/v1/llm_usage_logs?select=user_id",
                headers=headers
            )
            all_usages = all_usage_resp.json()
            
            active_counts = {}
            for u in all_usages:
                 uid = u["user_id"]
                 active_counts[uid] = active_counts.get(uid, 0) + 1
                 
            # Sort and pick top 5
            top_users = sorted(active_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            formatted_top_users = []
            for uid, count in top_users:
                 formatted_top_users.append({
                     "user_id": uid,
                     "usage_count": count
                 })

            # Daily usage cost chart data (7 Days)
            days_7_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            chart_resp = await client.get(
                f"{url}/rest/v1/llm_usage_logs?timestamp=gte.{days_7_ago}&select=cost_usd,timestamp",
                headers=headers
            )
            chart_usages = chart_resp.json()
            
            # Aggregate by day
            daily_costs = {}
            for u in chart_usages:
                 day = u["timestamp"][:10] # YYYY-MM-DD
                 daily_costs[day] = daily_costs.get(day, 0.0) + float(u.get("cost_usd", 0))
                 
            chart_data = [{"date": k, "cost": v} for k, v in sorted(daily_costs.items())]

            return {
                "total_users": total_users,
                "aum": round(aum, 2),
                "cost_24h": round(cost_24h, 4),
                "top_users": formatted_top_users,
                "chart_data": chart_data
            }

        except Exception as e:
            logger.error(f"Metrics load failure: {e}")
            raise HTTPException(status_code=500, detail="Platform metrikleri toplanamadı.")

import os
import httpx
import asyncio
import jwt
from datetime import datetime, timezone

# --- CONFIGURATION ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

async def test_env_variables():
    print("📋 [1/5] Checking Environment Variables...")
    vars_to_check = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_ROLE_KEY": "SET" if SUPABASE_KEY else "MISSING",
        "SUPABASE_JWT_SECRET": "SET" if JWT_SECRET else "MISSING",
    }
    for k, v in vars_to_check.items():
        print(f"  - {k}: {v}")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ CRITICAL: Supabase URL or Key is missing!")
        return False
    return True

async def test_supabase_connectivity():
    print("\n🔗 [2/5] Testing Supabase REST Connectivity...")
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    tables = ["portfolios", "paper_trades", "portfolio_snapshots", "user_settings"]
    success_count = 0
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for table in tables:
            url = f"{SUPABASE_URL}/rest/v1/{table}?limit=1"
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code in (200, 204, 206):
                    print(f"  ✅ Table '{table}': OK (HTTP {resp.status_code})")
                    success_count += 1
                else:
                    print(f"  ❌ Table '{table}': FAILED (HTTP {resp.status_code})")
                    print(f"     Detail: {resp.text}")
            except Exception as e:
                print(f"  ❌ Table '{table}': ERROR ({str(e)})")
    
    return success_count == len(tables)

async def test_jwt_verification():
    print("\n🛡️ [3/5] Testing JWT Verification logic...")
    if not JWT_SECRET:
        print("  ⚠️ Skipping JWT check: SUPABASE_JWT_SECRET is not set.")
        return False
        
    try:
        # Generate a test token that mimics Supabase's format
        test_payload = {
            "sub": "00000000-0000-0000-0000-000000000000",
            "email": "test@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "exp": int(datetime.now(timezone.utc).timestamp()) + 3600
        }
        token = jwt.encode(test_payload, JWT_SECRET, algorithm="HS256")
        
        # Try to decode it
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        if decoded["sub"] == test_payload["sub"]:
            print("  ✅ JWT Mock Sign/Verify: OK")
            return True
    except Exception as e:
        print(f"  ❌ JWT Test Error: {str(e)}")
    return False

async def test_yahoo_finance_search():
    print("\n📈 [4/5] Testing Yahoo Finance Egress (US vs TR)...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {"User-Agent": "Mozilla/5.0"}
        
        # Test 1: US Search
        try:
            res_us = await client.get("https://query2.finance.yahoo.com/v1/finance/search?q=AAPL&quotesCount=1", headers=headers)
            if res_us.status_code == 200:
                print("  ✅ US Search (AAPL): OK")
            else:
                print(f"  ❌ US Search (AAPL): FAILED (HTTP {res_us.status_code})")
        except Exception as e:
            print(f"  ❌ US Search (AAPL): ERROR ({str(e)})")

        # Test 2: TR Search
        try:
            res_tr = await client.get("https://query2.finance.yahoo.com/v1/finance/search?q=THYAO.IS&quotesCount=1", headers=headers)
            if res_tr.status_code == 200:
                print("  ✅ TR Search (THYAO.IS): OK")
            else:
                print(f"  ❌ TR Search (THYAO.IS): FAILED (HTTP {res_tr.status_code})")
        except Exception as e:
            print(f"  ❌ TR Search (THYAO.IS): ERROR ({str(e)})")

async def test_api_endpoints():
    print("\n🚀 [5/5] Checking Public API Health Endpoints...")
    # This assumes the server is running locally on 8000 or it tests the remote one
    # We will test the local one if possible, otherwise skip.
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:8000/api/health")
            if resp.status_code == 200:
                print(f"  ✅ Local Health Check: OK ({resp.json()})")
            else:
                print(f"  ⚠️ Local Health Check: Failed or Server Not Running.")
    except:
        print("  ℹ️ Local Server not detected. Skipping endpoint check.")

async def main():
    print("="*50)
    print("🏁 [BACKGROUND CONNECTIVITY TEST] 🏁")
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print("="*50)
    
    env_ok = await test_env_variables()
    if env_ok:
        await test_supabase_connectivity()
        await test_jwt_verification()
    
    await test_yahoo_finance_search()
    await test_api_endpoints()
    
    print("\n"+"="*50)
    print("📡 [TEST COMPLETE] 📡")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())

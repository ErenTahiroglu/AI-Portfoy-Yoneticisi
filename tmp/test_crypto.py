import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.analysis_engine import AnalysisEngine
import asyncio

async def test():
    engine = AnalysisEngine()
    # Test BTCUSDT
    result = await engine.analyze([{"ticker": "BTCUSDT", "weight": 1}])
    print("\n=== BTCUSDT Analiz Sonucu ===")
    for r in result:
        print(f"Ticker: {r.get('ticker')}")
        print(f"Market: {r.get('market')}")
        print(f"Status: {r.get('status')}")
        if 'financials' in r:
            print(f"Son Fiyat: {r['financials'].get('son_fiyat')}")
        if 'klines' in r:
            print(f"Mum Verisi (Klines) Sayısı: {len(r['klines'])}")
        if 'error' in r:
            print(f"Hata: {r['error']}")

if __name__ == "__main__":
    asyncio.run(test())

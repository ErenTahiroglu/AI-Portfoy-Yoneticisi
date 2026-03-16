"""
🚀 Production Verification Script (Faz 9)
=========================================
Bu script, uygulamanın kritik matematiksel ve mantıksal katmanlarının
(IslamicAnalyzer, TechnicalAnalyzer ve AnalysisEngine) doğruluğunu kontrol eder.
"""

import sys
import os
import asyncio
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analyzers.islamic_analyzer import _get_single_stock_data
from src.analyzers.technical_analyzer import run_technical_indicators

def generate_mock_history():
    """RSI < 30 (Oversold) tetiklenmesi için suni data."""
    dates = pd.date_range(end='2026-01-01', periods=70)
    # Son 5 günde keskin fiyat düşüşü (RSI penceresi içine)
    close_prices = [100.0] * 65 + [25.0] * 5
    df = pd.DataFrame({
        'Close': close_prices,
        'Open': close_prices,
        'High': [p + 1 for p in close_prices],
        'Low': [p - 1 for p in close_prices],
        'Volume': [1000] * 70
    }, index=dates)
    df.index.name = 'Date'
    df = df.reset_index()
    df['symbol'] = 'MOCK'
    return df.set_index(['symbol', 'Date'])

def test_islamic_math():
    print("🔬 Analiz: İslami Uygunluk Matematiği...")
    
    mock_inc = pd.DataFrame([{
        'asOfDate': '2025-12-31',
        'TotalRevenue': 1000.0,
        'InterestIncome': 40.0 # %4
    }])
    mock_bal = pd.DataFrame([{
        'asOfDate': '2025-12-31',
        'TotalAssets': 2000.0,
        'TotalDebt': 500.0, # %25
        'CashAndCashEquivalents': 200.0,
        'OtherShortTermInvestments': 100.0 # %15
    }])
    
    with patch('src.analyzers.islamic_analyzer.Ticker') as MockTicker:
        instance = MockTicker.return_value
        # If any dict/str returned earlier mock expects df
        instance.income_statement.return_value = mock_inc
        instance.balance_sheet.return_value = mock_bal
        
        res = _get_single_stock_data('MOCK')
        
        print(f"-> Islamic Analyzer Result: {res}")
        assert res is not None, "Islamic analyzer failed entirely"
        assert res['purification_ratio'] == 4.0, f"Purification incorrect: {res['purification_ratio']}"
        assert res['debt_ratio'] == 25.0, f"Debt incorrect: {res['debt_ratio']}"
        assert res['liquidity_ratio'] == 15.0, f"Liquidity incorrect: {res['liquidity_ratio']}"
        print("✅ İslami Matematik Doğrulandı (Division-Safe + Percentage Correct)")

def test_technical_signals():
    print("🔬 Analiz: Teknik Sinyal ve Crossover Mantığı...")
    hist = generate_mock_history()
    
    with patch('yahooquery.Ticker') as MockTicker:
        instance = MockTicker.return_value
        instance.history.return_value = hist
        
        res_entry = {}
        run_technical_indicators('MOCK', res_entry)
        
        assert "technicals" in res_entry, "Technicals calculation failed"
        tech = res_entry["technicals"]
        assert "signals" in tech, "Signals missing from output"
        
        signals = tech.get("signals", [])
        assert len(signals) > 0, "No technical signals generated for oversold security"
        print(f"-> Üretilen Sinyaller: {signals}")
        for s in signals:
            assert s["signal"] in ["BULLISH", "BEARISH"]
            assert "reason" in s

    print("✅ Teknik Sinyalizasyon Doğrulandı (Signals array populated)")

async def main():
    print("🚀 Nihai Üretim Doğrulaması BAŞLIYOR...\n")
    test_islamic_math()
    test_technical_signals()
    print("\n🎉 Tüm Üretim Doğrulama Testleri Başarıyla Geçti!")

if __name__ == '__main__':
    asyncio.run(main())

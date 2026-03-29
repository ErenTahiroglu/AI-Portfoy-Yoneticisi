"""
🚀 Nihai Üretim Doğrulaması (Production Verification)
===================================================
Bu betik, AI Portfoy Yoneticisi projesinin finansal matematik,
mantıksal akış ve hata yakalama mekanizmalarını AGRESİF bir şekilde test eder.
Sıfıra bölme, NaN üretme veya çökmeye sebep olabilecek durumları denetler.
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch

# Proje kök dizinini Python yoluna ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test Edilecek Modüller
from backend.analyzers.islamic_analyzer import _get_single_stock_data
from backend.analyzers.technical_analyzer import run_technical_indicators
from backend.infrastructure.analysis_engine import AnalysisEngine, analyzer_registry

class TestProductionIntegrity(unittest.TestCase):

    def setUp(self):
        print(f"\n--- {self._testMethodName} BAŞLIYOR ---")

    # ══════════════════════════════════════════════════════════════════════
    # Bölüm 1: İslami Analiz ve Matematik Denetimi
    # ══════════════════════════════════════════════════════════════════════

    @patch('backend.analyzers.islamic_analyzer.Ticker')
    def test_islamic_math_correctness(self, MockTicker):
        """AAOIFI Standartları: Temel oranların doğruluğunu test eder."""
        mock_inc = pd.DataFrame([{
            'asOfDate': '2025-12-31',
            'TotalRevenue': 1000.0,
            'InterestIncome': 50.0 # %5
        }])
        mock_bal = pd.DataFrame([{
            'asOfDate': '2025-12-31',
            'TotalAssets': 2000.0,
            'TotalDebt': 600.0, # %30
            'CashAndCashEquivalents': 200.0,
            'OtherShortTermInvestments': 400.0 # Total %30
        }])
        
        instance = MockTicker.return_value
        instance.income_statement.return_value = mock_inc
        instance.balance_sheet.return_value = mock_bal
        
        res = _get_single_stock_data('AAPL')
        
        self.assertIsNotNone(res)
        self.assertEqual(res['purification_ratio'], 5.0)
        self.assertEqual(res['debt_ratio'], 30.0)
        self.assertEqual(res['liquidity_ratio'], 30.0)
        print("✅ Standart Hesaplama: Başarılı")

    @patch('backend.analyzers.islamic_analyzer.Ticker')
    def test_islamic_zero_division_guard(self, MockTicker):
        """AAOIFI: Sıfıra bölme hatasının engellendiğini test eder (Revenue/Assets = 0)."""
        # Gelir 0 durumu
        mock_inc = pd.DataFrame([{'asOfDate': '2025-12-31', 'TotalRevenue': 0.0, 'InterestIncome': 10.0}])
        mock_bal = pd.DataFrame([{'asOfDate': '2025-12-31', 'TotalAssets': 1000.0, 'TotalDebt': 100.0}])
        
        instance = MockTicker.return_value
        instance.income_statement.return_value = mock_inc
        instance.balance_sheet.return_value = mock_bal
        
        # Sıfır geliri olan hisse için None dönmeli (ZeroDivisionError yerine)
        res = _get_single_stock_data('ZERO_REV')
        self.assertIsNone(res)
        print("✅ Sıfır Gelir Koruması: Başarılı")

        # Varlık 0 durumu
        mock_inc_2 = pd.DataFrame([{'asOfDate': '2025-12-31', 'TotalRevenue': 100.0, 'InterestIncome': 10.0}])
        mock_bal_2 = pd.DataFrame([{'asOfDate': '2025-12-31', 'TotalAssets': 0.0, 'TotalDebt': 100.0}])
        
        # Mock sıfırlama / güncelleme
        instance.income_statement.return_value = mock_inc_2
        instance.balance_sheet.return_value = mock_bal_2
        
        res2 = _get_single_stock_data('ZERO_AST')
        self.assertIsNone(res2)
        print("✅ Sıfır Varlık Koruması: Başarılı")


    # ══════════════════════════════════════════════════════════════════════
    # Bölüm 2: Teknik Analiz ve Sinyal Denetimi
    # ══════════════════════════════════════════════════════════════════════

    @patch('yahooquery.Ticker')
    def test_technical_indicators_and_signals(self, MockTicker):
        """RSI ve MACD Sinyallerinin oluşma mantığını test eder."""
        dates = pd.date_range(end='2026-01-01', periods=100)
        # Sine wave to guarantee both up and down days for non-zero gains/losses
        close_prices = [10.0 + np.sin(i/5) * 2 for i in range(100)]
        
        df = pd.DataFrame({
            'Close': close_prices,
            'Open': close_prices,
            'High': [p + 0.5 for p in close_prices],
            'Low': [p - 0.5 for p in close_prices],
        }, index=dates)
        df.index.name = 'Date'
        df = df.reset_index()
        df['symbol'] = 'MOCK'
        hist = df.set_index(['symbol', 'Date'])

        instance = MockTicker.return_value
        instance.history.return_value = hist
        
        res_entry = {}
        run_technical_indicators('MOCK', res_entry)
        
        self.assertIn("technicals", res_entry)
        tech = res_entry["technicals"]
        self.assertIn("rsi_14", tech)
        self.assertTrue(0 <= tech["rsi_14"] <= 100)
        self.assertIn("gauge_score", tech)
        
        print(f"-> RSI: {tech.get('rsi_14')}, Gauge Score: {tech.get('gauge_score')}")
        print("✅ Teknik Göstergeler: Başarılı")

    @patch('yahooquery.Ticker')
    def test_technical_analyzer_rebase_zero_guard(self, MockTicker):
        """Relative Performance ilk fiyatı 0 ise çökmeme testidir."""
        dates = pd.date_range(end='2026-01-01', periods=50)
        # İlk fiyat 0 (Data bozukluğu testi)
        close_prices = [0.0] + [10.0] * 49
        df = pd.DataFrame({
            'Close': close_prices, 'Open': close_prices, 'High': close_prices, 'Low': close_prices
        }, index=dates)
        df.index.name = 'Date'
        df = df.reset_index()
        df['symbol'] = 'ZERO_START'
        hist = df.set_index(['symbol', 'Date'])

        instance = MockTicker.return_value
        instance.history.return_value = hist
        
        res_entry = {}
        # Hata fırlatmamalı, relative_performance hesaplanmayıp es geçilmeli
        try:
            run_technical_indicators('ZERO_START', res_entry)
            tech = res_entry.get("technicals", {})
            # relative_performance dict içinde olmamalı (rebase guard yakaladı)
            self.assertNotIn("relative_performance", tech)
            print("✅ Zero Rebase Guard: Başarılı (Çökme Engellendi)")
        except ZeroDivisionError:
            self.fail("ZeroDivisionError: Relative Performance'da ilk fiyat 0 kontrolü eksik!")


    # ══════════════════════════════════════════════════════════════════════
    # Bölüm 3: Registry ve Genel Orkestrasyon
    # ══════════════════════════════════════════════════════════════════════

    def test_registry_integration(self):
        """Stratejilerin doğru register edildiğini test eder."""
        # AnalysisEngine başlatılarak stratejilerin kaydı tetiklenir
        _ = AnalysisEngine()
        strategies = analyzer_registry.get_strategies()
        self.assertTrue(len(strategies) > 0)
        names = [s.name for s in strategies]
        self.assertIn("islamic", names)
        self.assertIn("technical", names)
        self.assertIn("financial", names)
        print(f"-> Kayıtlı Stratejiler: {names}")
        print("✅ Registry Entegrasyonu: Başarılı")

if __name__ == '__main__':
    print("\n🚀 AI Portfoy Yöneticisi AGRESİF Üretim Doğrulama Testi Başlatılıyor...\n")
    unittest.main()

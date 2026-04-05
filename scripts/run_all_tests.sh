#!/bin/bash

# 🛡️ AI-Portfoy-Yoneticisi: Unified Autonomous Test Runner
# =======================================================
# Bu script, hem Backend (Python) hem de Frontend (JS) testlerini 
# paralel çalıştırır ve sonuçları 'test_report.log' içine yazar.

LOG_FILE="test_report.log"
echo "🚀 [Otonom QA] Test süreci başlatılıyor... Tarih: $(date)" > $LOG_FILE
echo "--------------------------------------------------------" >> $LOG_FILE

# 1. Beklentiler: VirtualEnv ve Node_Modules var mı?
if [ ! -d "venv" ]; then
    echo "❌ HATA: 'venv' dizini bulunamadı. Lütfen önce kurulumu yapın." | tee -a $LOG_FILE
    exit 1
fi

# 2. Backend Testleri (Pytest & Chaos)
echo "🐍 [BACKEND] Pytest (Hardening & Chaos) çalıştırılıyor..." | tee -a $LOG_FILE
mkdir -p /tmp/prometheus_multiproc_dir
export PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc_dir

source venv/bin/activate
# Yeni eklenen isolation, precision ve chaos testlerini de dahil et
pytest backend/tests/test_logic_hardening.py \
       backend/tests/test_llm_chaos.py \
       backend/tests/test_financial_integrity.py \
       backend/tests/test_chaos_engineering.py \
       backend/tests/test_pnl_isolation.py \
       backend/tests/test_decimal_precision_v3.py \
       backend/tests/test_shadow_pnl_chaos.py \
       --tb=short >> $LOG_FILE 2>&1

PYTEST_EXIT=$?
if [ $PYTEST_EXIT -eq 0 ]; then
    echo "✅ [BACKEND] Tüm mantık, izolasyon ve hassasiyet testleri BAŞARILI." | tee -a $LOG_FILE
else
    echo "⚠️  [BACKEND] Bazı testler BAŞARISIZ. Lütfen '$LOG_FILE' dosyasını inceleyin." | tee -a $LOG_FILE
fi

echo "--------------------------------------------------------" >> $LOG_FILE

# 3. Frontend Testleri (Vitest)
echo "⚛️  [FRONTEND] Vitest (Math Stress & State) çalıştırılıyor..." | tee -a $LOG_FILE
npm run test frontend/tests/unit/state_resilience.test.js \
             frontend/tests/unit/math_stress.test.js \
             frontend/tests/unit/financial_friction.test.js -- --run >> $LOG_FILE 2>&1

VITEST_EXIT=$?
if [ $VITEST_EXIT -eq 0 ]; then
    echo "✅ [FRONTEND] Tüm matematiksel stress ve state testleri BAŞARILI." | tee -a $LOG_FILE
else
    echo "⚠️  [FRONTEND] Bazı testler BAŞARISIZ. Lütfen '$LOG_FILE' dosyasını inceleyin." | tee -a $LOG_FILE
fi

echo "--------------------------------------------------------" >> $LOG_FILE
echo "🏁 [Otonom QA] Test süreci tamamlandı." | tee -a $LOG_FILE

# Final Durum
if [ $PYTEST_EXIT -eq 0 ] && [ $VITEST_EXIT -eq 0 ]; then
    echo "⭐⭐⭐ SISTEM GÜVENİLİR DURUMDADIR ⭐⭐⭐" | tee -a $LOG_FILE
    exit 0
else
    echo "🚩🚩🚩 SISTEM RİSKLİ DURUMDADIR 🚩🚩🚩" | tee -a $LOG_FILE
    exit 1
fi

<div align="center">
  
# 📊 Portföy Analiz Platformu — AI Destekli
### (AI-Powered Portfolio Analysis Platform)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-AI-orange.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Türkçe (Turkish)

**Portföy Analiz Platformu (v4.3)**, ABD hisseleri, Borsa İstanbul (BIST) hisseleri ve TEFAS fonlarını aynı anda analiz edebilen, yapay zeka destekli yerel bir web uygulamasıdır. 

Finansal verileri hesaplar, opsiyonel olarak İslami uygunluk (AAOIFI) denetimi yapar, sonuçları Google Gemini AI modeli ile yorumlar ve modern, mobil uyumlu, logolu bir arayüz sunar.

### ✨ Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🌍 **Çoklu Piyasa** | ABD (NYSE/NASDAQ), BIST ve TEFAS hisselerini karışık girin — pazar **otomatik algılanır** |
| 🛡️ **TEFAS Entegrasyonu** | `curl_cffi` tabanlı scraper ile WAF engellerini aşan, 180 günlük akıllı chunk'larla hızlı veri çekimi |
| 🌟 **Portfolio Visualizer (PV)** | Kompakt Profesyonel Mod, Dinamik Nakit Akışı & Yeniden Dengeleme Simülatörü ve Drawdown Sualtı Grafikleri |
| 🤖 **AI Portföy Sihirbazı & Copilot** | Metin girişiyle portföy kurdurma ve yüzen **AI Copilot** widget'ı ile anında portföy sorgulama |
| 📊 **Premium UX Grafikleri** | Fintables stili **Finansal Sağlık Radarı**, TradingView stili **Teknik Kadran (Gauge)** ve Koyfin stili **Göreli Performans** |
| 🕌 **İslami Finans (Zoya Stili)** | Hisse bazında detaylı Haram Gelir ve Faizli Borç ilerleme çubukları |
| 🗺️ **Dinamik Isı Haritası** | Finviz stili anlık F/K, Temettü ve Günlük Değişim filtreli interaktif Treemap |
| 🔍 **Gelişmiş Metrikler** | Sortino, Calmar, Max Drawdown hesaplamaları ve ABD pazarı için Fama-French proxy Faktör Regresyonu |
| 🛡️ **Stres Testleri** | Tech Crash, 2008 Krizi, Covid-19 simülasyonları ile modern **Market Shock Gauge** kadranı |
| 📈 **Teknik Göstergeler** | RSI, MACD, EMA/SMA hareketli ortalamalar ve trend analizi |
| 🎲 **Monte Carlo** | 200 simülasyon × 1 yıl — portföy risk/getiri fan grafiği |
| 🪄 **Autocomplete** | Türkçe/İngilizce harf duyarlı, 1-2 harften itibaren akıllı öneriler |
| 📥 **Dışa Aktarım** | Excel, PDF, Word formatlarında profesyonel rapor indirme |

### 🛠️ Kurulum ve Çalıştırma

```bash
# Depoyu klonlayın
git clone https://github.com/ErenTahiroglu/AI-Portfoy-Yoneticisi.git
cd AI-Portfoy-Yoneticisi

# Sanal ortam oluşturun ve aktif edin
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
uvicorn src.api.main:app --reload
```
Uygulamaya `http://127.0.0.1:8000/ui` adresinden erişebilirsiniz.

### 🧩 Modüler Mimari (Puzzle Modeli)

*   `src/api/`: FastAPI endpointleri ve yönlendirmeler (Routing).
*   `src/core/`: Analiz orkestratörü (`analysis_engine.py`), Monte Carlo ve AI motoru.
*   `src/analyzers/`: Temel Değerleme (`valuation_analyzer`), Teknik Analiz (`technical_analyzer`), BIST, US ve İslami izole modüller.
*   `src/data/`: Data sağlayıcılar, `constants.py` (hisse listeleri) ve Market Detector.
*   `src/frontend/`: Glassmorphism tasarımlı modern arayüz.
*   `src/utils/`: Dosya işleme ve rapor dışa aktarma araçları.

---

## English

**Portfolio Analysis Platform (v4.3)** is a locally-hosted, AI-powered web application for analyzing US stocks, Borsa Istanbul (BIST) equities, and TEFAS mutual funds simultaneously. It features a modern, mobile-responsive interface with professional branding.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🌍 **Multi-Market** | Mix US, BIST and TEFAS tickers — market is **auto-detected** |
| 🪄 **AI Wizard & Copilot** | Create tailored portfolios instantly from natural language prompts, plus a floating **AI Chat Widget** |
| 📊 **Premium Dashboards** | Financial Health **Radar**, Technical **Gauge** indicators, and Relative Performance charts |
| 🗺️ **Dynamic Heatmap** | Interactive Treemap with P/E, Dividend Yield, and Daily Change filters |
| 🕌 **Shariah Compliance** | Zoya-style detailed purification and debt ratio progress bars |
| 🔍 **Interactive Metrics** | AI-powered custom insights for financial ratios |
| 🌟 **Portfolio Visualizer (PV)** | Compact Professional Mode, Cash Flow Simulation, Max Drawdown Charts and US Factor Regression |
| 🧪 **Premium Stress Tests** | Realistic simulations with modern **Market Shock Gauge** |
| 📈 **Advanced Optimization** | Markowitz Max Sharpe, Min Volatility, and Max Return optimizer options |
| 📥 **Export** | Download reports as Excel, PDF, or Word |
| 🛡️ **Privacy** | 100% local — your data never leaves your machine |

---

### ☁️ Canlı Ortamda Yayınlama (Vercel + Render Çift Mimari)

#### 1. Backend (Render.com)
*   **Build Command:** `pip install -r requirements.txt`
*   **Start Command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

#### 2. Frontend (Vercel)
*   `src/frontend/js/utils.js` dosyasındaki `API_BASE` değişkenini Render URL'iniz ile güncelleyin.
*   Vercel üzerinde projenizi yayına alın.

---
Geliştirici: [Eren Tahiroğlu](https://github.com/ErenTahiroglu)

*Disclaimer: This software is for informational and educational purposes only. It does not constitute financial or investment advice.*

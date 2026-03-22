<div align="center">
  
# 📊 Portföy Analiz Platformu — AI Destekli
### (AI-Powered Portfolio Analysis Platform)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-AI-orange.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Türkçe (Turkish)

**Portföy Analiz Platformu (v8.0)**, ABD hisseleri, Borsa İstanbul (BIST) hisseleri, Kripto Paralar ve TEFAS fonlarını aynı anda analiz edebilen, çoklu-ajan (Multi-Agent) yapay zeka destekli yerel bir web uygulamasıdır. 
Finansal verileri hesaplar, risk analizleri (VaR, MaxDD) yapar, sanal emirlerle (Paper Trading) strateji takibi sağlar, sonuçları Google Gemini AI CIO modülü ile yorumlar ve modern, mobil uyumlu, logolu bir arayüz sunar.

### ✨ Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🌍 **Çoklu Piyasa** | ABD (NYSE/NASDAQ), BIST, Kripto (Binance) ve TEFAS hisselerini karışık girin — pazar **otomatik algılanır** |
| 🤖 **Çoklu-Ajan Mimari (CIO)** | Analist ve Araştırmacı alt ajanlarının raporlarını derleyen **Chief Investment Officer (CIO)** orkestrasyonu |
| 🛡️ **Gelişmiş Risk Motoru** | %95 Güven Aralığı `VaR (Value at Risk)`, Maksimum Düşüş (`Max Drawdown`) ve Ayarlanabilir **Stres Testleri** |
| 📉 **Sanal Emir Sistemi** | Optimize edilen dağılımları `Supabase` üzerinden AL/SAT emirlerine (Paper Trading) dönüştürerek test etme |
| 🔔 **Otonom Alarm Sistemi** | Kritik piyasa seviyelerinde arka planda çalışan ve anında panoya/Telegram'a düşen uyarılar |
| 📊 **Premium UX Grafikleri** | Fintables stili **Finansal Sağlık Radarı**, TV stili **Teknik Kadran** ve Koyfin stili **Göreli Performans** |
| 🕌 **İslami Finans (Zoya Stili)** | Hisse bazında detaylı Haram Gelir ve Faizli Borç ilerleme çubukları (AAOIFI) |
| 🧪 **DCA Backtest** | TradingView lightweight-charts destekli aylık düzenli alım (DCA) ve bakiye büyüme senaryoları |
| 🪄 **Autocomplete** | Türkçe/İngilizce harf duyarlı, 1-2 harften itibaren akıllı öneriler |
| 📥 **Dışa Aktarım** | Excel, PDF, Word formatlarında profesyonel rapor indirme |

### 🛠️ Kurulum ve Çalıştırma

```bash
# Depoyu klonlayın
git clone https://github.com/ErenTahiroglu/AI-Portfoy-Yoneticisi.git
cd AI-Portfoy-Yoneticisi

# Sanal ortam oluşturun ve aktif edin
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Bağımlılıkları yükleyin
pip install -r backend/requirements.txt

# Uygulamayı başlatın
PYTHONPATH=. uvicorn backend.api.main:app --reload
```
Uygulamaya `http://127.0.0.1:8000/ui` adresinden erişebilirsiniz.

### 🧩 Temiz Mimari (Clean Architecture)

*   `backend/api/routers/`: Dekuple edilmiş FastAPI endpointleri (Analysis, Chat, User).
*   `backend/api/models.py`: Pydantic Request/Response şemaları.
*   `backend/core/`: Analiz orkestratörü (`analysis_engine.py`), Multi-Agent Motoru (`ai_agent.py`) ve Emir Motoru (`execution_engine.py`).
*   `frontend/js/components/`: ES6 Modülleri halinde parçalanmış Frontend arayüz kodları.


---

## English

**Portfolio Analysis Platform (v8.0)** is a locally-hosted, Multi-Agent AI web application for analyzing US stocks, BIST equities, Cryptocurrencies, and TEFAS mutual funds. It offers modular codebases, advanced risk calculation algorithms, paper trading verification, and rich modern dashboards.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🌍 **Multi-Market** | Mix US, BIST, Crypto and TEFAS tickers — market is **auto-detected** |
| 🤖 **Multi-Agent Orchestration** | Chief Investment Officer (CIO) agent aggregating reports from Analyst and Researcher agents |
| 🛡️ **Risk Analytics** | Historical %95 confidence `Value at Risk (VaR)`, `Max Drawdown`, and stress tests |
| 📉 **Paper Trading** | Calculates delta difference between current & optimal weights and records virtual market orders |
| 📊 **Premium Dashboards** | Financial Health **Radar**, Technical **Gauge** indicators, and Relative Performance charts |
| 🗺️ **Dynamic Heatmap** | Interactive Treemap with P/E, Dividend Yield, and Daily Change filters |
| 🕌 **Shariah Compliance** | Detailed Shariah (Zoya-style) bars and analysis |
| 📈 **Advanced Optimization** | Markowitz Max Sharpe and Min Volatility optimizer strategies |
| 📥 **Export** | Download reports as Excel, PDF, or Word |

---

### ☁️ Canlı Ortamda Yayınlama (Vercel + Render)

#### 1. Backend (Render.com)
*   **Root Directory:** `backend`
*   **Build Command:** `pip install -r requirements.txt`
*   **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
*   **💡 Multi-Agent Architecture [v7.5]:** `ai_agent.py` birden fazla alt-ajanın (Analist, Araştırmacı) paralelde çalıştıran asenkron CIO yapısına taşındı.
*   **💡 Risk Analyzer & Stress Testing [v7.6]:** %95 Güven Aralığında Günlük VaR, Max Drawdown ve %20 Endeks Şoku kurgusu backend hesaplamalarına bağlandı.
*   **💡 Sanal Emir İletim Sistemi [v7.7]:** Fark Delta hesabı ile paper trade virtual market orders logging and Supabase write flow devrede.
*   **💡 Otonom Bildirim Döngüsü [v7.8]:** Arka planda eşik kontrolü yapıp telegram/panoya alert yazan döngü Lifespan'a entegre edildi.
*   **💡 SOLID & Clean Architecture [v8.0]:** FastAPI Router'ları (`backend/api/routers/`) ve Frontend dosyaları ES6 Modüllerine kırılarak high-level decoupling sağlandı.

#### 2. Frontend (Vercel)
*   **Root Directory:** Proje kök dizini (Root) — Kök dizindeki `vercel.json` otomatik olarak `frontend` klasörünü build eder ve API isteklerini Render'a yönlendirir (Reverse Proxy).
*   `frontend/js/components/` ve `app.js` ES6 Modülleri üzerinden çalışmaktadır.


---
Geliştirici: [Eren Tahiroğlu](https://github.com/ErenTahiroglu)

*Disclaimer: This software is for informational and educational purposes only. It does not constitute financial or investment advice.*

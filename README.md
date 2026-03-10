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

**Portföy Analiz Platformu (v4.0)**, ABD hisseleri, Borsa İstanbul (BIST) hisseleri ve TEFAS fonlarını aynı anda analiz edebilen, yapay zeka destekli yerel bir web uygulamasıdır. 

Finansal verileri (getiri, enflasyon, temettü, risk metrikleri, temel değerleme oranları) hesaplar, opsiyonel olarak İslami uygunluk (AAOIFI) denetimi yapar ve sonuçları Google Gemini AI modeli ile yorumlar.

### ✨ Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🌍 **Çoklu Piyasa** | ABD (NYSE/NASDAQ), BIST ve TEFAS hisselerini karışık girin — pazar **otomatik algılanır** |
| 🛡️ **TEFAS Entegrasyonu** | `curl_cffi` tabanlı scraper ile WAF engellerini aşan, 180 günlük akıllı chunk'larla hızlı veri çekimi |
| 🤖 **AI Portföy Sihirbazı** | Metin girişiyle (örn: "Temettü veren 5 şirket") yapay zekaya anında özel portföy kurdurma |
| 🔍 **İnteraktif Metrikler** | Finansal oranlara (F/K, PDD vb.) tıklayarak statik tanımlar ve **AI destekli özel içgörüler** |
| 🛡️ **Stres Testleri** | Tech Crash, 2008 Krizi, Covid-19 simülasyonları ile modern **Market Shock Gauge** kadranı |
| 📉 **Teknik Göstergeler** | RSI 14, MACD 12/26/9, EMA 20/50/100/200, SMA 20/50/100/200 |
| 🧩 **Sektör Dağılımı** | Portföy genelinde sektör pasta grafiği ve interaktif ısı haritası (Treemap) |
| 🔗 **Korelasyon Matrisi** | Hisseler arası renk kodlu korelasyon ısı haritası |
| 🎲 **Monte Carlo** | 200 simülasyon × 1 yıl — portföy risk/getiri fan grafiği |
| 🪄 **Autocomplete** | Türkçe/İngilizce harf duyarlı, 1-2 harften itibaren akıllı öneriler |
| 📥 **Dışa Aktarım** | Excel, PDF, Word formatlarında profesyonel rapor indirme |
| 🎨 **Premium UX** | Glassmorphism tasarımı, Skeleton Loading, anlık hisse önizleme modalları ve akıcı animasyonlar |

### 🛠️ Kurulum ve Çalıştırma

#### 1. Gereksinimler
*   Python 3.10+
*   Google Gemini API Key (AI yorumları için)

#### 2. Yerelde Çalıştırma
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

Her dosya tek bir sorumluluğa sahiptir. Birbirinden bağımsız geliştirilebilir:

*   `src/api/`: FastAPI endpointleri ve API mantığı.
*   `src/core/`: Analiz orkestratörü, Monte Carlo ve AI motoru.
*   `src/analyzers/`: BIST, US ve İslami analiz araçları.
*   `src/data/`: Data sağlayıcılar, Market Detector ve Haber Akışı.
*   `src/frontend/`: Glassmorphism tasarımlı, i18n destekli modern arayüz (`utils.js`, `api.js`, `charts.js`).
*   `src/utils/`: Dosya işleme ve rapor dışa aktarma araçları.

---

## English

**Portfolio Analysis Platform (v4.0)** is a locally-hosted, AI-powered web application for analyzing US stocks, Borsa Istanbul (BIST) equities, and TEFAS mutual funds simultaneously.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🌍 **Multi-Market** | Mix US, BIST and TEFAS tickers — market is **auto-detected** |
| 🪄 **AI Wizard** | Create tailored portfolios instantly from natural language prompts |
| 🔍 **Interactive Metrics** | Click on financial ratios for static definitions and **AI-powered custom insights** |
| 🧪 **Premium Stress Tests** | Tech Crash, 2008 Crash, Covid-19 simulations with modern **Market Shock Gauge** |
| 📈 **Monte Carlo** | 200 simulations × 1 year — portfolio risk/return fan graphs |
| 📈 **Technical Indicators** | RSI, MACD, EMA, SMA and automated trend analysis |
| ⚖️ **Optimization** | Markowitz Efficient Frontier optimization for Maximum Sharpe ratio weights |
| 📥 **Export** | Download professional reports as Excel, PDF, or Word |
| 🛡️ **Privacy** | 100% local — your data (and API keys) never leave your machine |

### 🚀 How to Run

```bash
git clone https://github.com/ErenTahiroglu/AI-Portfoy-Yoneticisi.git
cd AI-Portfoy-Yoneticisi
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload
```

---

### ☁️ Canlı Ortamda Yayınlama (Vercel + Render Çift Mimari)

Bu proje, alan adınızı kullanabilmeniz ve TEFAS sunucularının ağır bot engellerini aşabilmeniz için **Çift Sunucu (Monorepo) Mimarisi** kullanır.

#### 1. Backend (Render.com)
*   Render üzerinde yeni bir "Web Service" oluşturun.
*   **Build Command:** `pip install -r requirements.txt`
*   **Start Command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`

#### 2. Frontend (Vercel)
*   `src/frontend/js/utils.js` dosyasındaki `API_BASE` değişkenini Render URL'iniz ile güncelleyin.
*   Vercel üzerinde "Add New Project" deyip deponuzu seçin ve yayına alın.

---
Geliştirici: [Eren Tahiroğlu](https://github.com/ErenTahiroglu)

*Disclaimer: This software is for informational and educational purposes only. It does not constitute financial or investment advice. Always verify AI-generated analyses with your own research.*

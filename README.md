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

**Portföy Analiz Platformu**, ABD hisseleri, Borsa İstanbul (BIST) hisseleri ve TEFAS fonlarını aynı anda analiz edebilen, yapay zeka destekli yerel bir web uygulamasıdır.

Finansal verileri (getiri, enflasyon, temettü, risk metrikleri, temel değerleme oranları) hesaplar, opsiyonel olarak İslami uygunluk (AAOIFI) denetimi yapar ve sonuçları Google Gemini AI modeli ile yorumlar.

### ✨ Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🌍 **Çoklu Piyasa** | ABD (NYSE/NASDAQ), BIST ve TEFAS hisselerini karışık girin — pazar **otomatik algılanır** |
| 🛡️ **TEFAS Entegrasyonu** | `curl_cffi` tabanlı gelişmiş scraper ile WAF engellerini aşan, 180 günlük akıllı chunk'larla hızlı veri çekimi |
| 📊 **Değerleme Metrikleri** | P/E, P/B, Beta, Piyasa Değeri, EPS, ROE, Temüttü, 52 hafta aralığı |
| 📈 **Reel Getiri** | ABD ($) ve Türkiye (₺) enflasyon verilerinden arındırılmış gerçek getiri |
| 🎯 **Risk Analizi** | Sharpe Ratio, Maximum Drawdown, yıllık/aylık getiri dağılımı |
| 🔍 **İnteraktif Metrikler** | Finansal oranlara (F/K, PDD vb.) tıklayarak statik tanımlar ve **AI destekli özel içgörüler** |
| 🧪 **Premium Stres Testleri** | Tech Crash, 2008 Krizi, Covid-19 simülasyonları ile modern **Market Shock Gauge** kadranı |
| 🏦 **Temettü Emekliliği** | İstenilen pasif gelire aylık katkılarla ulaşma süresini hesaplayan gelişmiş simülatör |
| 📉 **Teknik Göstergeler** | RSI 14, MACD 12/26/9, EMA 20/50/100/200, SMA 20/50/100/200 |
| 🧩 **Sektör Dağılımı** | Portföy genelinde sektör pasta grafiği ve interaktif ısı haritası (Treemap) |
| 🔗 **Korelasyon Matrisi** | Hisseler arası renk kodlu korelasyon ısı haritası |
| ⚖️ **Portföy Optimizasyonu** | Markowitz Modern Portföy Teorisi (MPT) ile maksimum Sharpe oranlı ideal ağırlık hesabı |
| 🎲 **Monte Carlo** | 200 simülasyon × 1 yıl — portföy risk/getiri fan grafiği |
| 🪄 **AI Portföy Sihirbazı** | Metin girişiyle (örn: "Temettü veren 5 şirket") yapay zekaya anında özel portföy kurdurma |
| 📰 **Dinamik Haberler**| Şirketlere ait son dakika haberlerini AI duygu (sentiment) analiziyle (Bullish/Bearish) listeleme |
| 🤖 **AI Yorumları** | Gemini 2.5 Flash ile profesyonel finansal yorum |
| 🌐 **Çoklu Dil** | Türkçe / İngilizce arayüz desteği (anlık geçiş) |
| 🎨 **Tema Değiştirme** | Manuel açık/koyu tema + sistem teması otomatik algılama |
| 📱 **PWA** | Mobilde veya masaüstünde uygulama olarak kur |
| 📈 **İnteraktif Grafikler** | Chart.js ile yıllık getiri, sektör, Monte Carlo grafikleri |
| 🔍 **Autocomplete** | 60+ popüler ABD & BIST hissesi için öneri |
| 🧠 **Modüler Mimari** | Frontend kodları `utils.js`, `api.js`, `charts.js` olarak ayrılmış "puzzle" prensibiyle çalışır |
| 📋 **Watchlist** | Sık kullandığınız portföyleri kaydedin (localStorage) |
| 📊 **Karşılaştırma** | Hisseleri yan yana tablo ile kıyaslayın |
| 📥 **Dışa Aktarım** | Excel, PDF, Word formatlarında rapor indirin |
| ☪️ **İslami Analiz** | Opsiyonel AAOIFI uygunluk taraması (varsayılan kapalı) |
| 💎 **Premium UX** | Glassmorphism tasarımı, Skeleton Loading, anlık hisse önizleme modalları ve akıcı animasyonlar |
| ⚡ **Paralel Analiz** | Çoklu hisseler ThreadPoolExecutor ile 3-5x hızlı |
| 💾 **Akıllı Cache** | Aynı hisse 5 dakika içinde tekrar sorgulanmaz |
| 🔒 **API Şifreleme** | API anahtarları AES-GCM ile şifreli saklanır |
| 🛡️ **Gizlilik** | %100 yerel — verileriniz hiçbir sunucuya gitmez |
| 🧠 **Memory Safe** | Render 512MB RAM limiti için optimize edilmiş düşük thread (max 4) kullanımı ve aktif GC |
| 🐳 **Docker** | `docker compose up` ile tek komutla çalıştırma |

### 🧩 Modüler Mimari (Puzzle Modeli)

Her dosya tek bir sorumluluğa sahiptir. Birbirinden bağımsız geliştirilebilir:

```
src/
├── api/
│   ├── main.py              → FastAPI API katmanı + export/autocomplete
│   ├── config.py            → Uygulama ayarları & API anahtarları
│   └── rate_limiter.py      → Retry & limit yönetimi
├── core/
│   ├── analysis_engine.py   → Orkestratör (paralel + cache + teknik göstergeler + sektör)
│   ├── optimization_engine.py → Portföy optimizasyonu (MPT)
│   ├── ai_agent.py          → Gemini AI yorum üretimi
# 🚀 AI Destekli Portföy Analiz Platformu (v4.0)

Hisselerinizi ve yatırım fonlarınızı (ABD & Türkiye) saniyeler içinde analiz eden, yapay zeka destekli ve kullanıcı dostu bir yatırım platformu.

## ✨ Öne Çıkan Özellikler

*   **🔍 Akıllı Ticker Algılama:** ABD (NYSE/NASDAQ) ve Türkiye (BIST/TEFAS) sembollerini otomatik tanır.
*   **🤖 AI Portföy Sihirbazı:** Sadece ne tür bir portföy istediğinizi yazın (örn: "Yüksek temettülü 5 BIST hissesi"), AI sizin için tasarlasın.
*   **📊 İnteraktif Finansal Metrikler:** P/E, P/B, Beta gibi metriklere tıklayarak AI'dan o hisseye özel derinlemesine analiz alın.
*   **⚡ Hızlı Autocomplete:** Sadece 1-2 harf yazarak binlerce sembol arasından doğru olanı bulun.
*   **🛡️ Stres Testleri:** 2008 Krizi, Pandemi veya Teknoloji Çöküşü gibi senaryolarda portföyünüzün nasıl etkileneceğini görün.
*   **📈 Monte Carlo Simülasyonu:** Portföyünüzün 1 yıllık gelecekteki olası getiri dağılımını bilimsel yöntemlerle tahmin edin.
*   **☪️ İslami Uygunluk (Opsiyonel):** Katılım Finansı ilkelerine göre otomatik tarama ve arındırma oranları.
*   **📄 Çoklu Dışa Aktarma:** Analiz sonuçlarını **Excel**, **PDF** veya **Word** formatında indirin.

## 🛠️ Kurulum ve Çalıştırma

### 1. Gereksinimler
*   Python 3.10+
*   Google Gemini API Key (AI yorumları için)

### 2. Yerelde Çalıştırma
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

## 📂 Proje Yapısı

*   `src/api/`: FastAPI endpointleri ve API mantığı.
*   `src/core/`: Analiz orkestratörü ve Monte Carlo motoru.
*   `src/analyzers/`: BIST ve US pazar analiz araçları.
*   `src/frontend/`: Glassmorphism tasarımlı, i18n destekli modern arayüz.
*   `src/utils/`: Dosya işleme ve dışa aktarma araçları.

## 🔒 Güvenlik Notu
API anahtarlarınız asla sunucuya kaydedilmez, tarayıcınızın yerel depolamasında (localStorage) AES-GCM ile şifrelenmiş olarak tutulur.

## 📄 Lisans
Bu proje MIT lisansı ile lisanslanmıştır. Kullanım sorumluluğu tamamen kullanıcıya aittir. Yatırım tavsiyesi değildir.

### ☁️ Canlı Ortamda Yayınlama (Vercel + Render Çift Mimari)

Bu proje, alan adınızı kullanabilmeniz ve TEFAS sunucularının ağır "Cloudflare" bot engellerini aşabilmeniz için **Çift Sunucu (Monorepo) Mimarisi** kullanır. 

#### 1. Backend'i Render.com'a Yükleme (Veri Motoru)
*   **render.com** adresine gidip GitHub'ınızla giriş yapın.
*   "New" > "Web Service" seçeneğini tıklayın.
*   Bu deponuzu seçin.
*   **Root Directory:** Boş bırakın.
*   **Build Command:** `pip install -r requirements.txt`
*   **Start Command:** `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
*   "Create Web Service" butonuna basın. Render size bir URL verecektir (örn: `https://projeniz.onrender.com`).

#### 2. Frontend'i Vercel'e Yükleme (Hızlı Arayüz)
*   `src/frontend/js/utils.js` dosyasındaki `API_BASE` değişkenini Render'dan aldığınız URL ile güncelleyin.
*   Vercel'e gidin ve projeyi import edin.
*   Vercel otomatik olarak `src/frontend` dizinini algılayacak ve yayına alacaktır.

---
Geliştirici: [Eren Tahiroğlu](https://github.com/ErenTahiroglu)
*   **Blueprint:** Otomatik olarak depodaki `render.yaml` dosyasını bulacak ve tüm Python kurulumlarını sizin yerinize şipşak halledecektir. 
*   Bittiğinde size bir API linki verecek (Örn: `https://ai-portfolio-assistant.onrender.com`).

#### 2. Frontend'i Vercel'e Yükleme (Kullanıcı Arayüzü)
Vercel, kullanıcılarınızın sitenize ışık hızında erişmesini sağlayacak ve alan adınızı bağlayacağınız vitrindir.
*   İlk aşamadan aldığınız Render API adresini, bu klasördeki `vercel.json` dosyası içindeki `destination` kısmına (`https://RENDER_API_LINKINIZ/api/$1` şeklinde) yapıştırın ve değişiklikleri GitHub'a yollayın.
*   **vercel.com** adresinde "Add New Project" deyip bu repoyu seçin ve hiçbir ayara dokunmadan "Deploy" tuşuna basın.
*   Vercel otomatik olarak HTML arayüzünüzü kuracak ve "Analiz Et" butonuna basıldığında bu yükü gizlice kendi kurduğunuz Render Python sunucunuza aktaracaktır!

### 📦 Bağımlılıklar

| Paket | Amaç |
|-------|------|
| `fastapi` + `uvicorn` | API sunucusu |
| `yfinance` + `yahooquery` | Fiyat, bilanço ve değerleme verileri |
| `pandas` + `numpy` | Veri analizi |
| `requests` + `rate_limiter` | TEFAS WAF bypass & Chunked Fetching |
| `langchain-google-genai` | Gemini AI entegrasyonu |
| `python-docx` + `fpdf2` + `openpyxl` | Rapor dışa aktarımı |

---

## English

**Portfolio Analysis Platform** is a locally-hosted, AI-powered web application for analyzing US stocks, Borsa Istanbul (BIST) equities, and TEFAS mutual funds simultaneously.

It calculates financial metrics (returns, inflation adjustments, dividends, Sharpe Ratio, Max Drawdown, P/E, P/B, Beta), optionally audits AAOIFI Islamic compliance, and generates AI commentary via Google Gemini.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🌍 **Multi-Market** | Mix US, BIST and TEFAS tickers — market is **auto-detected** |
| 📊 **Valuation Metrics** | P/E, P/B, Beta, Market Cap, EPS, ROE, Dividend Yield, 52w range |
| 📈 **Real Returns** | Inflation-adjusted returns using US/TR CPI data from FRED |
| 🎯 **Risk Analysis** | Sharpe Ratio, Max Drawdown, yearly/monthly return breakdowns |
| 🔍 **Interactive Metrics** | Click on financial ratios for static definitions and **AI-powered custom insights** |
| 🧪 **Premium Stress Tests** | Tech Crash, 2008 Crash, Covid-19 simulations with modern **Market Shock Gauge** |
| 🏦 **Dividend FI/RE** | Calculate time to reach target passive income with monthly contributions |
| 🛡️ **TEFAS Fetching** | Reliable mutual fund data retrieval using custom `curl_cffi` scraper with WAF bypass |
| ⚖️ **Optimization** | Markowitz Efficient Frontier optimization for Maximum Sharpe ratio weights |
| 🪄 **AI Wizard** | Create tailored portfolios instantly from natural language prompts |
| 📰 **Dynamic News** | AI-filtered impactful market news with Sentiment Analysis (Bullish/Bearish) |
| 🤖 **AI Commentary** | Professional fund-manager style analysis via Gemini 2.5 Flash |
| 📈 **Interactive Charts** | Chart.js bar charts, Heatmaps (Treemaps), correlations and Monte Carlo graphs |
| 🔍 **Autocomplete** | Suggestions for 60+ popular US & BIST tickers |
| 🧠 **Modular Architecture** | Frontend decoupled into `utils.js`, `api.js`, `charts.js` for "puzzle-like" clean extensibility |
| 📋 **Watchlist** | Save frequently-used portfolios (localStorage) |
| 📊 **Comparison** | Side-by-side metric comparison table |
| 📥 **Export** | Download reports as Excel, PDF, or Word |
| ☪️ **Islamic Analysis** | Optional AAOIFI compliance scan (off by default) |
| ⚡ **Parallel Analysis** | ThreadPoolExecutor for 3-5x speed boost |
| 💾 **Smart Cache** | 5-minute TTL prevents redundant API calls |
| 🛡️ **Privacy** | 100% local — your data never leaves your machine |

### 🧩 Modular Architecture (Puzzle Model)

Each file has a single responsibility and can be developed independently:

```
src/
├── api/                 → FastAPI Layer
├── core/                → Analysis & AI Engines
├── analyzers/           → Market-specific Analyzers
├── data/                → Data Sources & Scrapers
├── utils/                → File Processing Utilities
├── desktop_app.py       → Desktop Launcher (Entry Point)
└── frontend/            → Web UI
```

### 🚀 How to Run

Easiest way: download the project and double-click!

- **Windows:** `baslat_windows.bat`
- **Mac/Linux:** `baslat_mac_linux.command`

> **🤖 Python not installed?** No problem! The launcher scripts auto-detect and install Python if it's missing. On Windows via `winget` or Python.org silent installer, on Mac via Homebrew, on Linux via apt/dnf/pacman.

For manual setup:
```bash
git clone https://github.com/ErenTahiroglu/AI-Portfoy-Yoneticisi.git
cd AI-Portfoy-Yoneticisi
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python src/desktop_app.py
```

### 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | API server |
| `yfinance` + `yahooquery` | Price, balance sheet & valuation data |
| `pandas` + `numpy` | Data analysis |
| `requests` + `rate_limiter` | TEFAS WAF bypass & Chunked Fetching |
| `langchain-google-genai` | Gemini AI integration |
| `python-docx` + `fpdf2` + `openpyxl` | Report export |

---

---
*Not: Render.com Free Tier (512MB RAM) limiti için uygulama eşzamanlı analiz sayısını 2 ticker ile sınırlandıracak şekilde optimize edilmiştir.*

*Disclaimer: This software is for informational and educational purposes only. It does not constitute financial or investment advice. Always verify AI-generated analyses with your own research.*

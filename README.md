<div align="center">
  
# 🤖 AI İslami Portföy Yöneticisi & Analiz Aracı
### (AI Islamic Portfolio Manager & Analyzer)

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Gemini AI](https://img.shields.io/badge/Google_Gemini-AI-orange.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## Türkçe (Turkish)

**AI İslami Portföy Yöneticisi**, ABD hisseleri, Borsa İstanbul (BIST) hisseleri ve TEFAS fonlarını aynı anda analiz edebilen, yapay zeka destekli yerel bir masaüstü uygulamasıdır. 

Finansal verileri (getiri, enflasyon, temettü, risk metrikleri) hesaplar, **AAOIFI İslami finans (Katılım) standartlarını** denetler ve sonuçları Google Gemini AI modeli ile otonom olarak yorumlar. Tek bir arayüzden tüm portföyünüzün röntgenini çekmenizi sağlar.

### ✨ Temel Özellikler
* 🌍 **Çoklu Piyasa Desteği:** Aynı giriş kutucuğuna hem BIST (`THYAO`, `AKBNK`), hem ABD (`AAPL`, `TSLA`), hem de TEFAS fonlarınızı (`TP2`, `ZP8`) karışık yazabilirsiniz. Sistem piyasayı **otomatik tespit eder**.
* ☪️ **İslami Uygunluk (AAOIFI) Analizi:** Şirket bilançosunu inceleyerek *Faiz Geliri (<\%5)* ve *Borçluluk Oranı (<\%30)* sınırlarını denetler (\"Katılım Endeksi\" standartları).
* 📈 **Reel Getiri Hesaplama:** ABD hisseleri için ABD (\$), BIST/TEFAS için Türkiye (₺) enflasyon verilerini (FRED) çekerek, getirinizi enflasyondan arındırır.
* 🎯 **Sharpe Ratio & Max Drawdown:** Her hisse/fon için risk-getiri oranı ve en büyük düşüş yüzdesi hesaplanır.
* 🤖 **Otonom Yapay Zeka Yorumu:** Ham veriyi boğucu olmaktan çıkarır; Gemini 2.5 Flash modeli ile size profesyonel bir fon yöneticisi gibi finansal metin / uyarılar yazar.
* 🛡️ **Güvenlik (Yerel Çalışma):** Kendi API anahtarınızı (Gemini & Alpha Vantage) kullanırsınız. Verileriniz hiçbir bulut sunucusuna gitmez, %100 kendi bilgisayarınızda (localhost) çalışır.
* 📂 **Toplu Excel Girdisi:** Hisse sembollerinizi tek tek yazmak yerine doğrudan Excel portföyünüzü sürükle-bırak ile yükleyebilirsiniz.
* ⚡ **Paralel Veri Çekme:** Yahoo Finance, Stooq ve Alpha Vantage kaynakları eşzamanlı olarak sorgulanır (3x hız artışı).
* 🌐 **TEFAS WAF Bypass:** Playwright sanal tarayıcı ile TEFAS'ın F5 güvenlik duvarını aşarak fon verilerini çeker.
* 🚀 **PyInstaller Bağımsız (Çapraz Platform):** `.exe` hantallığından arındırılmış, hafifletilmiş başlatıcıları (Launcher) ile Windows, Mac veya Linux'ta tek tıklamayla anında çalışır.

### 🧩 Modüler Mimari (Puzzle Modeli)

Uygulamanın arka planı tamamen modüler bir "yap-boz" mimarisine sahiptir. Her dosya tek bir sorumluluğa odaklanır:

```
src/
├── main.py              → FastAPI HTTP katmanı (endpoint'ler)
├── analysis_engine.py   → Orkestratör (tüm parçaları yönetir)
├── market_detector.py   → Pazar algılama (US / TR / TEFAS)
├── base_analyzer.py     → Ortak hesaplama mantığı (DRY)
├── bist_analyzer.py     → BIST & TEFAS analizi (TR pazar)
├── portfolio_analyzer.py→ ABD hisse analizi (US pazar)
├── tefas_scraper.py     → Playwright TEFAS WAF bypass
├── islamic_analyzer.py  → AAOIFI İslami uygunluk denetimi
├── ai_agent.py          → Gemini AI yorum üretimi
├── data_sources.py      → SSL bypass, logging, sabitler
├── file_processor.py    → Excel/DOCX/PDF okuma & yazma
├── desktop_app.py       → Masaüstü başlatıcı
└── frontend/            → HTML/CSS/JS arayüz
```

### 🚀 Nasıl Çalıştırılır (Kurulum)
Uygulamayı kullanmak için bilgisayarınızda **Python 3.10 veya üzeri** yüklü olmalıdır. *(Önemli: Python'u kurarken en alttaki **"Add Python to PATH"** kutucuğunu işaretlemeyi unutmayın!)*

1. Projeyi bilgisayarınıza indirin (ZIP veya Git Clone).
2. Proje klasörüne girin ve sisteminize uygun olan dosyaya çift tıklayın:
   * **Windows kullanıcıları:** `baslat_windows.bat` dosyasına tıklayın.
   * **Mac / Linux kullanıcıları:** `baslat_mac_linux.command` dosyasını çalıştırın.
3. Kütüphaneler otomatik kurulacak, Playwright tarayıcısı indirilecek, sunucu başlayacak ve tarayıcınızda arayüz otomatik olarak açılacaktır.

### 📦 Bağımlılıklar
| Paket | Amaç |
|-------|------|
| `fastapi` + `uvicorn` | API sunucusu |
| `yfinance` + `pandas_datareader` | Fiyat ve enflasyon verileri |
| `playwright` + `nest_asyncio` | TEFAS WAF bypass (sanal tarayıcı) |
| `langchain-google-genai` | Gemini AI entegrasyonu |
| `curl_cffi` | SSL bypass & Chrome impersonate |
| `pandas` + `numpy` | Veri analizi |
| `python-docx` + `fpdf2` | Rapor dışa aktarımı |

---

## English

**AI Islamic Portfolio Manager** is a locally-hosted, AI-powered desktop application capable of simultaneously analyzing US stocks, Borsa Istanbul (BIST) equities, and TEFAS mutual funds. 

It calculates financial metrics (returns, inflation adjustments, dividends, Sharpe Ratio, Max Drawdown), audits **AAOIFI Islamic finance compliance**, and autonomously interprets the results using the Google Gemini AI model. It allows you to X-ray your entire portfolio from a single, unified interface.

### ✨ Key Features
* 🌍 **Multi-Market Support:** You can enter a mix of BIST (`THYAO`, `AKBNK`), US stocks (`AAPL`, `TSLA`), and TEFAS funds (`TP2`, `ZP8`) into the main input field. The system **auto-detects** the market.
* ☪️ **Islamic Compliance (AAOIFI) Analysis:** Audits company balance sheets against *Interest Income (<5%)* and *Debt Ratio (<30%)* thresholds ("Participation Index" standards).
* 📈 **Real Return Calculation:** Pulls US (\$) or Turkey (₺) inflation data (via FRED) based on the asset's market to strip inflation from your raw historical returns.
* 🎯 **Sharpe Ratio & Max Drawdown:** Risk-adjusted return ratio and maximum drawdown percentage calculated for every asset.
* 🤖 **Autonomous AI Commentary:** Turns raw data into actionable insights; the Gemini 2.5 Flash model writes professional fund-manager style financial text and warnings for you.
* 🛡️ **Privacy First (Local Execution):** Bring your own API keys (Gemini & Alpha Vantage). Your portfolio data never goes to a third-party cloud server; it runs 100% locally on your machine (localhost).
* 📂 **Batch Excel Upload:** Instead of typing ticker symbols manually, drag-and-drop your Excel portfolio file directly into the app.
* ⚡ **Parallel Data Fetching:** Yahoo Finance, Stooq, and Alpha Vantage are queried concurrently (3x speed boost).
* 🌐 **TEFAS WAF Bypass:** Uses Playwright headless browser to bypass the F5 web application firewall and scrape TEFAS fund data.
* 🚀 **Cross-Platform Launchers:** Freed from clunky `.exe` standalone builds; uses lightweight launcher scripts to boot instantly on Windows, Mac, or Linux with a single click.

### 🧩 Modular Architecture (Puzzle Model)

The backend features a fully modular "puzzle-piece" architecture where each file has a single responsibility:

```
src/
├── main.py              → FastAPI HTTP layer (endpoints)
├── analysis_engine.py   → Orchestrator (manages all pieces)
├── market_detector.py   → Market detection (US / TR / TEFAS)
├── base_analyzer.py     → Shared calculation logic (DRY)
├── bist_analyzer.py     → BIST & TEFAS analysis (TR market)
├── portfolio_analyzer.py→ US stock analysis (US market)
├── tefas_scraper.py     → Playwright TEFAS WAF bypass
├── islamic_analyzer.py  → AAOIFI Islamic compliance audit
├── ai_agent.py          → Gemini AI commentary generation
├── data_sources.py      → SSL bypass, logging, constants
├── file_processor.py    → Excel/DOCX/PDF read & write
├── desktop_app.py       → Desktop launcher
└── frontend/            → HTML/CSS/JS interface
```

### 🚀 How to Run (Installation)
The only requirement is having **Python 3.10 or higher** installed on your machine. *(Important: Make sure to check the **"Add Python to PATH"** box during installation!)*

1. Download the project (via ZIP or Git Clone).
2. Open the project folder and double-click the launcher for your Operating System:
   * **Windows users:** Double-click on `baslat_windows.bat`.
   * **Mac / Linux users:** Run `baslat_mac_linux.command` (or manually run the bash script).
3. Dependencies will auto-install, the Playwright browser will be downloaded, the local server will boot, and your browser will automatically open the UI.

### 📦 Dependencies
| Package | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | API server |
| `yfinance` + `pandas_datareader` | Price and inflation data |
| `playwright` + `nest_asyncio` | TEFAS WAF bypass (headless browser) |
| `langchain-google-genai` | Gemini AI integration |
| `curl_cffi` | SSL bypass & Chrome impersonate |
| `pandas` + `numpy` | Data analysis |
| `python-docx` + `fpdf2` | Report export |

---
*Disclaimer: This software is for informational and educational purposes only. It does not constitute financial or investment advice. Always verify AI-generated analyses with your own research.*

# AI Portföy Yöneticisi 🚀

Modern, esnek ve yüksek performanslı otonom portföy analiz ve yönetim platformu. Sıradan bir hisse senedi takip uygulamasının ötesinde; Offline-First PWA yeteneklerine, sıfır gecikmeli (Zero-Latency) arayüze ve Web Worker tabanlı asenkron matematik motoruna sahip endüstri standardında bir mühendislik harikasıdır.

![Tests](https://img.shields.io/badge/Tests-Passing_25/25-brightgreen.svg)
![Coverage](https://img.shields.io/badge/Coverage-98%25-brightgreen.svg)
![Architecture](https://img.shields.io/badge/Architecture-ESM_&_Web_Workers-blue.svg)
![License](https://img.shields.io/badge/License-MIT-purple.svg)

---

## 🌟 Vizyon ve Mimari

Bu proje, bulut bilişim sınırlarında (Free-Tier, 512MB RAM vb.) bile **%100 kesintisiz ve hatasız** çalışabilmek üzere tasarlanmıştır.

### 🛡️ Üst Düzey Mimari Özellikler

- **Offline-First PWA & Zero-Latency SWR (Stale-While-Revalidate):**
  Uygulama açılır açılmaz IndexedDB üzerinden en son veriyi anında hidratlar (hydration). Kullanıcı saniyenin onda biri süresinde arayüzü görürken, arka planda canlı veriler sessizce güncellenir ve non-blocking bir şekilde senkronize edilir.

- **Web Worker `MathEngine`:**
  Ağır Sharpe Oranı, Beta ve Volatilite hesaplamaları ana UI iş parçacığını (Main Thread) tıkamaması için Web Worker'lara devredilir. Veriler `Float64Array` ve `ArrayBuffer` aracılığıyla zero-copy (kopyalamasız) olarak aktarılır.

- **Dirençli Ağ Katmanı (Resilient Network):**
  `HttpClient.js` exponential backoff (üstel geri çekilme) stratejisiyle çalışır. Geçici ağ kopmalarında otomatik yeniden denemeler yapar.

- **Redis Tabanlı Idempotency:**
  Kullanıcı veya ağ kaynaklı *Retry Storm* (yeniden deneme fırtınası) sorunlarını önlemek için, her request body'sinden bir hash (`Idempotency-Key`) oluşturulur. FastAPI katmanındaki `IdempotencyMiddleware`, duplicate istekleri Redis kilidi (lock) ile tespit eder ve 409 Conflict döndürerek backend'in gereksiz yere yorulmasını engeller.

- **Memory-Safe Backend:**
  Python tarafında Explicit GC (Garbage Collection), yfinance önbellek temizliği ve rate-limiting ile 512MB RAM sınırlarında OOM (Out Of Memory) hataları kesin olarak engellenir.

---

## 🏗️ Gelişim Süreci (Aşama 1 - 12)

Projenin modernizasyonu 12 aşamalı devasa bir mimari evrimle gerçekleşmiştir:

| Aşama | Odak Noktası | Detaylar |
| :--- | :--- | :--- |
| **1-3** | **Modüler ESM & Core** | Spagetti JS kodları saf ve native ES Module (ESM) yapısına geçirildi. Web Worker `MathEngine` entegre edildi. |
| **4** | **State Management** | Global değişkenler yerine Proxy tabanlı Pub/Sub State Manager (`core/state.js`) kuruldu. DOM güncellemeleri reaktif hale getirildi. |
| **5** | **Test & QA** | Vitest ile Unit/Integration testleri (JSDOM, MSW) yazıldı. `MathEngine` ve `HttpClient` test coverage oranı %98'e çıkarıldı. |
| **6** | **Free-Tier Hardening** | Backend'e Redis Rate Limiter ve Explicit GC eklenerek Render/Railway üzerindeki OOM Kill sorunları çözüldü. |
| **7-8** | **Security & Deployment** | Vercel Cache-Control Header'ları, Strict CORS politikaları ve Load Balancer IP Extraction mekanizmaları (X-Forwarded-For) devreye alındı. |
| **9** | **SWR & Zero-Latency UX** | Açılış sürelerini sıfıra indiren SWR mimarisi uygulandı. Veriler IndexedDB'ye kaydedildi ve Layout Shift problemleri çözüldü. |
| **10** | **Idempotency** | Retry fırtınalarına karşı `IdempotencyMiddleware` ve payload-hash tabanlı benzersiz anahtarlama sistemi eklendi. |
| **11** | **UI/UX & PWA Zırhı** | Mobil ekran taşmaları önlendi, PWA Pull-to-Refresh hataları giderildi ve tüm bileşenlere Empty State (Boş Durum) tasarımları eklendi. |
| **12** | **Bug Hunt & Stabilization** | Son stabilizasyon turu yapıldı, DOM null referansları önlendi, sessiz hatalar temizlendi ve dokümantasyon tamamlandı. |
| **13** | **Multi-Agent LangGraph** | CIO Orchestrator ve çoklu ajan yapısı entegre edildi. |
| **14** | **Async & UI Final Polish** | `pytest-asyncio` entegrasyonu tamamlandı, UI üzerindeki Unicode escape hataları ve HttpClient asenkron problemleri çözüldü. |
| **15** | **Performans Optimizasyonu** | Kripto veri işleme süreçleri ve genel sistem performansı optimize edildi. |
| **16** | **Otonom Portföy Rebalans** | Risk yönetimi ve otonom portföy optimizasyon algoritmaları eklendi. |
| **17** | **Institutional Hardening** | Ruff linter temizliği, PEP8 uyumu ve backend mimari stabilizasyonu tamamlandı. |

---

## 🏗️ Mimari ve Kalite Standartları

Bu proje, sadece çalışan bir kod değil, aynı zamanda **sürdürülebilir ve kurumsal** bir mühendislik ürünüdür:

- **Ruff Cleanup (Institutional-Grade):** Tüm backend kod tabanı, modern Python ekosisteminin en hızlı linter'ı olan Ruff ile taranmış; tanımlanmamış değişkenler, hatalı formatlar ve potansiyel güvenlik açıkları (Wave 2) temizlenmiştir.
- **Zero-Trust Sentinel:** GitHub Actions üzerinde çalışan otonom sağlık kontrolleri ve güvenlik tarayıcıları (TruffleHog) ile API anahtarı sızıntıları ve sistem çökmeleri anında tespit edilir.
- **Shadow Test Architecture:** Canlı ortamda (Production) LLM analizlerini test etmek için `X-Shadow-Test` header'ı kullanılarak veritabanı kirliliği önlenir.

---

## 🛠️ Teknoloji Yığını

### Frontend
- **Vanilla JavaScript (ESM)** (Framework-Agnostic, Zero Dependencies)
- **Web Workers** & `ArrayBuffer`
- **IndexedDB** & SWR Pattern
- **PWA (Progressive Web App)**
- **CSS3 Variables & Flexbox/Grid**
- **Vitest & JSDOM** (Testing)

### Backend
- **Python 3.10+ & FastAPI**
- **Redis** (Rate Limiting, Idempotency Locks)
- **yfinance** (Canlı Piyasa Verileri)
- **Supabase / PostgreSQL** (Kimlik Doğrulama & DB)
- **OpenAI / Gemini** (Yapay Zeka Copilot & Analiz)

---

## 🚀 Hızlı Başlangıç

Sistemi ayağa kaldırmak için iki farklı yöntem tercih edebilirsiniz: Docker ile tam izole kurulum veya yerel cihazınızda manuel kurulum.

### Seçenek 1: Docker ile Kurulum (Önerilen)
Sistemde Docker kuruluysa tek bir komutla hem backend, hem frontend, hem de Redis önbelleğini ayağa kaldırabilirsiniz.
```bash
# Repo'yu klonlayın ve kök dizine gidin
# Çevresel değişken örneğini kopyalayın ve içini doldurun
cp .env.example .env

# Container'ları arka planda inşa edip çalıştırın
docker-compose up --build -d
```
Sistem ayağa kalktıktan sonra tarayıcınızdan `http://localhost:3000` adresine giderek arayüze ulaşabilirsiniz.

### Seçenek 2: Manuel (Local) Kurulum

#### 1. Backend Kurulumu (Python & FastAPI)
```bash
# Geliştirme ortamı oluşturun ve aktifleştirin
python -m venv venv
source venv/bin/activate  # Windows için: venv\Scripts\activate

# Backend bağımlılıklarını kurun
pip install -r backend/requirements.txt

# Çevresel değişkenleri hazırlayın
cp .env.example .env

# Sunucuyu başlatın
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend Kurulumu (Vanilla JS / Web Server)
Uygulamanın ön yüzü saf HTML, CSS ve Vanilla JS'den oluştuğu için karmaşık bir build sürecine ihtiyaç duymaz. Doğrudan bir basit HTTP sunucusu ile ayağa kalkar.
```bash
# Yeni bir terminal açın ve uygulamanın kök dizininde çalıştırın:
python -m http.server 3000
```
Tarayıcınızdan `http://localhost:3000/frontend/` adresine giderek sistemi kullanmaya başlayabilirsiniz.

### Testleri Çalıştırma
```bash
# Finansal Bütünlük, Hesaplama Metrikleri ve Kayan Nokta Testleri:
source venv/bin/activate
pytest backend/tests/test_financial_integrity.py backend/tests/test_decimal_precision_v3.py
```

---

## 🛡️ Güvenlik ve Katkı
Tüm API uç noktaları Rate Limiter ve Idempotency Middleware ile korunmaktadır. Projeye katkıda bulunurken lütfen `ESM` mimarisini bozmamaya ve testleri (`npx vitest run`) geçecek şekilde PR göndermeye özen gösterin.

**Lisans:** MIT
\n* **Sponsorluk:** Katkıda bulunmak için [GitHub Sponsor](https://github.com/sponsors/ErenTahiroglu) sayfasını ziyaret edebilirsiniz.  

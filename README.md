# 📈 AI-Portföy-Yöneticisi (AI Portfolio Manager)

## Yapay Zeka Destekli, Kurumsal Standartlarda Akıllı Portföy Analiz ve Risk Yönetimi Platformu

[![Vercel](https://img.shields.io/badge/Frontend-Vercel-blue?style=flat-square&logo=vercel)](https://vercel.com)
[![Render](https://img.shields.io/badge/Backend-Render-black?style=flat-square&logo=render)](https://render.com)
[![Supabase](https://img.shields.io/badge/Database-Supabase-green?style=flat-square&logo=supabase)](https://supabase.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-teal?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)

---

## 📖 Genel Bakış

AI-Portföy-Yöneticisi; yatırımcıların hisse senedi, fon ve kripto varlıklarını **Gemini / Groq (Yapay Zeka)** motorlarıyla saniyeler içinde analiz eden, optimize eden ve risk süzgecinden geçiren modern bir web uygulamasıdır. Geleneksel analizlerin aksine, canlı veri akışları ve çoklu-ajan asistan (CIO Orchestrator) mimarisiyle yatırımcıya harekete geçebileceği net tavsiyeler üretir.

---

## 🔥 Öne Çıkan Özellikler (Features)

### 🤖 1. Yapay Zeka & Analiz

* **Chief Investment Officer (CIO) Ajanı:** Analist ve Researcher modellerinden gelen verileri sentezleyen orkestratör asistan.
* **Hisse & Fon Raporlama:** VaR (Value at Risk), Beta ve Maximum Drawdown gibi modern risk metrikleri.
* **Makro Analiz Generator:** Tüm portföyün korelasyonlarını ve dengeleme ihtiyaçlarını streaming (akan) metin olarak sunar.
* **Puzzle Early Exit:** Sadece İslami uygunluk arayan kullanıcılar için gereksiz LLM çağrılarını kesen maliyet optimizasyonu.

### 🎨 2. Kullanıcı Deneyimi (UX) & Onboarding

* **Akıllı Karşılama Sihirbazı (Onboarding Wizard):** "Sıfırıncı Seviye" kullanıcılar için 3 adımlı, jargonsuz ve card-based bir yatırım profili oluşturma akışı.
* **Kişiselleştirilmiş AI Yanıtları:** Sihirbazda toplanan veriler otomatik olarak AI sistem prompt'una enjekte edilir.
* **Modern Landing Page (UX Refined):** Scroll-based navigasyon, akıllı "Uygulamaya Git" butonu ve otomatik dashboard atlamayı önleyen kontrollü geçişler.
* **İzole Yönetici Modu (Admin Isolation):** Geliştirici erişimi (Bypass) gerçek kullanıcı oturumlarından ayrıştırıldı; oturum varken kimlik değişimi engellendi.

### 🛡️ 3. Güvenlik ve Kurumsal Kalkanlar (SRE Essentials)

* **Görünmez Duvar (Invisible Wall):** Yeni başlayan kullanıcılar durumuna göre riskli varlıklardan otomatik filtrelenir.
* **Davranışsal Fren (Behavioral Brake):** AI asistanı, yeni başlayanların FUD/FOMO durumlarını durdurur ve rasyonel sorgulama yapar.
* **📊 Telemetry Pipeline:** Tüm güvenlik müdahaleleri Supabase `user_events` tablosunda loglanır.
* **Zero-Trust CI:** `pytest-socket` kalkanı ile test sırasında dış dünya ile tüm ağ trafiği bloklanır (Sızıntı koruması).
* **Performance Gates:** Analiz süreleri 20s sınırında (Vercel/Render limitleri) otomatik monitor edilir.
* **Safe-Fail LLM Mocking:** API anahtarı yokken bile framework kabiliyetleri mock-LLM ile test edilebilir.
* **Prompt Isolation:** Dışarıdan akan haberler XML etiketleri ile hapsedilir.
* **Idempotency:** Mükerrer emir basımları prevent edilir.

---

## 📝 Son Değişiklikler (Changelog)

* **v2.0.0 (Current): The Great Architectural Refactor.** 
  * **Frontend Modernization:** Tamamen Vanilla JS ES Modules (ESM) yapısına geçildi. Pub/Sub tabanlı reaktif state yönetimi (Proxy) entegre edildi.
  * **Zero-Copy Web Worker:** Monte Carlo ve Korelasyon hesaplamaları `MathEngine.js` ile ana iş parçacığından ayrıldı, `Float64Array` kullanılarak bellek verimliliği sağlandı.
  * **Resilient Network:** Exponential Backoff destekli `HttpClient` wrapper yazıldı.
  * **Test Driven:** `Vitest` kurularak çekirdek fonksiyonlar için %100 test kapsama oranı sağlandı (25+ test).
  * **Backend Observability:** Tüm isteklerde `X-Correlation-ID` takibi, Contextual Logging ve global hata şeması entegre edildi.
* **v1.1.3: Hardening & Stability.** Finalized modular architecture, resolved frontend linting warnings, and synchronized production configuration files across Render, Vercel, and Docker.
* **v1.1.2: Hybrid Redis & Persistence.** Added standard TCP Redis support for local Docker compatibility. Completed Supabase SQL schema with missing telemetry and portfolio tables.
* **v1.1.1: Market Search & Stability.** Extended search filters for US exchanges (NYSE, NASDAQ, AMEX). Fixed innerHTML crashes during analysis.

---

## 🏗️ Mimari Yapı (Puzzle Framework)

Proje, **Monorepo** yapısında olup hem backend hem frontend tarafında modüler **Puzzle** mimarisini kullanır:

### 🧩 Backend (FastAPI)

* **`/backend/nodes/`**: AI Ajanları ve veri toplama düğümleri.
* **`/backend/engine/`**: LangGraph iş akışları, State yönetimi ve Optimizasyon motoru.
* **`/backend/infrastructure/`**: Auth, LLM Factory, Redis Cache, Scheduler ve Limiter gibi temel yapı taşları.
* **`/backend/services/`**: `ChatOrchestrator` gibi üst düzey iş mantığı sarmalları.
* **`/backend/api/`**: FastAPI Router'lar, Global Exception Handlers ve Correlation ID Middleware katmanı.

### 🎨 Frontend (Vanilla JS & ESM)

* **`/frontend/js/core/`**: Reaktif durum yönetimi (`state.js`) ve Yüksek performanslı matematik motoru (`MathEngine.js`).
* **`/frontend/js/network/`**: Dirençli `HttpClient` ve Supabase entegrasyonu.
* **`/frontend/js/worker.js`**: Zero-copy (ArrayBuffer) veri transferi ile asenkron simülasyon hesaplamaları.
* **`/frontend/js/components/`**: Olay tabanlı, modüler Web Bileşenleri.

### 🛠️ Tooling & DevOps

* **`tests/`**: Pytest (Backend) ve Vitest (Frontend Unit & Integration) tabanlı otonom testler.
* **`migrations/`**: Alembic ile versiyonlanmış veritabanı şeması.
* **`brand_assets/`**: Kurumsal görsel kimlik kalkanı.

---

## 🚀 Başlangıç & Kurulum (Lokal)

Sistemi bilgisayarınızda ayağa kaldırmak için aşağıdaki adımları izleyin:

### 1. Dosya Hazırlığı (.env)

Kök dizindeki şablonu kopyalayarak `.env` dosyanızı oluşturun ve anahtarları doldurun:

```bash
cp .env.example .env
```

> **Gerekli Temel Anahtarlar:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `GEMINI_API_KEY`, `UPSTASH_REDIS_REST_URL`.

### 2. Docker İle Hızlı Kurulum

Tüm platformu tek satır kodla ayağa kaldırabilirsiniz:

```bash
docker-compose up --build
```

* **API Gateway (Backend):** `http://localhost:8000`
* **Statik UI Dağılımı (Frontend):** Vercel üzerinden veya lokal server (`http://localhost:3000`) ile.

---

## 🧪 Otonom UI/UX Testleri

Arayüzün görsel bütünlüğünü otomatik test etmek ve ekran görüntüleri almak için Puppeteer kullanılmaktadır:

```bash
# 1. Node Bağımlılıklarını Kurun (Kök dizinde)
npm install

# 2. Otonom Ekran Görüntüsü Botunu Çalıştırın
npm run test:ui
```

*Görsel çıktılar `tests/ui/screenshots/` klasörüne kaydedilir.*

---

## 🤝 İletişim & Destek

* **Sponsorluk:** Katkıda bulunmak için [GitHub Sponsor](https://github.com/sponsors/ErenTahiroglu) sayfasını ziyaret edebilirsiniz.

Saygılarımızla.

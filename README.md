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

* **v11.0 (Current):** **Puzzle Framework Release.** Tamamen modüler, ölçeklenebilir ve SRP (Single Responsibility) uyumlu yeni mimari geçişi tamamlandı. Backend (`nodes/`, `engine/`, `infrastructure/`, `services/`) ve Frontend (`core/`, `network/`, `components/`) dizinleri normalize edildi. `ChatOrchestrator` ve `BaseComponent` ile otonom veri akışı sağlandı.
* **v10.5:** **SRE Hardening & Zero-Trust CI.** `pytest-socket` tabanlı katı ağ izolasyonu (Network Block) ve asenkron sızıntı koruması eklendi. "Sadece İslami Analiz" modu için Puzzle mimarisi ve API maliyetlerini %90 düşüren **Erken Çıkış (Early Exit)** mantığı devreye alındı. Otonom Web Components (`AnalysisCard`) mimarisine geçiş tamamlandı.
* **v10.1:** **Free-Tier SRE & Ölçeklenebilirlik Optimizasyonu.** Vercel 10s Timeout limitleri için Upstash Redis tabanlı Asenkron Polling (HTTP 202 Job Queue) mimarisine geçildi.
* **v10.0:** **Kurumsal Gözlemlenebilirlik ve PnL (Shadow Tracking).** Tamamen izole Supabase pg_cron tabanlı T+n sanal kâr/zarar ölçüm motoru ve `/metrics` Prometheus telemetri altyapısı kuruldu.
* **v9.0:** **Yönlü Graf (LangGraph) Multi-Agent** kurgusuna geçildi! Bull vs Bear tartışma döngüleri, Devre Kesici (Circuit Breaker) kalkanı ve Shadow Deployment (Gölge Dağıtım) mekanizması ile sıfır riskli paralel geçiş operasyonu. Kapsamlı otonomi ve Fan-Out Fan-In veri toplayıcılar eklendi.
* **v1.2.8:** Güvenli Yönetici Başlatma (Admin Bootstrap) ve Genişletilmiş JWT Yaşam Döngüsü yapılandırması.
* **v1.2.5:** Yönetici yetki izolasyonu (Admin Bypass Fix) ve görsel bildirim katmanı eklendi.
* **v1.2.0:** Landing page tasarımı yenilendi, UX akışları optimize edildi.
* **v1.1.5:** Güvenlik katmanı (Behavioral Brake) iyileştirildi, loglama mekanizması güçlendirildi.
* **v1.1.0:** Çoklu-ajan (CIO) mimarisi canlıya alındı.

---

## 🏗️ Mimari Yapı (Puzzle Framework)

Proje, **Monorepo** yapısında olup hem backend hem frontend tarafında modüler **Puzzle** mimarisini kullanır:

### 🧩 Backend (FastAPI)

* **`/backend/nodes/`**: AI Ajanları ve veri toplama düğümleri.
* **`/backend/engine/`**: LangGraph iş akışları, State yönetimi ve Optimizasyon motoru.
* **`/backend/infrastructure/`**: Auth, LLM Factory, Redis Cache, Scheduler ve Limiter gibi temel yapı taşları.
* **`/backend/services/`**: `ChatOrchestrator` gibi üst düzey iş mantığı sarmalları.
* **`/backend/api/`**: FastAPI Router'lar ve Model tanımları.

### 🎨 Frontend (Vanilla JS)

* **`/frontend/js/core/`**: Uygulama durumu (`state.js`), i18n ve yapılandırma.
* **`/frontend/js/network/`**: API istemcisi ve Supabase entegrasyonu.
* **`/frontend/js/components/`**: `BaseComponent` tabanlı reactive Web Components (`<x-hero-cards>`, `<x-analysis-grid>`).

### 🛠️ Tooling & DevOps

* **`tests/`**: Pytest ve Puppeteer tabanlı otonom testler.
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

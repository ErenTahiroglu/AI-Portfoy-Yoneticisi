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

### 🎨 2. Kullanıcı Deneyimi (UX) & Onboarding

* **Akıllı Karşılama Sihirbazı (Onboarding Wizard):** "Sıfırıncı Seviye" kullanıcılar için 3 adımlı, jargonsuz ve card-based bir yatırım profili oluşturma akışı.
* **Kişiselleştirilmiş AI Yanıtları:** Sihirbazda toplanan veriler otomatik olarak AI sistem prompt'una enjekte edilir.
* **Modern Landing Page (UX Refined):** Scroll-based navigasyon, akıllı "Uygulamaya Git" butonu ve otomatik dashboard atlamayı önleyen kontrollü geçişler.
* **İzole Yönetici Modu (Admin Isolation):** Geliştirici erişimi (Bypass) gerçek kullanıcı oturumlarından ayrıştırıldı; oturum varken kimlik değişimi engellendi.

### 🛡️ 3. Güvenlik ve Kurumsal Kalkanlar (SRE Essentials)

* **Görünmez Duvar (Invisible Wall):** Yeni başlayan kullanıcılar durumuna göre riskli varlıklardan otomatik filtrelenir.
* **Davranışsal Fren (Behavioral Brake):** AI asistanı, yeni başlayanların FUD/FOMO durumlarını durdurur ve rasyonel sorgulama yapar.
* **📊 Telemetry Pipeline:** Tüm güvenlik müdahaleleri Supabase `user_events` tablosunda loglanır.
* **Sıfır Güven (Zero-Trust) IAM:** JWT güvenliği ve Supabase Auth entegrasyonu.
* **Prompt Isolation:** Dışarıdan akan haberler XML etiketleri ile hapsedilir.
* **Idempotency:** Mükerrer emir basımları prevent edilir.

---

## 📝 Son Değişiklikler (Changelog)

* **v1.2.8:** Güvenli Yönetici Başlatma (Admin Bootstrap) ve Genişletilmiş JWT Yaşam Döngüsü yapılandırması.
* **v1.2.5:** Yönetici yetki izolasyonu (Admin Bypass Fix) ve görsel bildirim katmanı eklendi.
* **v1.2.0:** Landing page tasarımı yenilendi, UX akışları optimize edildi.
* **v1.1.5:** Güvenlik katmanı (Behavioral Brake) iyileştirildi, loglama mekanizması güçlendirildi.
* **v1.1.0:** Çoklu-ajan (CIO) mimarisi canlıya alındı.

---

## 🏗️ Mimari Yapı (Monorepo)

* **`/frontend`**: Vanilla Javascript, CSS3 ve HTML5. Dinamik yükleme modals ve Cold Start UI toleransları.
* **`/backend`**: FastAPI (Python 3.11). Asenkron I/O akışları ve arka plan metrik işleyiciler. İzolasyonlu proxy operasyonları.
* **`tests/ui/`**: Puppeteer tabanlı otonom ekran görüntüsü ve görsel test otomasyonu.
* **`brand_assets/`**: Kurumsal logo, renk paletleri ve font guideline kalkanı.
* **`.claudemd`**: AI Workspace kalkanı, teknoloji yığını ve kesin mimari sınır kısıtlamaları.
* **🧩 Modüler Mimari (Puzzle)**: `services/` ve `components/` katmanları ile tam SRP (Single Responsibility) uyumu.
* **🗄️ Database Migrations**: Alembic ile versiyonlanmış veritabanı şeması (Supabase entegrasyonu).


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

* **API Gateway:** `http://localhost:8000`
* **Statik UI Dağılımı:** `http://localhost:8000/ui`

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

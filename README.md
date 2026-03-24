# 📈 AI-Portföy-Yöneticisi (AI Portfolio Manager)

**Yapay Zeka Destekli, Kurumsal Standartlarda Akıllı Portföy Analiz ve Risk Yönetimi Platformu**

[![Vercel](https://img.shields.io/badge/Frontend-Vercel-blue?style=flat-square&logo=vercel)](https://vercel.com)
[![Render](https://img.shields.io/badge/Backend-Render-black?style=flat-square&logo=render)](https://render.com)
[![Supabase](https://img.shields.io/badge/Database-Supabase-green?style=flat-square&logo=supabase)](https://supabase.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-teal?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)

---

## 📖 Genel Bakış

AI-Portföy-Yöneticisi; yatırımcıların hisse senedi, fon ve kripto varlıklarını **Gemini (Yapay Zeka)** motoruyla saniyeler içinde analiz eden, optimize eden ve risk süzgecinden geçiren modern bir web uygulamasıdır. 
Geleneksel analizlerin aksine, canlı veri akışları ve çoklu-ajan asistan (CIO Orchestrator) mimarisiyle yatırımcıya harekete geçebileceği net tavsiyeler üretir.

---

## 🔥 Öne Çıkan Özellikler (Features)

### 🤖 1. Yapay Zeka & Analiz
*   **Chief Investment Officer (CIO) Ajanı:** Analist ve Researcher modellerinden gelen verileri sentezleyen orkestratör asistan.
*   **Hisse & Fon Raporlama:** VaR (Value at Risk), Beta ve Maximum Drawdown gibi modern risk metrikleri.
*   **Makro Analiz Generator:** Tüm portföyün korelasyonlarını ve dengeleme ihtiyaçlarını streaming (akan) metin olarak sunar.

### 🛡️ 2. Güvenlik ve Kurumsal Kalkanlar (SRE Essentials)
*   **Sıfır Güven (Zero-Trust) IAM:** WebSocket ve API kollarında JWT güvenliği ve Redis tabanlı Canlı **Oturum İptal (Revocation)** süzgeci.
*   **Thundering Herd & Cache Stampede Guard:** Yeniden bağlanma anlarında **Exponential Jitter** metodu ve RAM içi Mutex loklaması ile sunucu darboğazlarını çözer.
*   **Prompt Isolation & PII Sanitization:** Dışarıdan akan haberler XML etiketleri ile hapsedilir, LLM’e gitmeden hassas bakiye verileri otomatik maskelenir.
*   **Idempotency & Tracing:** Mükerrer emir basımları (Double-click) prevent edilir; baştan uca UUID Correlation zinciri mevcuttur.

---

## 🏗️ Mimari Yapı (Monorepo)

*   **`/frontend`**: Vanilla Javascript, CSS3 ve HTML5. Dinamik yükleme modals ve Cold Start UI toleransları.
*   **`/backend`**: FastAPI (Python 3.11). Asenkron I/O akışları ve arka plan metrik işleyiciler. İzolasyonlu proxy operasyonları.
*   **`/infrastructure`**: Statik veritabanı `schema.sql` ve Docker konfigürasyonları.

---

## 🚀 Başlangıç & Kurulum (Lokal)

Sistemi bilgisayarınızda ayağa kaldırmak için aşağıdaki adımları izleyin:

### 1. Dosya Hazırlığı (.env)
Kök dizindeki şablonu kopyalayarak `.env` dosyanızı oluşturun ve anahtarları doldurun:
```bash
cp .env.example .env
```
> **Gerekli Temel Anahtarlar:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `UPSTASH_REDIS_REST_URL`.

### 2. Docker İle Hızlı Kurulum
Tüm platformu tek satır kodla ayağa kaldırabilirsiniz:
```bash
docker-compose up --build
```
*   **API Gateway:** `http://localhost:8000`
*   **Statik UI Dağılımı:** `http://localhost:8000/ui`

---

## 🤝 İletişim & Destek
*   **Geliştirici:** Eren Tahiroğlu
*   **Sponsorluk:** Katkıda bulunmak için [GitHub Sponsor](https://github.com/sponsors/ErenTahiroglu) sayfasını ziyaret edebilirsiniz.

Saygılarımızla.

# 🏛️ Sistem Mimarisi (ARCHITECTURE.md)

**AI-Portföy-Yöneticisi** platformu, yüksek erişilebilirlik, hız ve kurumsal güvenlik (SRE) standartları gözetilerek **Three-Tier (3 Katmanlı)** bir monorepo mimarisiyle tasarlanmıştır.

---

## 🗺️ 1. Genel Mimari (Three-Tier)

Sistem 3 temel katmandan oluşur:

### 🌟 A. Sunum Katmanı (Frontend - Vercel)
*   **Teknoloji:** Vanilla JS, HTML5, CSS3, Chart.js.
*   **Görev:** Kullanıcının portföyünü görselleştirmek, AI chatbot ile konuşmasını sağlamak ve canlı fiyatları yansıtmak.
*   **Özellik:** API_BASE dinamik yönetimi ve **Render Cold Start** koruma mekanizmalarına sahiptir.

### ⚙️ B. Mantık Katmanı (Backend - Render)
*   **Teknoloji:** FastAPI (Python), httpx, ASGI (Uvicorn).
*   **Görev:** Analitik hesaplamalar, AI Ajan orkestrasyonu, veri proxy'liği ve WebSocket canlı akışı yönetimi.
*   **Güvenlik:** JWT tabanlı Sıfır Güven (Zero-Trust) IAM, Rate Limiter ve Mutex Cache kalkanları Backend'ten yönetilir.

### 🗄️ C. Veri Katmanı (Data Lake - Supabase & Redis)
*   **Supabase (PostgreSQL + PostgREST):** Kullanıcı portföyleri, geçmiş snapshotlar ve loglar burada tutulur. Erişimler Backend proxy üzerinden stateless HTTP REST ile HTTPS güvenliğiyle gerçekleşir.
*   **Redis (Upstash):** Dağıtık önbellek (Cache), API hız sınırlaması (Rate Limit) ve token revokasyonu (Blocklist) için kullanılır.

---

## 🔄 2. Veri Akış Modelleri (Data Flow)

### 📈 Örnek Senaryo: Portföy Optimizasyonu Talebi

Kullanıcı arayüzden **"Portföyümü Analiz Et"** butonuna bastığında veri şu yollardan geçer:

1.  **İstemci (Vercel):** İstek ön yüz üzerinden fırlatılır. `X-Correlation-ID` başlığı eklenir (Tracing).
2.  **Güvenlik Kapısı (CORS & Rate Limiter):** Render'a ulaşan istek CORS whitelist süzgecinden geçer. Redis üzerindeki IP bazlı **Rate Limiter** hızı doğrular.
3.  **Kimlik Doğrulama (Auth):** `verify_jwt` middleware'i, Supra Auth JWT tokenı doğrular ve kullanıcının oturumunun Redis **Blocklist**'te olup olmadığına bakar.
4.  **Önbellek Sorgulama (Cache):** Analiz sonucu talep edilmeden önce Redis Cache sorgulanır. Cache Miss olursa **Mutex Locking** devreye girerek Cache Stampede önlenir.
5.  **Analitik & AI Orkestrasyonu (`ai_agent.py`):**
    *   Sistem kullanıcının portföy kurgusunu alır.
    *   Hassas değerler prompt öncesi **Maskelenir (PII Sanitization)**.
    *   İçerikler `<news_item>` etiketleriyle beslenerek **Indirect Prompt Injection** engellenir.
6.  **Nihai Sonuç:** Yapay zeka orkestratörü (CIO) çıktı üretir ve Frontend'e basar. İstek veritabanına loglanır.

---

## 🛡️ 3. SRE ve Hata Toleransı

*   **Circuit Breaker (Şalter):** Dış finansal API (Polygon vb.) çöktüğünde sistem kilitlenmez, Falling-back modeline geçilir.
*   **Stateless Scaling:** Backend kurgusu RAM'de session tutmaz, bu sayede Render üzerinde yatayda sonsuz çoğaltılabilir (Scale-out).

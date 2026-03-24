# 📈 AI-Portföy-Yöneticisi (AI Portfolio Manager)

Yapay Zeka (Gemini) destekli, modern mimariye sahip portföy analiz, optimizasyon ve risk yönetim platformu.

---

## 🏗️ Proje Yapısı (Monorepo)

- **`/frontend`**: Vanilla Javascript, HTML ve Vanilla CSS tabanlı dinamik kullanıcı arayüzü. (Vercel deployment uyumlu).
- **`/backend`**: FastAPI tabanlı yüksek performanslı analitik sunucu. (Render/Docker deployment uyumlu).
- **`/infrastructure`**: Veritabanı (`schema.sql`) kurulum dosyalarını barındırır.

---

## 🚀 Başlangıç & Kurulum

### 1. Ortam Değişkenleri (.env)
Kök dizindeki `.env.example` dosyasını kopyalayıp `.env` adında bir dosya oluşturun:
```bash
cp .env.example .env
```
Gerekli `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY` vb. anahtarları doldurun.

### 2. Docker ile Çalıştırma
Tüm altyapıyı tek bir komutla ayağa kaldırabilirsiniz:
```bash
docker-compose up --build
```
API sunucusu otomatik olarak `http://localhost:8000` portunda çalışacaktır.

---

## 🛡️ Güvenlik ve Kurumsal Standartlar (Enterprise Grade)
Bu proje üzerinde uygulanan son SRE ve Güvenlik denetimleriyle birlikte (Aşama 1-8):

*   **Sıfır Güven (Zero-Trust):** WebSocket ve REST API’ler JWT IAM katmanı ile korunmaktadır. Oturum kapatmalar için Redis tabanlı otomatik **Blocklist** mekanizması bulunur.
*   **İdempotens & Tracing:** Mükerrer emirler saniyeler içinde süzülür (Double-click guard) ve UUID tabanlı korelasyon log zinciri kurulmuştur.
*   **Thundering Herd & Cache Stampede Guard:** Yeniden bağlanma (Reconnect) anlarında rastgele bileşenli **Exponential Jitter** uygulanmış ve RAM içi Mutex kilitleme ile cache fırtınaları engellenmiştir.
*   **Hata Toleransı (Circuit Breaker):** Dış API kesintilerinde ML tahminleri askıya alınır ("Fallback") ve sistemin çökmesi önlenir.
*   **Prompt Injection & PII Masking:** Dış haberler XML delimiters (`<news_item>`) ile süzülür, LLM’e gitmeden önce hassas finansal veriler maskelenerek tam veri güvenliği sağlanır.
*   **Cold Start Toleransı (SRE):** Render "uykuya dalma" gecikmelerinde arayüz, kullanıcıyı dinamik sayaca bağlayarak uyarır ve ağ stresini azaltır.

Saygılar.

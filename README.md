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

## 🛡️ Güvenlik ve Kurumsal Standartlar
Bu proje üzerinde uygulanan son denetimlerle birlikte:
- **İdempotens:** Ağır analiz süreçlerinde mükerrer basımlar (Double-click) engellenmiştir.
- **Dağıtık İzleme (Tracing):** Ön yüzden backend'e kadar UUID tabanlı log korelasyon zinciri kurulmuştur.
- **Graceful Shutdown & Fail-Fast:** Başlangıçta eksik ayarlar anında çöker, kapanırken kaynaklar sızıntısız temizlenir.
- **Güvenlik Çitleri:** Swagger Docs canlı ortamda kapalıdır, CORS katı origin beyaz listesindedir.

Saygılar.

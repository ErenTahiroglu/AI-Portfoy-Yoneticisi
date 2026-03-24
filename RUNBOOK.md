# 🆘 Nöbetçi Mühendis El Kitabı (RUNBOOK.md)

**AI-Portföy-Yöneticisi** platformunda oluşabilecek operasyonel kriz anlarında (Disaster) takip edilmesi gereken acil müdahale (Troubleshooting) adımlarıdır.

---

## 🚨 Senaryo 1: Render Uygulaması Crash Loop'ta (Sürekli Çöküyor)

### 🔍 Olası Nedenler:
- Kritik bir ortam değişkeninin (`env`) eksik veya yanlış tanımlanması.
- Render port bağlama (`$PORT`) çakışması.
- Bağımlılıkların derlenememesi (Build failure).

### 🛠️ Müdahale Adımları:
1.  **Render Logs:** Render Dashboard'dan `Deploy Logs` ekranına gidin. `sys.exit(1)` veya `traceback` veren hatayı okuyun.
2.  **Healthcheck Probe:** `render.yaml` üzerinde `healthCheckPath` rotasının `/api/health` olduğundan emin olun. Canlı ortamda `/docs` kapalıdır!
3.  **Environment Variables:** `SUPABASE_URL` veya `GEMINI_API_KEY` gibi kritik anahtarlarda tırnak işareti (`""`) veya boşluk kalıp kalmadığını kontrol edin.

---

## 🛑 Senaryo 2: Kullanıcılar "Çok Fazla İstek" (429) Alıyor

### 🔍 Olası Nedenler:
- DDoS veya bot saldırısı.
- Bir kullanıcının döngüye giren (Infinite loop) ön yüz kodu.
- Redis IP limitlerinin çok dar kurgulanması.

### 🛠️ Müdahale Adımları:
1.  **Redis Dashboard (Upstash):** Gelen istek hacmini ve en çok istek atan IP adresini tespit edin.
2.  **Temizlik:** Eğer kilitlenen bir IP varsa ve saldırı değilse, `backend/core/redis_cache.py` üzerinden Redis'teki ilgili sayacı (`ratelimit:ip_adresi`) temizleyin (`DEL` komutu).
3.  **Limit Gevşetme:** Eğer kapasite yetersizse `backend/core/circuit_breaker.py` veya rate limiter ayarındaki limitleri (Örn: Dakikada 60 -> 120) geçici olarak artırın ve Redeploy atın.

---

## 🧠 Senaryo 3: LLM Halüsinasyon Görüyor / Fatura Kabarıyor

### 🔍 Olası Nedenler:
- Prompt Enjeksiyonu (Müdahale edilmiş dış haberler).
- Prompt parametrelerindeki `temperature` değerinin çok yüksek olması.
- `max_output_tokens` sınırının olmaması yüzünden LLM'in sonsuz döngüde metin üretmesi.

### 🛠️ Müdahale Adımları:
1.  **Prompt İzleme:** `ai_agent.py` içindeki orkestratör modellerinin temperature değerlerini kontrol edin (Standardı `0.3` seviyesindedir).
2.  **Delimiter İzolasyonu:** Son güncellemelerle eklenen `<news_item>` etiketlerinin `ai_agent.py` ve `news_fetcher.py` üzerinde aktif kaldığından emin olun. Etiket kaldırıldıysa geri ekleyin.
3.  **Quota Limit:** Google Generative AI (Google AI Studio) konsolunu açıp saatlik ve günlük token kotalarını gözden geçirin, gerekirse üst sınır (Hard Cap) koyun.

---

## 🔌 Senaryo 4: Veritabanı ve Ağ Bağlantı Problemleri

*   **Supabase 401/403:** `SUPABASE_SERVICE_ROLE_KEY` süresi dolmuş veya değiştirilmiş olabilir.
*   **SSL Handshake Failure:** Supabase bağlantı adresinde `?sslmode=require` veya HTTPS protokolünün zorunlu kılınmış olduğunu (Default) doğrulayın.

---
*Nöbetçi Mühendis Notu: "Metrikler için `/api/metrics` rotasını, genel sağlık için `/api/health` rotasını anlık dinleyin."*

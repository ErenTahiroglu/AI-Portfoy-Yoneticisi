---- RENDER FREE YENİLMEZ (UNDYING) CRON HACK
---- Supabase SQL Editor üzerinden çalıştırılır.

-- İlk olarak HTTP eklentisini aktif et (Genellikle Supabase'de var)
CREATE EXTENSION IF NOT EXISTS http;

-- 14 dakikada bir çalışacak şekilde cron job oluştur.
-- Render, 15 dakika hareketsiz kalınca uyur. Biz 14. dakikada ping atarak
-- bu sayacı sürekli sıfırlıyoruz.

SELECT cron.schedule(
    'render-keep-alive-job', -- Job Adı
    '*/14 * * * *',          -- Cron süresi: Her 14 dakikada bir
    $$
    SELECT status FROM http_get('https://ai-portfoy-yoneticisi.onrender.com/api/health');
    $$
);

/*
Bilgi Modülü: Eğer Supabase pg_net eklentisini zorunlu tutuyorsa net.http_get() kullanılmalıdır:
SELECT cron.schedule(
    'render-keep-alive-job',
    '*/14 * * * *',
    $$ SELECT net.http_get(url:='https://ai-portfoy-yoneticisi.onrender.com/api/health') $$
);
*/

const CACHE_NAME = 'portfolio-ai-v5';

const STATIC_ASSETS = [
    './',
    './index.html',
    './styles.css',
    './manifest.json',
    './logo.png',
    './js/core/i18n.js',
    './js/utils.js',
    './js/db.js',
    './js/core/state.js',
    './js/network/api.js',
    './js/charts.js',
    './js/app.js',
    './js/components/AnalysisComponents.js',
    './js/components/DashboardComponents.js'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        (async () => {
            const keys = await caches.keys();
            await Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)));
            await self.clients.claim();
        })()
    );
});

self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // API POST calls (Analysis, Chat vb.) → Network First with Timeout Catch
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => new Response(JSON.stringify({ error: 'Bağlantı koptu veya sunucu uyanamadı.' }), {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }))
        );
        return;
    }

    // Static assets & Diğer her şey → Stale-While-Revalidate Stratejisi
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            const fetchPromise = fetch(event.request).then((networkResponse) => {
                // Arkaplanda ağı kontrol et, yeniyse cache'i güncelle
                if (networkResponse && networkResponse.status === 200) {
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, networkResponse.clone());
                    });
                }
                return networkResponse;
            }).catch(() => {
                // Offline durumunda sessizce fail ol
                console.warn("[SW] Offline: Ağa ulaşılamadı, Cache ile devam ediliyor.");
            });
            
            // Eğer Cache'de varsa ANINDA ver, yoksay fetchPromise'i (Ağı) bekle
            return cachedResponse || fetchPromise;
        })
    );
});

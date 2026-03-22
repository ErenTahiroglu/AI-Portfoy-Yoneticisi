const CACHE_NAME = 'portfolio-ai-v5';

const STATIC_ASSETS = [
    './',
    './index.html',
    './styles.css',
    './manifest.json',
    './logo.png',
    './js/i18n.js',
    './js/utils.js',
    './js/db.js',
    './js/state.js',
    './js/api.js',
    './js/charts.js',
    './js/app.js',
    './js/components/CardComponent.js'
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
    // API calls → network first
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => new Response(JSON.stringify({ error: 'Çevrimdışı' }), {
                headers: { 'Content-Type': 'application/json' }
            }))
        );
        return;
    }
    // Static assets → cache first, then network
    event.respondWith(
        caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
});

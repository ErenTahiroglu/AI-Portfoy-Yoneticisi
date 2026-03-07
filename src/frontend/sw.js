const CACHE_NAME = 'portfolio-v3';
const STATIC_ASSETS = [
    '/ui/',
    '/ui/index.html',
    '/ui/styles.css',
    '/ui/app.js',
    '/ui/i18n.js',
    '/ui/manifest.json',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
        )
    );
    self.clients.claim();
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

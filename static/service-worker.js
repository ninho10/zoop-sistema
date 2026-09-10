const CACHE_NAME = 'zoop-cache-v1';
const urlsToCache = [
    '/static/style.css',
    '/static/logo.png',
    '/static/manifest.json'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request).catch(() => {
            // If network fails, try to return from cache
            return caches.match(event.request);
        })
    );
});

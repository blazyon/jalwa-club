const CACHE_NAME = 'luckydraw-v1';
const STATIC_ASSETS = [
  '/',
  '/games/wingo/',
  '/games/k3/',
  '/games/5d/',
  '/wallet/',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  if (e.request.url.includes('/api/')) return; // Always fresh for API
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});

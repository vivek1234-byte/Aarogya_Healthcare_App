const CACHE_NAME = 'meditek-cache-v3';
const ASSETS_TO_CACHE = [
  './',
  'patient_dashboard.html',
  'index.html',
  'dashboard.css',
  'dashboard.js',
  'style.css',
  'script.js',
  'manifest.json',
  'assets/melina_avatar.jpg',
  'assets/ai_orb.jpg',
  'assets/exact_top_hero.jpg'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});

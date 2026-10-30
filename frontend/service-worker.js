const CACHE_NAME = 'arogya-cache-v14';
const ASSETS_TO_CACHE = [
  './',
  'index.html',
  'style.css',
  'script.js',
  'app.css',
  'app.js',
  'patient_dashboard.html',
  'patient.css',
  'patient.js',
  'health_worker.html',
  'health_worker.js',
  'doctor.html',
  'doctor.js',
  'officer.html',
  'officer.js',
  'manifest.json',
  'assets/icon-192.png',
  'assets/icon-512.png',
  'assets/ai_orb.jpg',
  'assets/login_hero.jpg'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE).catch(() => {}))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.map((key) => (key !== CACHE_NAME ? caches.delete(key) : null))))
  );
  self.clients.claim();
});

// Network first so updates show immediately; cached app shell only when offline.
// API calls and non-GET requests always go to the network (never cached).
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.pathname.startsWith('/api/') || url.origin !== self.location.origin) return;
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(e.request, copy));
        }
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});

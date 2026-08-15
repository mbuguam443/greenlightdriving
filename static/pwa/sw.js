var CACHE = 'greenlight-portal-v1';
var PRECACHE = [
  '/static/images/logo.png',
  '/static/images/favicon.ico',
  '/static/pwa/pwa-192x192.png',
  '/static/pwa/pwa-512x512.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE)
      .then(function (cache) { return cache.addAll(PRECACHE); })
      .then(function () { return self.skipWaiting(); })
      .catch(function () { self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;
  var url = new URL(event.request.url);
  if (url.origin !== location.origin) return;

  // Network-first for page navigations so the portal stays fresh; offline fallback to cache.
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).then(function (resp) {
        var copy = resp.clone();
        caches.open(CACHE).then(function (cache) { cache.put(event.request, copy); });
        return resp;
      }).catch(function () {
        return caches.match(event.request);
      })
    );
    return;
  }

  // Cache-first for static assets.
  event.respondWith(
    caches.match(event.request).then(function (cached) {
      return cached || fetch(event.request).then(function (resp) {
        if (resp && resp.status === 200) {
          var copy = resp.clone();
          caches.open(CACHE).then(function (cache) { cache.put(event.request, copy); });
        }
        return resp;
      });
    })
  );
});

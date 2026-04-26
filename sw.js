const CACHE_NAME = 'manabi-20260426';
const PRECACHE = ['/', '/index.html', '/manifest.json'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);

  if (url.origin === location.origin && url.pathname.startsWith('/functions/')) return;
  if (url.origin !== location.origin) {
    const host = url.hostname;
    if (!host.endsWith('googleapis.com') && !host.endsWith('gstatic.com') &&
        !host.endsWith('jsdelivr.net') && !host.endsWith('unpkg.com')) return;
  }

  const isNavigation = e.request.mode === 'navigate';
  e.respondWith(
    fetch(e.request).then(res => {
      if (res.ok) {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
      }
      return res;
    }).catch(() => {
      if (isNavigation) return caches.match('/index.html');
      return caches.match(e.request);
    })
  );
});

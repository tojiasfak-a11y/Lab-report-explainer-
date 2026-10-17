/* Service worker: lets the site open instantly and work offline after the first visit.
   - Same-site files: network first (so updates arrive), cache as the offline fallback.
   - Reading tools (pdf.js / Tesseract) from the CDN: cached after first use so scans work faster later. */
const SHELL = 'thelivu-shell-v2';
const TOOLS = 'thelivu-tools-v1';
const FILES = ['./', './index.html', './manifest.json', './icon-192.png', './icon-512.png', './favicon-96.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith('thelivu-') && k !== SHELL && k !== TOOLS).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    e.respondWith(fetch(req, { cache: 'no-cache' }).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(SHELL).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req).then(hit => hit || caches.match('./index.html'))));
  } else if (/(^|\.)(jsdelivr\.net|cdnjs\.cloudflare\.com|projectnaptha\.com)$/.test(url.hostname)) {
    e.respondWith(caches.open(TOOLS).then(c => c.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok) c.put(req, res.clone());
      return res;
    }))));
  }
});

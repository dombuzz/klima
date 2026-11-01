// Service Worker «Raumklima»: macht die Seite installierbar.
// Seiten und Symbole der eigenen Domain werden zuerst vom Netz geholt (immer aktuell);
// nur wenn das Netz fehlt, kommt die zuletzt gesehene Kopie. Messdaten (andere Domains) werden nie zwischengespeichert.
const CACHE = 'klima-v1';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())
));
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET' || new URL(r.url).origin !== self.location.origin) return;
  e.respondWith(
    fetch(r).then(res => {
      if (res.ok) { const c = res.clone(); caches.open(CACHE).then(ch => ch.put(r, c)); }
      return res;
    }).catch(() => caches.match(r).then(m => m || caches.match('/')))
  );
});

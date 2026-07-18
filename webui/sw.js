// Minimal service worker: cache the app shell so Mnemos installs as a PWA and opens
// offline. Dynamic endpoints (/ask) are never cached.
const CACHE = "mnemos-v1";
const SHELL = ["/", "/icon-192.png", "/icon-512.png", "/manifest.webmanifest"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.pathname === "/ask") return; // don't cache POST/dynamic
  e.respondWith(caches.match(e.request).then((r) => r || fetch(e.request)));
});

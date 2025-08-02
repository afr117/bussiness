const cacheName = "product-cache-v1";
const staticAssets = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/icons/manifest-icon-192.png",
  "/static/icons/manifest-icon-512.png"
];

self.addEventListener("install", async e => {
  const cache = await caches.open(cacheName);
  await cache.addAll(staticAssets);
  return self.skipWaiting();
});

self.addEventListener("activate", e => {
  self.clients.claim();
});

self.addEventListener("fetch", async e => {
  const req = e.request;
  const cachedResponse = await caches.match(req);
  return cachedResponse || fetch(req);
});

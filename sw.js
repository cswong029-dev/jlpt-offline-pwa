/* 更新擴充包或核心檔後，請 bump 版本以刷新快取 */
/* wkei-vocab 大型 JSON 不預載，首次連線後由 fetch 寫入快取 */
const CACHE_NAME = 'jlpt-offline-v8';

const CORE_URLS = [
  './index.html',
  './css/app.css',
  './js/storage.js',
  './js/data.js',
  './js/tts.js',
  './js/app.js',
  './manifest.webmanifest',
  './data/registry.json',
  './data/packs/builtin-grammar/grammar.json',
  './data/packs/builtin-grammar/quizzes.json',
  './data/packs/sample-n5/vocab.json',
  './data/packs/sample-n5/grammar.json',
  './data/packs/sample-n5/quizzes.json',
  './data/packs/sample-n5/reading.json',
  './data/packs/sample-n5/listening.json',
  './data/packs/graded-reading/reading.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((res) => {
          const copy = res.clone();
          if (res.ok) {
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return res;
        })
        .catch(() => caches.match(event.request));
    })
  );
});

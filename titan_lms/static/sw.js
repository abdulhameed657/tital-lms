const CACHE_NAME = 'titan-lms-cache-v1';
const urlsToCache = [
  '/',
  '/student/dashboard',
  '/student/code_sandbox',
  '/student/flashcards'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      })
  );
});

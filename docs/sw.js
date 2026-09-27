// Service worker: lets Ski Info open with poor or no coverage on the slopes.
// Everything of our own goes to the network first (so a deploy is picked up
// straight away) and falls back to the last copy when offline; the stations
// you've opened (their data files) stay available. Other sites (weather,
// satellite tiles, stats) are left alone.
var VERSION = 'v2';
var SHELL = 'skiinfo-shell-' + VERSION;
var PAGES = 'skiinfo-pages-' + VERSION;
var DATA = 'skiinfo-data-' + VERSION;
var ASSETS = 'skiinfo-assets-' + VERSION;
var LIMITS = {};
LIMITS[PAGES] = 80;
LIMITS[DATA] = 40;      // station data files can be large
LIMITS[ASSETS] = 300;
var SHELL_FILES = ['/', '/profile.js', '/snow.js', '/snow.css', '/station-actions.js', '/track.js',
  '/static-pages.css', '/static-pages.js', '/favicon.svg', '/icons/icon-192.png', '/manifest.webmanifest'];

self.addEventListener('install', function (event) {
  event.waitUntil(caches.open(SHELL).then(function (cache) {
    return cache.addAll(SHELL_FILES.map(function (u) { return new Request(u, { cache: 'reload' }); }));
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (event) {
  var keep = [SHELL, PAGES, DATA, ASSETS];
  event.waitUntil(caches.keys().then(function (names) {
    return Promise.all(names.filter(function (n) { return keep.indexOf(n) === -1; }).map(function (n) { return caches.delete(n); }));
  }).then(function () { return self.clients.claim(); }));
});

function trim(cacheName) {
  var max = LIMITS[cacheName];
  if (!max) return;
  caches.open(cacheName).then(function (cache) {
    cache.keys().then(function (keys) {
      // Oldest entries first (insertion order).
      for (var i = 0; i < keys.length - max; i++) cache.delete(keys[i]);
    });
  });
}

function networkFirst(request, cacheName, fallbackUrl) {
  return fetch(request).then(function (response) {
    if (response.ok) {
      var copy = response.clone();
      caches.open(cacheName).then(function (cache) { cache.put(request, copy).then(function () { trim(cacheName); }); });
    }
    return response;
  }).catch(function () {
    return caches.match(request, { ignoreSearch: request.mode === 'navigate' }).then(function (hit) {
      if (hit) return hit;
      if (fallbackUrl) return caches.match(fallbackUrl);
      return Response.error();
    });
  });
}

function cacheFirst(request, cacheName) {
  return caches.match(request).then(function (hit) {
    return hit || fetch(request).then(function (response) {
      if (response.ok) {
        var copy = response.clone();
        caches.open(cacheName).then(function (cache) { cache.put(request, copy).then(function () { trim(cacheName); }); });
      }
      return response;
    });
  });
}

self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (request.method !== 'GET') return;
  var url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname === '/stats.html' || url.pathname === '/sw.js') return;

  if (request.mode === 'navigate') {
    event.respondWith(networkFirst(request, PAGES, '/'));
  } else if (/^\/(data\/.*|snow|guias|slugs)\.json$/.test(url.pathname)) {
    event.respondWith(networkFirst(request, DATA));
  } else if (/^\/(flags|icons|og\/thumb)\//.test(url.pathname)) {
    event.respondWith(cacheFirst(request, ASSETS));
  } else {
    event.respondWith(networkFirst(request, ASSETS));
  }
});

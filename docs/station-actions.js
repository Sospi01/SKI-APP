// "Cómo llegar" and "Compartir" for a station, shared by the app
// (index.html) and the generated station pages.

// Where directions should point: the lowest lift end -- the base area, where
// the car park usually is (the station's centre is often up the mountain).
// Mirrors base_location() in data-pipeline/scripts/build_seo_pages.py.
function stationBaseLocation(raw) {
  var best = null;
  (raw.lifts || []).forEach(function (l) {
    (l.geom || []).forEach(function (part) {
      if (!part.length) return;
      [part[0], part[part.length - 1]].forEach(function (p) {
        if (p.length > 2 && p[2] != null && (!best || p[2] < best[2])) best = p;
      });
    });
  });
  if (best) return { lat: best[1], lon: best[0] };
  if (raw.latitude != null) return { lat: raw.latitude, lon: raw.longitude };
  return null;
}

function stationDirectionsUrl(raw) {
  var p = stationBaseLocation(raw);
  return p ? 'https://www.google.com/maps/dir/?api=1&destination=' + p.lat.toFixed(5) + ',' + p.lon.toFixed(5) : null;
}

if (typeof T !== 'function') { var T = function (s) { var a = arguments; return s.replace(/\{(\d)\}/g, function (m, i) { return a[+i + 1]; }); }; }

function showShareToast(text) {
  var t = document.getElementById('share-toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'share-toast';
    t.setAttribute('role', 'status');
    t.style.cssText = 'position:fixed;left:50%;bottom:84px;transform:translateX(-50%);z-index:60;background:#10161c;color:#fff;'
      + 'font:600 13px/1.3 "IBM Plex Sans",system-ui,sans-serif;padding:10px 16px;border-radius:999px;'
      + 'box-shadow:0 10px 24px -8px rgba(0,0,0,.5);transition:opacity .25s;pointer-events:none';
    document.body.appendChild(t);
  }
  t.textContent = text;
  t.style.opacity = '1';
  clearTimeout(showShareToast.timer);
  showShareToast.timer = setTimeout(function () { t.style.opacity = '0'; }, 2200);
}

// Android app (native share sheet via the WebView bridge, from app 1.0.5),
// then the browser's own share sheet, then copy to the clipboard.
function shareStationLink(title, url) {
  var text = T('{0} en Ski Info: mapa de pistas y previsión de nieve', title);
  try {
    if (window.SkiInfoAndroid && window.SkiInfoAndroid.share) { window.SkiInfoAndroid.share(text, url); return; }
  } catch (e) { /* fall through */ }
  if (navigator.share) {
    navigator.share({ title: title + ' · Ski Info', text: text, url: url }).catch(function () {});
    return;
  }
  function done() { showShareToast(T('Enlace copiado')); }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(done, function () { window.prompt(T('Copia el enlace:'), url); });
  } else {
    window.prompt(T('Copia el enlace:'), url);
  }
}

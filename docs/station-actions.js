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

// "Mis estaciones": the ids of the stations someone saved, newest first, kept
// in this browser only (the home page lists them with their snow forecast).
var FAV_KEY = 'si_favs', FAV_MAX = 30;
function favStations() {
  try {
    var v = JSON.parse(localStorage.getItem(FAV_KEY) || '[]');
    return Array.isArray(v) ? v.filter(function (x) { return typeof x === 'string'; }) : [];
  } catch (e) { return []; }
}
function isFavStation(id) { return favStations().indexOf(id) !== -1; }
// Returns the new state (true = saved), or null if the browser can't store it.
function toggleFavStation(id) {
  var list = favStations(), i = list.indexOf(id);
  if (i === -1) list.unshift(id); else list.splice(i, 1);
  try { localStorage.setItem(FAV_KEY, JSON.stringify(list.slice(0, FAV_MAX))); } catch (e) { return null; }
  return i === -1;
}
var FAV_ICON = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 2.6l2.2 4.6 5 .7-3.6 3.5.9 5-4.5-2.4-4.5 2.4.9-5L2.8 7.9l5-.7z" '
  + 'fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>';
// Wires a "Guardar" button: its label, pressed state and a confirmation toast.
// getStation() -> { id, name, country } of the station it applies to.
function setupFavButton(btn, getStation, onChange) {
  function paint() {
    var s = getStation(), on = !!(s && isFavStation(s.id));
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    btn.classList.toggle('is-fav', on);
    btn.innerHTML = FAV_ICON + '<span></span>';
    btn.querySelector('span').textContent = on ? T('Guardada') : T('Guardar');
    // Phones show just the star (see .fav-btn in the CSS): the label stays readable to screen readers.
    btn.setAttribute('aria-label', on ? T('Guardada') : T('Guardar'));
  }
  btn.addEventListener('click', function () {
    var s = getStation();
    if (!s) return;
    var on = toggleFavStation(s.id);
    if (on === null) return;
    paint();
    showShareToast(on ? T('Guardada en Mis estaciones') : T('Quitada de Mis estaciones'));
    if (on && window.SkiTrack && SkiTrack.fav) SkiTrack.fav(s.id, s.name, s.country);
    if (onChange) onChange(on);
  });
  paint();
  return paint;
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

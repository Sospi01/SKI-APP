// Snow + weather forecast for a station, shared by the app (index.html) and
// the generated station pages. One Open-Meteo request (free, no key,
// CORS-enabled) covers two points on the same coordinates: the top of the
// station and its base, so temperatures are downscaled to each altitude.
// Snowfall/snow depth/freezing level come from the weather models, not from
// the station's own snow report -- the widget says so.

var WEATHER_CODE = {
  0: "Despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
  45: "Niebla", 48: "Niebla escarchada",
  51: "Llovizna débil", 53: "Llovizna", 55: "Llovizna intensa",
  56: "Llovizna helada", 57: "Llovizna helada intensa",
  61: "Lluvia débil", 63: "Lluvia", 65: "Lluvia intensa",
  66: "Lluvia helada", 67: "Lluvia helada intensa",
  71: "Nieve débil", 73: "Nieve", 75: "Nieve intensa", 77: "Cristales de nieve",
  80: "Chubascos débiles", 81: "Chubascos", 82: "Chubascos intensos",
  85: "Chubascos de nieve", 86: "Chubascos de nieve intensos",
  95: "Tormenta", 96: "Tormenta con granizo", 99: "Tormenta con granizo intensa"
};
if (typeof localizeTable === 'function') localizeTable(WEATHER_CODE, 'weather');
var SNOW_LOCALE = typeof SKI_LOCALE === 'string' ? SKI_LOCALE : 'es-ES';
if (typeof T !== 'function') { var T = function (s) { var a = arguments; return s.replace(/\{(\d)\}/g, function (m, i) { return a[+i + 1]; }); }; } // pages without docs/i18n.js

var WEATHER_ICONS = {
  sun: '<circle cx="12" cy="12" r="4.2" fill="currentColor"/><path d="M12 2.8v2.4M12 18.8v2.4M2.8 12h2.4M18.8 12h2.4M5.5 5.5l1.7 1.7M16.8 16.8l1.7 1.7M5.5 18.5l1.7-1.7M16.8 7.2l1.7-1.7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
  partly: '<g class="wx-sun"><circle cx="9" cy="9" r="3.4" fill="currentColor"/><path d="M9 2.4v1.6M2.4 9h1.6M4.3 4.3l1.1 1.1M13.7 4.3l-1.1 1.1" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></g><path class="wx-cloud" d="M9.5 20h9a3.4 3.4 0 0 0 .3-6.8 5 5 0 0 0-9.4 1.7A2.6 2.6 0 0 0 9.5 20z"/>',
  cloud: '<path class="wx-cloud" d="M7 19h11a4 4 0 0 0 .4-8 6 6 0 0 0-11.3 2A3 3 0 0 0 7 19z"/>',
  fog: '<path class="wx-cloud" d="M7 14h11a4 4 0 0 0 .4-8 6 6 0 0 0-11.3 2A3 3 0 0 0 7 14z"/><path d="M4 17.5h16M6 21h12" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/>',
  rain: '<path class="wx-cloud" d="M7 14h11a4 4 0 0 0 .4-8 6 6 0 0 0-11.3 2A3 3 0 0 0 7 14z"/><path d="M8.5 16.5l-1 3M12.5 16.5l-1 3M16.5 16.5l-1 3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>',
  snow: '<path class="wx-cloud" d="M7 13.5h11a4 4 0 0 0 .4-8 6 6 0 0 0-11.3 2A3 3 0 0 0 7 13.5z"/><g fill="currentColor"><circle cx="8" cy="17" r="1.25"/><circle cx="12.5" cy="19.5" r="1.25"/><circle cx="16.5" cy="17" r="1.25"/><circle cx="10" cy="21.8" r="1.1"/><circle cx="15" cy="22" r="1.1"/></g>',
  storm: '<path class="wx-cloud" d="M7 14h11a4 4 0 0 0 .4-8 6 6 0 0 0-11.3 2A3 3 0 0 0 7 14z"/><path d="M12.5 14.5l-2.5 4h3l-2 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
};

function weatherKind(code) {
  if (code == null) return 'cloud';
  if (code <= 1) return 'sun';
  if (code === 2) return 'partly';
  if (code === 3) return 'cloud';
  if (code === 45 || code === 48) return 'fog';
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return 'snow';
  if (code >= 95) return 'storm';
  return 'rain';
}

function weatherIconSvg(code) {
  var kind = weatherKind(code);
  return '<svg class="wx wx-' + kind + '" viewBox="0 0 24 24" aria-hidden="true">' + WEATHER_ICONS[kind] + '</svg>';
}

function snowFmt(n, d) {
  if (n == null || isNaN(n)) return '–';
  n = n + 0; // -0 (e.g. Math.round(-0.4)) would print as "-0"
  return n.toLocaleString(SNOW_LOCALE, { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 });
}

// cm with one decimal below 1 cm, whole cm above ("0,4 cm", "12 cm").
function snowCm(cm) {
  if (cm == null || isNaN(cm)) return '–';
  if (cm <= 0.05) return '0 cm';
  return snowFmt(cm, cm < 1 ? 1 : 0) + ' cm';
}

// Resolves to null on any failure, so callers can simply hide the widget.
function fetchSnowForecast(lat, lon, topM, baseM) {
  var twoPoints = topM != null && baseM != null && topM - baseM >= 50;
  var params = [
    'latitude=' + (twoPoints ? lat + ',' + lat : lat),
    'longitude=' + (twoPoints ? lon + ',' + lon : lon),
    'current=temperature_2m,wind_speed_10m,weather_code',
    'hourly=snowfall,snow_depth,freezing_level_height',
    'daily=weather_code,temperature_2m_max,temperature_2m_min,snowfall_sum,wind_speed_10m_max',
    'past_days=1', 'forecast_days=7', 'timezone=auto'
  ];
  if (twoPoints) params.push('elevation=' + Math.round(topM) + ',' + Math.round(baseM));
  else if (topM != null) params.push('elevation=' + Math.round(topM));
  // The station screen waits for this, so never let a slow or stalled
  // Open-Meteo response hold it up: give up after a few seconds.
  var ctrl = typeof AbortController === 'function' ? new AbortController() : null;
  var timeout = new Promise(function (resolve) {
    setTimeout(function () { if (ctrl) ctrl.abort(); resolve(null); }, SNOW_FETCH_TIMEOUT_MS);
  });
  var request = fetch('https://api.open-meteo.com/v1/forecast?' + params.join('&'), ctrl ? { signal: ctrl.signal } : undefined)
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (data) {
      if (!data) return null;
      var top = Array.isArray(data) ? data[0] : data;
      var base = Array.isArray(data) ? data[1] : null;
      return parseSnowForecast(top, base, topM, twoPoints ? baseM : null);
    })
    .catch(function (err) { console.error('forecast fetch failed', err); return null; });
  return Promise.race([request, timeout]);
}
var SNOW_FETCH_TIMEOUT_MS = 5000;

function parseSnowForecast(top, base, topM, baseM) {
  if (!top || !top.daily || !top.hourly || !top.current) return null;
  var h = top.hourly, d = top.daily, c = top.current;
  var nowHour = (c.time || '').slice(0, 13);
  var idx = h.time.findIndex(function (t) { return t.slice(0, 13) === nowHour; });
  if (idx < 0) idx = Math.min(h.time.length - 1, 24);
  var last24 = 0;
  for (var i = Math.max(0, idx - 23); i <= idx; i++) last24 += h.snowfall[i] || 0;
  var todayIdx = d.time.indexOf((c.time || '').slice(0, 10));
  if (todayIdx < 0) todayIdx = 1;
  var days = [];
  for (var j = todayIdx; j < d.time.length; j++) {
    days.push({
      date: d.time[j],
      snow: d.snowfall_sum[j],
      tmax: d.temperature_2m_max[j],
      tmin: d.temperature_2m_min[j],
      wind: d.wind_speed_10m_max[j],
      code: d.weather_code[j],
      baseMax: base && base.daily ? base.daily.temperature_2m_max[j] : null,
      baseMin: base && base.daily ? base.daily.temperature_2m_min[j] : null
    });
  }
  var total = days.reduce(function (a, x) { return a + (x.snow || 0); }, 0);
  // current.time is local to the station; utc_offset_seconds turns it into a real instant.
  var fetched = new Date(Date.parse(c.time + ':00Z') - (top.utc_offset_seconds || 0) * 1000);
  return {
    topM: topM, baseM: baseM,
    now: {
      temp: c.temperature_2m, wind: c.wind_speed_10m, code: c.weather_code,
      baseTemp: base && base.current ? base.current.temperature_2m : null,
      baseWind: base && base.current ? base.current.wind_speed_10m : null,
      baseCode: base && base.current ? base.current.weather_code : null
    },
    last24: last24,
    depthCm: h.snow_depth[idx] != null ? h.snow_depth[idx] * 100 : null,
    freezingM: h.freezing_level_height[idx],
    days: days,
    total: total,
    fetched: isNaN(fetched.getTime()) ? null : fetched
  };
}

function snowDayLabel(iso, i) {
  if (i === 0) return T('Hoy');
  // "Tomorrow" doesn't fit the narrow day column: English uses the weekday.
  if (i === 1 && SNOW_LOCALE.indexOf('es') === 0) return T('Mañana');
  var dt = new Date(iso + 'T12:00:00Z');
  var wd = dt.toLocaleDateString(SNOW_LOCALE, { weekday: 'short', timeZone: 'UTC' }).replace('.', '');
  return wd.charAt(0).toUpperCase() + wd.slice(1) + ' ' + dt.getUTCDate();
}

function snowHeadline(fc) {
  var t = fc.total;
  if (t >= 30) return T('Gran nevada prevista');
  if (t >= 10) return T('Nieve en camino');
  if (t >= 1) return T('Alguna nevada débil');
  return T('Sin nevadas a la vista');
}

// Fills `container` with the whole widget (empties it when there's no data).
function renderSnowForecast(container, fc) {
  container.innerHTML = '';
  if (!fc || !fc.days.length) return;
  var el = function (tag, cls, html) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  };
  var elev = function (m) { return m != null ? snowFmt(Math.round(m)) + ' m' : ''; };

  var head = el('div', 'snow-head');
  head.appendChild(el('div', 'snow-head-icon', weatherIconSvg(fc.now.code)));
  var ht = el('div', 'snow-head-txt');
  ht.appendChild(el('div', 'snow-head-title', snowHeadline(fc)));
  var nowParts = [];
  nowParts.push(T('Ahora {0}° en cota alta', snowFmt(Math.round(fc.now.temp))) + (fc.topM != null ? ' (' + elev(fc.topM) + ')' : ''));
  if (fc.now.baseTemp != null) nowParts.push(T('{0}° en la base', snowFmt(Math.round(fc.now.baseTemp))));
  ht.appendChild(el('div', 'snow-head-sub', nowParts.join(' · ') + ' · ' + (WEATHER_CODE[fc.now.code] || '')));
  head.appendChild(ht);
  container.appendChild(head);

  var tiles = el('div', 'snow-tiles');
  [
    [snowCm(fc.total), T('Nieve próximos 7 días')],
    [snowCm(fc.last24), T('Nieve últimas 24 h')],
    [fc.depthCm != null ? snowCm(fc.depthCm) : '–', T('Espesor estimado')],
    [fc.freezingM != null ? elev(Math.round(fc.freezingM / 50) * 50) : '–', T('Isoterma 0 °C')]
  ].forEach(function (t, i) {
    var tile = el('div', 'snow-tile' + (i === 0 && fc.total >= 1 ? ' hot' : ''));
    tile.appendChild(el('div', 'v', t[0]));
    tile.appendChild(el('div', 'k', t[1]));
    tiles.appendChild(tile);
  });
  container.appendChild(tiles);

  var maxSnow = Math.max(10, Math.max.apply(null, fc.days.map(function (x) { return x.snow || 0; })));
  var strip = el('div', 'snow-days');
  fc.days.forEach(function (day, i) {
    var col = el('div', 'snow-day');
    col.title = WEATHER_CODE[day.code] || '';
    col.appendChild(el('div', 'snow-day-name', snowDayLabel(day.date, i)));
    col.appendChild(el('div', 'snow-day-icon', weatherIconSvg(day.code)));
    var barWrap = el('div', 'snow-bar-wrap');
    var bar = el('div', 'snow-bar');
    bar.style.height = (day.snow > 0.05 ? Math.max(6, (day.snow / maxSnow) * 100) : 0) + '%';
    barWrap.appendChild(bar);
    col.appendChild(barWrap);
    col.appendChild(el('div', 'snow-day-cm' + (day.snow > 0.05 ? '' : ' zero'), day.snow > 0.05 ? snowCm(day.snow) : '0'));
    col.appendChild(el('div', 'snow-day-t', '<b>' + snowFmt(Math.round(day.tmax)) + '°</b> ' + snowFmt(Math.round(day.tmin)) + '°'));
    if (day.baseMax != null) col.appendChild(el('div', 'snow-day-tb', snowFmt(Math.round(day.baseMax)) + '° ' + snowFmt(Math.round(day.baseMin)) + '°'));
    col.appendChild(el('div', 'snow-day-w', snowFmt(Math.round(day.wind)) + ' km/h'));
    strip.appendChild(col);
  });
  container.appendChild(strip);

  var legend = T('Temperaturas máx./mín.: arriba en cota alta') + (fc.topM != null ? ' (' + elev(fc.topM) + ')' : '')
    + (fc.days[0].baseMax != null ? T(', debajo en la base ({0})', elev(fc.baseM)) : '') + T('; viento máximo del día.');
  container.appendChild(el('p', 'snow-note', legend));
  var when = fc.fetched ? fc.fetched.toLocaleTimeString(SNOW_LOCALE, { hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Madrid' }) : '';
  container.appendChild(el('p', 'snow-note', T('Previsión de modelos meteorológicos ({0})', '<a href="https://open-meteo.com/" target="_blank" rel="noopener">Open-Meteo</a>')
    + (when ? T(', actualizada a las {0}', when) : '') + T('. El espesor es una estimación del modelo, no el parte oficial de la estación.')));
}

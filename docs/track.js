// Anonymous usage stats, shared by the app (index.html) and every generated
// page (stations, guides, countries, /app). Events are written straight to
// Firestore's REST API; its security rules (firestore.rules) allow
// create-only from here, and reading needs the owner's Google sign-in on
// stats.html. No cookies and nothing personal: a random per-install id kept
// in localStorage, a session id, where the visit came from (the referring
// site, not what anyone searched for), the device's time zone (for the
// country, without any IP lookup), and which stations/pages were opened.
//
// A session is shared by every page and tab of the same browser: it only
// starts again after 30 minutes without activity, so moving from a guide to
// a station page (or reloading) doesn't count as a new visit.
var SkiTrack = (function () {
  var PROJECT = 'ski-info-9910e';
  var ENDPOINT = 'https://firestore.googleapis.com/v1/projects/' + PROJECT + '/databases/(default)/documents:commit';
  var DOC_PREFIX = 'projects/' + PROJECT + '/databases/(default)/documents/events/';
  var RETENTION_DAYS = 395;
  var SESSION_GAP_MS = 30 * 60 * 1000;
  var FLUSH_EVERY_MS = 10 * 60 * 1000;
  // Fields older Firestore rules don't know about: dropped on a rejected write.
  var NEW_FIELDS = ['src', 'ref', 'lp', 'tz'];
  var ua = navigator.userAgent || '';
  var disabled = !/(^|\.)skiinfoapp\.com$|\.github\.io$/.test(location.hostname);
  // Android's WebView user agent carries "; wv)" -- that's the Play Store app.
  var platform = /; wv\)/.test(ua) ? 'android' : 'web';

  function randomId(len) {
    var chars = 'abcdefghijklmnopqrstuvwxyz0123456789', out = '';
    var bytes = new Uint8Array(len);
    (window.crypto || window.msCrypto).getRandomValues(bytes);
    for (var i = 0; i < len; i++) out += chars[bytes[i] % chars.length];
    return out;
  }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }

  var uid = store('si_uid'), isNew = false;
  if (!uid) { uid = randomId(20); isNew = true; store('si_uid', uid); }

  // ---- where the visit came from ----
  var SOURCES = [
    [/(^|\.)google\./, 'google'], [/(^|\.)bing\.com$/, 'bing'], [/(^|\.)duckduckgo\.com$/, 'duckduckgo'],
    [/(^|\.)yahoo\./, 'yahoo'], [/(^|\.)ecosia\.org$/, 'ecosia'], [/(^|\.)qwant\.com$/, 'qwant'],
    [/(^|\.)(facebook\.com|fb\.me|fb\.com)$/, 'facebook'], [/(^|\.)instagram\.com$/, 'instagram'],
    [/(^|\.)(t\.co|twitter\.com|x\.com)$/, 'x'], [/(^|\.)reddit\.com$/, 'reddit'], [/(^|\.)nevasport\.com$/, 'nevasport'],
    [/(^|\.)(whatsapp\.com|wa\.me)$/, 'whatsapp'], [/(^|\.)(t\.me|telegram\.org)$/, 'telegram'],
    [/(^|\.)linkedin\.com$/, 'linkedin'], [/(^|\.)tiktok\.com$/, 'tiktok'], [/(^|\.)youtube\.com$/, 'youtube'],
    [/(^|\.)skiinfoapp\.com$/, 'interna']
  ];
  var ANDROID_APPS = {
    'com.whatsapp': 'whatsapp', 'org.telegram.messenger': 'telegram', 'com.google.android.googlequicksearchbox': 'google',
    'com.google.android.gm': 'gmail', 'com.facebook.katana': 'facebook', 'com.instagram.android': 'instagram',
    'com.reddit.frontpage': 'reddit', 'com.twitter.android': 'x'
  };
  function detectSource() {
    var q = {};
    location.search.replace(/^\?/, '').split('&').forEach(function (kv) {
      var i = kv.indexOf('=');
      if (i > 0) { try { q[kv.slice(0, i)] = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, ' ')); } catch (e) {} }
    });
    var r = document.referrer || '', refHost = '';
    var m = /^[a-z-]+:\/\/([^\/?#]+)/i.exec(r);
    if (m) refHost = m[1].toLowerCase().replace(/^www\./, '');
    var tag = q.ref || q.utm_source;
    if (tag) return { src: 'tag:' + tag.toLowerCase().replace(/[^a-z0-9_.-]/g, '').slice(0, 30), ref: refHost };
    if (q.fuente === 'app-instalada' || navigator.standalone === true
        || (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches)) return { src: 'pwa' };
    if (platform === 'android') return { src: 'app' };
    if (/^android-app:\/\//i.test(r)) return { src: ANDROID_APPS[refHost] || 'app:' + refHost.slice(0, 30), ref: refHost };
    if (refHost) {
      for (var i = 0; i < SOURCES.length; i++) if (SOURCES[i][0].test(refHost)) return { src: SOURCES[i][1], ref: refHost };
      return { src: 'web', ref: refHost };
    }
    if (/FBAN|FBAV|FB_IAB/.test(ua)) return { src: 'facebook' };
    if (/Instagram/.test(ua)) return { src: 'instagram' };
    return { src: 'directo' };
  }

  // ---- sending ----
  function post(fields, urgent, onRejected) {
    var body = JSON.stringify({ writes: [{
      update: { name: DOC_PREFIX + randomId(20), fields: fields },
      updateTransforms: [{ fieldPath: 'ts', setToServerValue: 'REQUEST_TIME' }],
      currentDocument: { exists: false }
    }] });
    // keepalive (so the request survives the page closing) only where it's
    // needed; older Chromium rejects keepalive on requests that need a CORS
    // preflight, so fall back to a plain request then.
    var opts = { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body };
    function check(res) { if (res && res.status === 403 && onRejected) onRejected(); }
    function plain() { try { return fetch(ENDPOINT, opts).then(check, function () {}); } catch (e) {} }
    if (!urgent) { plain(); return; }
    try { fetch(ENDPOINT, Object.assign({ keepalive: true }, opts)).then(check, plain); } catch (e) { plain(); }
  }
  function send(type, extra, urgent) {
    if (disabled) return;
    touch();
    var fields = {
      type: { stringValue: type }, uid: { stringValue: uid }, sid: { stringValue: sid },
      platform: { stringValue: platform },
      exp: { timestampValue: new Date(Date.now() + RETENTION_DAYS * 86400000).toISOString() }
    };
    var hasNew = false;
    Object.keys(extra || {}).forEach(function (k) {
      var v = extra[k];
      if (v == null || v === '') return;
      if (NEW_FIELDS.indexOf(k) !== -1) hasNew = true;
      if (typeof v === 'number') fields[k] = { integerValue: String(Math.round(v)) };
      else if (typeof v === 'boolean') fields[k] = { booleanValue: v };
      else fields[k] = { stringValue: String(v).slice(0, k === 'name' ? 200 : 120) };
    });
    // Until the new Firestore rules are published, retry without the new
    // fields rather than lose the event.
    post(fields, urgent, hasNew && type !== 'page' ? function () {
      NEW_FIELDS.forEach(function (k) { delete fields[k]; });
      post(fields, urgent);
    } : null);
  }

  // ---- session (shared across pages and tabs) ----
  var sid, activeMs = 0, visibleSince = null;
  function touch() { store('si_last', String(Date.now())); }
  function startSession(src) {
    sid = randomId(16);
    store('si_sid', sid);
    touch();
    activeMs = 0;
    visibleSince = document.hidden ? null : Date.now();
    var tz = '';
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
    send('open', { isNew: isNew, lang: (navigator.language || '').slice(0, 10), src: src.src, ref: src.ref, lp: location.pathname, tz: tz.slice(0, 40) });
    isNew = false;
  }
  function sessionAlive() {
    var last = Number(store('si_last') || 0);
    return store('si_sid') && Date.now() - last < SESSION_GAP_MS;
  }
  function flushTime() {
    if (visibleSince != null) { activeMs += Date.now() - visibleSince; visibleSince = null; }
    var secs = Math.round(activeMs / 1000);
    activeMs = 0;
    if (secs > 0) send('time', { secs: Math.min(secs, 86400) }, true);
  }

  if (sessionAlive()) {
    sid = store('si_sid');
    visibleSince = document.hidden ? null : Date.now();
    touch();
  } else {
    startSession(detectSource());
  }
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { flushTime(); touch(); return; }
    if (!sessionAlive()) startSession({ src: platform === 'android' ? 'app' : 'reanudada' });
    else { sid = store('si_sid') || sid; visibleSince = Date.now(); touch(); }
  });
  window.addEventListener('pagehide', flushTime);
  setInterval(function () {
    if (document.hidden) return;
    flushTime();
    visibleSince = Date.now();
  }, FLUSH_EVERY_MS);

  function stationFields(id, name, country) { return { station: id, name: name, country: country }; }
  var api = {
    station: function (id, name, country) { send('station', stationFields(id, name, country)); },
    map: function (id, name, country) { send('map', stationFields(id, name, country)); },
    booking: function (id, name, country) { send('booking', stationFields(id, name, country)); },
    fav: function (id, name, country) { send('fav', stationFields(id, name, country)); },
    // Any other page (guides, countries, /app): which one, for the stats.
    page: function () { send('page', { lp: location.pathname }); }
  };
  // <script src="/track.js" data-page>: a plain page view (guides, countries...).
  if (document.currentScript && document.currentScript.hasAttribute('data-page')) api.page();
  return api;
})();

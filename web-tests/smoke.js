// Smoke test for the web app (docs/): the homes in every language, a station
// on a phone and on desktop (map preview, map, runs list), the stats demo, and
// the usage counter (counts people, skips robots). Run it before pushing.
//
//   cd docs && python3 -m http.server 8903 &                        # serve docs/
//   python3 data-pipeline/scripts/build_seo_pages.py --inject-home   # optional: /en/ /fr/ /de/ /it/ /nl/ /pl/ and static pages
//   NODE_PATH=/opt/node22/lib/node_modules node web-tests/smoke.js
//
// Every request outside the local server is blocked (as in the sandbox), and
// Open-Meteo is answered with a fake forecast so stations load as in production.
const { chromium, devices } = require('playwright');
const fs = require('fs'), path = require('path');

const BASE = process.env.BASE || 'http://localhost:8903';
const DOCS = path.join(__dirname, '..', 'docs');
const BAQUEIRA = '125d02338620dc079d5d635595a099370161bf83';
const CHROMIUM = process.env.CHROMIUM || '/opt/pw-browsers/chromium';

let failures = 0;
function check(ok, label, detail) {
  console.log((ok ? 'ok    ' : 'FAIL  ') + label + (detail ? '  (' + detail + ')' : ''));
  if (!ok) failures++;
}

// A 7-day forecast in Open-Meteo's shape, for one or several points.
function mockMeteo(url) {
  const u = new URL(url);
  const n = u.searchParams.get('latitude').split(',').length;
  const today = new Date(); const iso = (d) => d.toISOString().slice(0, 10);
  const days = []; for (let i = -1; i < 7; i++) { const d = new Date(today); d.setUTCDate(d.getUTCDate() + i); days.push(iso(d)); }
  const hours = []; days.forEach((d) => { for (let h = 0; h < 24; h++) hours.push(d + 'T' + String(h).padStart(2, '0') + ':00'); });
  const nowT = iso(today) + 'T' + String(today.getUTCHours()).padStart(2, '0') + ':00';
  const mk = (k) => ({
    utc_offset_seconds: 7200,
    current: { time: nowT, temperature_2m: -4 + k, wind_speed_10m: 22, weather_code: 73 },
    hourly: { time: hours, snowfall: hours.map((_, i) => (i > 10 && i < 30 ? 0.6 : 0)), snow_depth: hours.map(() => 0.85), freezing_level_height: hours.map(() => 1850) },
    daily: { time: days, weather_code: [71, 73, 75, 3, 0, 2, 85, 45], temperature_2m_max: days.map((_, i) => -2 + i), temperature_2m_min: days.map((_, i) => -9 + i),
      snowfall_sum: [8, 12.4, 25, 0.3, 0, 0, 6, 0], wind_speed_10m_max: [30, 45, 60, 20, 10, 15, 25, 18] }
  });
  const arr = Array.from({ length: n }, (_, k) => mk(k));
  return JSON.stringify(n === 1 ? arr[0] : arr);
}

async function newPage(browser, opts) {
  const ctx = await browser.newContext({ ...opts, serviceWorkers: 'block' });
  await ctx.route('**/*', (route) => {
    const url = route.request().url();
    if (url.includes('api.open-meteo.com')) return route.fulfill({ status: 200, contentType: 'application/json', body: mockMeteo(url) });
    return url.startsWith(BASE) ? route.continue() : route.abort();
  });
  const page = await ctx.newPage();
  page.errors = [];
  page.on('pageerror', (e) => page.errors.push(String(e)));
  return page;
}

async function exists(p) {
  try { const r = await fetch(BASE + p); return r.ok; } catch (e) { return false; }
}

(async () => {
  if (!(await exists('/'))) { console.error('No server at ' + BASE + ' (cd docs && python3 -m http.server 8903)'); process.exit(2); }
  // Software WebGL, for the 3D map.
  const browser = await chromium.launch({ executablePath: CHROMIUM, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });

  // ---- homes ----
  for (const lang of ['', 'en/', 'fr/', 'de/', 'it/', 'nl/', 'pl/']) {
    if (lang && !(await exists('/' + lang))) { console.log('skip  /' + lang + ' (not built: run build_seo_pages.py --inject-home)'); continue; }
    const p = await newPage(browser, devices['Pixel 7']);
    await p.goto(BASE + '/' + lang); await p.waitForTimeout(1200);
    const info = await p.evaluate(() => ({
      search: !!document.getElementById('global-search'),
      picker: !!document.querySelector('.lang-picker'),
      lang: document.documentElement.lang
    }));
    check(info.search && info.picker && !p.errors.length, 'home /' + lang, 'lang=' + info.lang + (p.errors.length ? ' errors: ' + p.errors.join(' | ') : ''));
    await p.context().close();
  }

  // ---- home for a first visit: popular stations in the hero, nearest ones by time zone ----
  {
    const p = await newPage(browser, { ...devices['Pixel 7'], timezoneId: 'Europe/Madrid' });
    await p.goto(BASE + '/'); await p.waitForTimeout(1200);
    const chips = await p.$$eval('#home-popular button', (b) => b.map((x) => x.textContent));
    const near = await p.$$eval('#near-list .station-card', (c) => c.length);
    check(chips.length >= 4 && near === 6, 'home: popular chips and "Cerca de ti"', chips.join(', ') + ' · ' + near + ' near');
    await p.click('#home-popular button');
    await p.waitForSelector('#screen-dashboard:not([hidden])', { timeout: 8000 }).catch(() => {});
    check(await p.$eval('#screen-dashboard', (e) => !e.hidden), 'home: a popular chip opens its station');
    await p.context().close();
  }

  // ---- station on a phone ----
  {
    const p = await newPage(browser, devices['Pixel 7']);
    await p.goto(BASE + '/?estacion=' + BAQUEIRA);
    await p.waitForSelector('#runs-list .run-item', { timeout: 15000 }).catch(() => {});
    await p.waitForTimeout(500);
    const s = await p.evaluate(() => ({
      name: document.getElementById('h-name').textContent,
      runs: document.querySelectorAll('#runs-list .run-item').length,
      preview: !document.getElementById('map-preview-section').hidden,
      previewPaths: document.querySelectorAll('#map-preview-art path').length,
      previewTiles: document.querySelectorAll('#map-preview-art image').length,
      sub: document.getElementById('map-preview-sub').textContent
    }));
    check(s.runs > 50 && /Baqueira/.test(s.name), 'phone station: hero and runs list', s.name + ', ' + s.runs + ' runs');
    check(s.preview && s.previewPaths > 50 && s.previewTiles > 0, 'phone station: map preview card', s.previewPaths + ' paths, ' + s.previewTiles + ' tiles, "' + s.sub + '"');
    await p.click('#map-preview'); await p.waitForTimeout(600);
    const map = await p.evaluate(() => ({ visible: !document.getElementById('pane-map').hidden, lines: document.querySelectorAll('#map-svg polyline').length }));
    check(map.visible && map.lines > 50, 'phone station: preview opens the map', map.lines + ' polylines');
    await p.tap('#map-mode button[data-mode=slope]'); await p.waitForTimeout(400);
    const slope = await p.evaluate(() => ({
      on: document.getElementById('map-svg').classList.contains('slope-mode'),
      groups: document.querySelectorAll('.map-slope').length, runs: document.querySelectorAll('.map-run').length,
      colours: new Set([...document.querySelectorAll('.map-slope polyline')].map((e) => e.style.stroke)).size
    }));
    check(slope.on && slope.groups === slope.runs && slope.colours >= 3, 'phone station: map coloured by real slope', slope.groups + ' runs, ' + slope.colours + ' colours');
    await p.tap('#map-mode button[data-mode=diff]');
    check(!p.errors.length, 'phone station: no JS errors', p.errors.join(' | '));
    await p.context().close();
  }

  // ---- "where am I" on the piste map ----
  {
    const p = await newPage(browser, { ...devices['Pixel 7'], permissions: ['geolocation'], geolocation: { latitude: 42.68642, longitude: 0.97727, accuracy: 15 } });
    await p.goto(BASE + '/?estacion=' + BAQUEIRA + '&vista=mapa');
    await p.waitForSelector('#map-svg polyline', { timeout: 15000 }).catch(() => {});
    await p.tap('#map-locate'); await p.waitForTimeout(1200);
    const loc = await p.evaluate(() => ({ dot: document.querySelectorAll('.map-loc-dot').length, msg: document.getElementById('map-loc-msg').textContent }));
    check(loc.dot === 1 && /Muguet/.test(loc.msg), 'phone station: "where am I" shows the position and the run you are on', loc.msg);
    await p.context().close();
  }

  // ---- station on desktop ----
  {
    const p = await newPage(browser, { viewport: { width: 1440, height: 900 } });
    await p.goto(BASE + '/?estacion=' + BAQUEIRA);
    await p.waitForSelector('#runs-list .run-item', { timeout: 15000 }).catch(() => {});
    await p.waitForTimeout(800);
    const d = await p.evaluate(() => ({
      lines: document.querySelectorAll('#map-svg polyline').length,
      previewShown: getComputedStyle(document.getElementById('map-preview-section')).display !== 'none'
    }));
    check(d.lines > 50 && !d.previewShown, 'desktop station: map beside the info, no preview card', d.lines + ' polylines');
    await p.click('#runs-list .run-item'); await p.waitForTimeout(800);
    const prof = await p.$('#map-run-panel svg');
    if (prof) {
      const pb = await prof.boundingBox();
      await p.mouse.move(pb.x + pb.width * 0.5, pb.y + pb.height * 0.6); await p.waitForTimeout(150);
    }
    const scrub = await p.evaluate(() => ({
      text: (document.querySelector('#map-run-panel svg g[pointer-events] text') || {}).textContent || '',
      marker: !!document.querySelector('.map-profile-point:not([display="none"])')
    }));
    check(/m · \d+ m · \d+%/.test(scrub.text) && scrub.marker, 'desktop station: sliding along a profile shows the point and marks it on the map', scrub.text);
    check(!p.errors.length, 'desktop station: no JS errors', p.errors.join(' | '));
    await p.context().close();
  }

  // ---- 3D map: opens over the 2D map and closes again ----
  // (Terrain and imagery tiles are blocked here: it draws the runs on a flat dark ground.)
  {
    const p = await newPage(browser, devices['Pixel 7']);
    await p.goto(BASE + '/?estacion=' + BAQUEIRA + '&vista=mapa');
    await p.waitForSelector('#map-svg polyline', { timeout: 15000 }).catch(() => {});
    const shown = await p.$eval('#map-3d-btn', (e) => !e.hidden);
    await p.tap('#map-3d-btn');
    await p.waitForSelector('#map-3d canvas', { timeout: 15000 }).catch(() => {});
    await p.waitForFunction(() => document.getElementById('map-3d-msg').hidden, null, { timeout: 20000 }).catch(() => {});
    const on = await p.evaluate(() => ({ canvas: !!document.querySelector('#map-3d canvas'), btn: document.getElementById('map-3d-btn').textContent,
      spin: !document.getElementById('map-3d-spin').hidden, msg: document.getElementById('map-3d-msg').hidden }));
    await p.tap('#map-3d-btn'); await p.waitForTimeout(300);
    const off = await p.evaluate(() => !document.querySelector('#map-3d canvas') && document.getElementById('map-3d').hidden);
    check(shown && on.canvas && on.btn === '2D' && on.spin && on.msg && off && !p.errors.length,
          '3D map: button shown, opens and closes', JSON.stringify(on) + (p.errors.length ? ' errors: ' + p.errors.join(' | ') : ''));
    await p.context().close();
  }

  // ---- route planner (hidden behind ?rutas=1): a route from a tapped point to a run ----
  {
    const p = await newPage(browser, { viewport: { width: 1440, height: 900 } });
    await p.goto(BASE + '/?rutas=1&estacion=' + BAQUEIRA);
    await p.waitForSelector('#runs-list .run-item', { timeout: 15000 }).catch(() => {});
    await p.click('#runs-list .run-item >> nth=3'); await p.waitForTimeout(400);
    await p.click('#map-run-panel .map-route-btn').catch(() => {});
    // Start: a tap on a lift on the map, clear of the route panel.
    await p.waitForSelector('.route-place-hint', { timeout: 10000 }).catch(() => {});
    const lp = await p.evaluate(() => {
      const pr = document.getElementById('map-run-panel').getBoundingClientRect();
      for (const e of document.querySelectorAll('.map-lift')) {
        const q = e.getPointAtLength(e.getTotalLength() / 2), m = e.getScreenCTM();
        const x = m.a * q.x + m.c * q.y + m.e, y = m.b * q.x + m.d * q.y + m.f;
        if (x > 500 && y > 150 && y < innerHeight - 40 && x < pr.left - 20 && document.elementFromPoint(x, y)) return [x, y];
      }
    });
    if (lp) await p.mouse.click(lp[0], lp[1]);
    await p.waitForSelector('.route-summary', { timeout: 10000 }).catch(() => {});
    const r = await p.evaluate(() => ({ sum: (document.querySelector('.route-summary') || {}).textContent || '', steps: document.querySelectorAll('.route-steps li').length, drawn: document.querySelectorAll('.map-route-line').length }));
    check(/min/.test(r.sum) && r.steps >= 3 && r.drawn > 0 && !p.errors.length, 'route planner: a route from a tapped point to a run', r.sum + ' · ' + r.steps + ' steps' + (p.errors.length ? ' errors: ' + p.errors.join(' | ') : ''));
    await p.context().close();
  }

  // ---- generated station page ----
  if (await exists('/estacion/baqueira-beret/')) {
    const p = await newPage(browser, devices['Pixel 7']);
    await p.goto(BASE + '/estacion/baqueira-beret/'); await p.waitForTimeout(800);
    const t = await p.title();
    check(/Baqueira/.test(t) && !p.errors.length, 'static page /estacion/baqueira-beret/', t);
    // A station shared from the app's map (#mapa) opens straight on the map.
    await p.goto('about:blank'); await p.goto(BASE + '/estacion/baqueira-beret/#mapa');
    await p.waitForSelector('#pane-map:not([hidden]) #map-svg polyline', { timeout: 15000 }).catch(() => {});
    check(await p.evaluate(() => !document.getElementById('pane-map').hidden && document.querySelectorAll('#map-svg polyline').length > 50),
      'static page #mapa opens the station map', p.url());
    await p.context().close();
  } else console.log('skip  static pages (not built)');

  // ---- stats demo ----
  {
    const p = await newPage(browser, { viewport: { width: 1000, height: 900 } });
    await p.goto(BASE + '/stats.html?demo=1'); await p.waitForTimeout(1500);
    const st = await p.evaluate(() => ({ dash: !document.getElementById('dash').hidden, users: document.querySelectorAll('details.user').length }));
    check(st.dash && st.users > 0 && !p.errors.length, 'stats.html?demo=1', st.users + ' users listed' + (p.errors.length ? ' errors: ' + p.errors.join(' | ') : ''));
    await p.context().close();
  }

  // ---- usage counter (only runs on skiinfoapp.com: served from docs/ under that host) ----
  const UA = {
    person: 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36',
    googlebot: 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/129.0 Safari/537.36'
  };
  for (const who of ['person', 'googlebot']) {
    const ctx = await browser.newContext({ userAgent: UA[who], timezoneId: 'Europe/Madrid', serviceWorkers: 'block' });
    // Playwright sets navigator.webdriver, which the counter treats as a robot.
    await ctx.addInitScript(() => Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false }));
    const sent = [];
    await ctx.route('**/*', (route) => {
      const url = route.request().url();
      if (url.startsWith('https://skiinfoapp.com/')) {
        let rel = decodeURIComponent(new URL(url).pathname); if (rel.endsWith('/')) rel += 'index.html';
        const f = path.join(DOCS, rel);
        const type = f.endsWith('.js') ? 'text/javascript' : f.endsWith('.json') ? 'application/json' : f.endsWith('.css') ? 'text/css' : 'text/html';
        return fs.existsSync(f) ? route.fulfill({ status: 200, contentType: type, body: fs.readFileSync(f) }) : route.fulfill({ status: 404, body: '' });
      }
      if (url.includes('firestore.googleapis.com') && route.request().method() === 'POST') {
        sent.push(JSON.parse(route.request().postData()).writes[0].update.fields);
        return route.fulfill({ status: 200, contentType: 'application/json', body: '{}', headers: { 'access-control-allow-origin': '*' } });
      }
      if (url.includes('firestore.googleapis.com')) return route.fulfill({ status: 204, headers: { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*' } });
      return route.abort();
    });
    const p = await ctx.newPage();
    await p.goto('https://skiinfoapp.com/'); await p.waitForTimeout(1200);
    const open = sent.find((f) => f.type.stringValue === 'open');
    if (who === 'person') check(open && open.tz && open.tz.stringValue === 'Europe/Madrid', 'counter: a person\'s visit is recorded with its time zone', open ? JSON.stringify(Object.keys(open)) : 'no open event');
    else check(!sent.length, 'counter: Googlebot is not counted', sent.length + ' events');
    await ctx.close();
  }

  await browser.close();
  console.log(failures ? '\n' + failures + ' check(s) failed' : '\nall checks passed');
  process.exit(failures ? 1 : 0);
})();

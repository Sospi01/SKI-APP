// Horizontal screenshots for Reddit (3D map, Baqueira): (a) a run's slope profile, (b) a route.
// node marketing/make_shots.js <out dir>, env TILE_DIR (tiles via fetch-tiles.yml, list from TILE_LOG), FAKE_TILE, DEM_DIR; RUN, DEST, START, ONLY=a|b|ab.
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path'); const { execFile } = require('child_process');
const BASE = 'http://localhost:8903', BAQ = '125d02338620dc079d5d635595a099370161bf83';
const OUT = process.argv[2]; const RUN = process.env.RUN || 'Cara Nord'; const ONLY = process.env.ONLY || 'ab';
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const asked = new Set();
  async function newCtx() {
    const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1.5, serviceWorkers: 'block', locale: 'es-ES' });
    await ctx.route(/World_Imagery/, r => {
      const m = /\/tile\/(\d+)\/(\d+)\/(\d+)/.exec(r.request().url()); const key = m ? m.slice(1).join('_') : null;
      if (key) asked.add(key);
      const file = key && process.env.TILE_DIR && path.join(process.env.TILE_DIR, key + '.jpg');
      if (file && fs.existsSync(file)) return r.fulfill({ body: fs.readFileSync(file), contentType: 'image/jpeg', headers: { 'access-control-allow-origin': '*' } });
      return r.fulfill({ body: fs.readFileSync(process.env.FAKE_TILE), contentType: 'image/jpeg', headers: { 'access-control-allow-origin': '*' } });
    });
    const demDir = process.env.DEM_DIR; fs.mkdirSync(demDir, { recursive: true });
    await ctx.route('**/elevation-tiles-prod/**', async r => {
      const url = r.request().url(), m = /terrarium\/(\d+)\/(\d+)\/(\d+)\.png/.exec(url);
      if (!m) return r.continue();
      const file = path.join(demDir, m.slice(1).join('_') + '.png');
      if (!fs.existsSync(file)) await new Promise(res => execFile('curl', ['-sSf', '--retry', '3', '-o', file, url], () => res()));
      if (!fs.existsSync(file)) return r.fulfill({ status: 404, headers: { 'access-control-allow-origin': '*' } });
      return r.fulfill({ body: fs.readFileSync(file), contentType: 'image/png', headers: { 'access-control-allow-origin': '*' } });
    });
    await ctx.route(/open-meteo|firestore|googleapis/, r => r.abort());
    await ctx.addInitScript(() => {
      try { localStorage.setItem('si_lang', 'es'); localStorage.setItem('si_lang_hint', '1'); localStorage.setItem('si_3d_hint', '9');
        localStorage.setItem('si_install_hint', '1'); localStorage.setItem('si_fav_nudge', '9'); localStorage.setItem('si_route_level', 'all'); } catch (e) {}
      let real;
      Object.defineProperty(window, 'SkiMap3D', { configurable: true, get() { return real; },
        set(v) { real = Object.assign({}, v, { open(o) { const a = v.open(o); window.__m3d = a; return a; } }); } });
    });
    const p = await ctx.newPage(); p.on('pageerror', e => console.error('page error:', e.message));
    return p;
  }
  const idle = (p, max) => p.evaluate((max) => new Promise(res => { const m = window.__m3d.map; let d = false; const f = () => { if (!d) { d = true; res(); } };
    m.once('idle', f); setTimeout(f, max); }), max);
  async function open3d(p) {
    await p.click('#map-3d-btn');
    await p.waitForFunction(() => window.__m3d && window.__m3d.map && window.__m3d.map.isStyleLoaded(), null, { timeout: 120000 });
    await p.evaluate(() => { window.__m3d.map._fadeDuration = 0; });
    for (let i = 0; i < 3; i++) await idle(p, 15000);
  }
  const DATA = JSON.parse(fs.readFileSync('/home/user/SKI-APP/docs/data/' + BAQ + '.json', 'utf8'));
  async function tidy(p) { await p.addStyleTag({ content: '.fav-nudge, .toast, #map-hint { display: none !important; }' }); }
  async function fit(p, coords, pitch) {
    await p.evaluate(({ coords, pitch }) => {
      const m = window.__m3d.map, xs = coords.map(c => c[0]), ys = coords.map(c => c[1]);
      const cam = m.cameraForBounds([[Math.min(...xs), Math.min(...ys)], [Math.max(...xs), Math.max(...ys)]],
        { padding: { top: 90, bottom: 70, left: 70, right: 560 }, bearing: m.getBearing(), maxZoom: 15.5 });
      // Tilted: a little further out, since the far side recedes.
      m.jumpTo({ center: cam.center, zoom: cam.zoom - 0.35, bearing: m.getBearing(), pitch });
    }, { coords, pitch });
  }
  async function shot(p, file) {
    const b = await (await p.$('#map-3d')).boundingBox();
    await p.screenshot({ path: path.join(OUT, file), clip: { x: b.x, y: b.y, width: b.width, height: b.height } });
  }
  async function settle(p) { for (let i = 0; i < 3; i++) await idle(p, 15000); await p.waitForTimeout(1500); }

  if (ONLY.includes('a')) {   // (a) a run's profile with the 3D map
    const p = await newCtx();
    await p.goto(`${BASE}/?estacion=${BAQ}`);
    await p.waitForSelector('#runs-list .run-item', { timeout: 30000 });
    await p.waitForTimeout(1200);
    await p.locator('#runs-list .run-item', { hasText: RUN }).first().click();
    await p.waitForTimeout(1000);
    await tidy(p);
    await open3d(p);
    const runCoords = DATA.runs.filter(r => r.name === RUN).flatMap(r => r.geom.flat());
    if (process.env.MODE_SLOPE !== '0') await p.locator('button', { hasText: 'Pendiente' }).first().click().catch(() => {});
    await fit(p, runCoords, 60);
    await settle(p);
    const prof = await p.$('#map-run-panel .run-profile svg');
    if (prof) { const b = await prof.boundingBox(); await p.mouse.move(b.x + b.width * 0.45, b.y + b.height * 0.55); await p.waitForTimeout(600); }
    await settle(p);
    console.log('cam', await p.evaluate(() => { const m = window.__m3d.map; return [m.getPitch(), m.getZoom(), m.getBearing(), !!m.getTerrain()]; }));
    await shot(p, 'a-perfil-3d.png');
    await p.context().close();
  }
  if (ONLY.includes('b')) {   // (b) a route in 3D
    const p = await newCtx();
    await p.goto(`${BASE}/?estacion=${BAQ}`);
    await p.waitForSelector('#runs-list .run-item', { timeout: 30000 });
    await p.waitForTimeout(1200);
    await p.locator('#runs-list .run-item', { hasText: process.env.DEST || 'Bonaigua' }).first().click();
    await p.waitForTimeout(800);
    await p.click('#map-run-panel .map-route-btn');
    await p.waitForSelector('.route-place-hint', { timeout: 10000 }).catch(() => {});
    // Start: the middle of a lift chosen by name (the .map-lift lines follow raw.lifts' parts).
    await p.click('#map-zoom-reset').catch(() => {}); await p.waitForTimeout(1200);
    const START = process.env.START || 'TSD Blanhiblar';
    let idx = 0, want = -1;
    DATA.lifts.forEach(l => (l.geom || []).forEach(part => { if (part.length < 2) return; if (l.name === START && want < 0) want = idx; idx++; }));
    const lp = await p.evaluate((want) => {
      const e = document.querySelectorAll('.map-lift')[want];
      const q = e.getPointAtLength(e.getTotalLength() / 2), m = e.getScreenCTM();
      return [m.a * q.x + m.c * q.y + m.e, m.b * q.x + m.d * q.y + m.f];
    }, want);
    console.log('start at', lp, await p.evaluate(([x, y]) => { const e = document.elementFromPoint(x, y); return e ? e.tagName + '.' + e.getAttribute('class') : null; }, lp));
    if (lp) await p.mouse.click(lp[0], lp[1]);
    await p.waitForTimeout(1500); await p.screenshot({ path: path.join(OUT, 'debug.png') });
    await p.waitForSelector('.route-summary', { timeout: 15000 });
    await p.waitForTimeout(1000);
    await tidy(p);
    await open3d(p);
    const rc = await p.evaluate(() => window.__m3d.map.getSource('route').getData().then(d => d.features.flatMap(f => f.geometry.coordinates)));
    await fit(p, rc, 58);
    await settle(p);
    // The start/end markers are placed once; nudge the camera so they sit on the terrain now it's loaded.
    await p.evaluate(() => { const m = window.__m3d.map; m.panBy([2, 0], { duration: 0 }); m.panBy([-2, 0], { duration: 0 }); });
    await settle(p);
    await shot(p, 'b-ruta-3d.png');
    console.log('route:', await p.evaluate(() => document.querySelector('.route-summary').textContent));
    await p.context().close();
  }
  await browser.close();
  if (process.env.TILE_LOG) fs.writeFileSync(process.env.TILE_LOG, [...asked].sort().join('\n') + '\n');
  if (process.env.TILE_DIR) console.log('tiles asked', asked.size, 'missing', [...asked].filter(k => !fs.existsSync(path.join(process.env.TILE_DIR, k + '.jpg'))).length);
})().catch(e => { console.error(e); process.exit(1); });

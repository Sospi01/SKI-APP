// A vertical (1080x1920) "¿Qué estación de esquí es?" video for TikTok / Reels /
// Shorts: the station's 3D view (relief, runs and their names, as on the web)
// turning a full circle slowly over the satellite imagery, with the question
// on top, a clue and a call to comment. Always the same look: the texts are a
// fixed template (overlay PNGs) laid over the map by ffmpeg.
//
// Run in Claude's sandbox against docs/ served on localhost:8903; the whole
// procedure (tile list, tile download, frames, mp4) is marketing/make_video.sh.
//   node marketing/make_video.js --station <id> --hint "Pirineo aragonés" --out <dir>
//     --list-tiles N   only turn through N bearings and write TILE_LOG (quick)
// Writes <dir>/frames/0001.jpg... (the map alone, --fps a second, ffmpeg
// interpolates them to 30) and <dir>/overlay.png, <dir>/outro.png.
//
// Speed: WebGL is drawn in software here, so each frame is drawn exactly once:
// jump to the bearing, force a draw and read the map's canvas in that same
// step (a page screenshot drew it all again, 2-3 draws a frame).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');

const arg = (name, def) => { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : def; };
const STATION = arg('station');
const HINT = arg('hint', '');
const OUT = arg('out', 'out');
const SECONDS = +arg('seconds', 20);       // one full turn: 18 degrees a second
const FPS = +arg('fps', 12);               // drawn; ffmpeg interpolates to 30
const SCALE = +arg('scale', 1.5);          // map drawn at 810x1440, scaled to 1080x1920 by ffmpeg
const TITLE = arg('title', '¿Qué estación\nde esquí es?');
const CTA = arg('cta', 'Respuesta en los comentarios 👇');
const OUTRO = arg('outro', 'Mapa 3D de 1.400 estaciones · skiinfoapp.com');
const BASE = arg('base', 'http://localhost:8903');
const ZOOM = +arg('zoom', 0.6);            // closer than the default framing
const NAMES = arg('names', '1') !== '0';   // run and lift names, as on the web
const LIST = +arg('list-tiles', 0);
// --still <file.jpg>: one picture at the app's framing (the home's station
// images, docs/img/home/), no turn and no texts.
const STILL = arg('still', '');
const W = +arg('width', 540), H = +arg('height', 960);   // CSS px; x2 = 1080x1920

const OVERLAY_CSS = `
  html, body { margin: 0; background: transparent; }
  #o { position: fixed; inset: 0; font-family: 'Barlow Condensed', sans-serif; color: #fff; }
  #o .top { position: absolute; top: 0; left: 0; right: 0; padding: 70px 28px 60px; text-align: center;
    background: linear-gradient(rgba(0,0,0,0.62), rgba(0,0,0,0)); }
  #o .title { white-space: pre-line; font-size: 50px; font-weight: 700; line-height: 1.0; text-transform: uppercase; letter-spacing: 0.5px; text-shadow: 0 3px 14px rgba(0,0,0,0.7); }
  #o .hint { display: inline-block; margin-top: 16px; font-size: 27px; font-weight: 700; padding: 6px 16px; border-radius: 999px;
    background: rgba(255,255,255,0.18); border: 1.5px solid rgba(255,255,255,0.55); text-shadow: 0 2px 8px rgba(0,0,0,0.6); }
  /* Well above TikTok's caption, username and comment bar, which cover
     about the bottom quarter (the user saw the call to comment hidden). */
  #o .bottom { position: absolute; left: 0; right: 0; bottom: 0; padding: 70px 28px 300px; text-align: center;
    background: linear-gradient(rgba(0,0,0,0), rgba(0,0,0,0.45) 60%, rgba(0,0,0,0)); }
  #o .cta { font-size: 34px; font-weight: 700; text-shadow: 0 3px 12px rgba(0,0,0,0.7); }
  #o .credit { position: absolute; left: 0; right: 0; bottom: 268px; text-align: center; font-family: 'IBM Plex Sans', sans-serif;
    font-size: 10.5px; opacity: 0.75; }`;
const esc = t => t.replace(/&/g, '&amp;').replace(/</g, '&lt;');

// The texts, as transparent 1080x1920 PNGs: one with the call to comment, one
// with the closing line (the last 2.5 s).
async function overlays(browser) {
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  const fonts = fs.readFileSync(path.join(__dirname, '..', 'docs', 'index.html'), 'utf8').match(/@font-face[^}]*}/g).join('\n');
  for (const [file, bottom] of [['overlay.png', CTA], ['outro.png', OUTRO]]) {
    const html = `<!doctype html><meta charset="utf-8"><style>${fonts.replace(/font-display: optional/g, 'font-display: block')}${OVERLAY_CSS}</style>
      <div id="o"><div class="top"><div class="title">${esc(TITLE)}</div>${HINT ? `<div class="hint">${esc(HINT)}</div>` : ''}</div>
      <div class="bottom"><div class="cta">${esc(bottom)}</div></div>
      <div class="credit">© OpenStreetMap (ODbL) · OpenSkiMap · Esri, Maxar, Earthstar Geographics · Terrain Tiles</div></div>`;
    await page.route(BASE + '/__overlay', r => r.fulfill({ body: html, contentType: 'text/html' }));
    await page.goto(BASE + '/__overlay');
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: path.join(OUT, file), omitBackground: true });
    await page.unroute(BASE + '/__overlay');
  }
  await ctx.close();
}

(async () => {
  if (!STATION) throw new Error('--station is required');
  fs.mkdirSync(path.join(OUT, 'frames'), { recursive: true });
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || undefined,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  if (!LIST && !STILL) await overlays(browser);
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: SCALE, serviceWorkers: 'block', locale: 'es-ES' });
  // Satellite tiles: from a folder of downloaded tiles (TILE_DIR, files z_y_x.jpg,
  // fetched where the imagery is reachable), else a stand-in (FAKE_TILE), else the
  // network. TILE_LOG lists every tile asked for (to know which to download).
  const asked = new Set();
  if (process.env.TILE_DIR || process.env.FAKE_TILE || process.env.TILE_LOG) {
    await ctx.route('**/World_Imagery/**', r => {
      const m = /\/tile\/(\d+)\/(\d+)\/(\d+)/.exec(r.request().url());
      const key = m ? m.slice(1).join('_') : null;
      if (key) asked.add(key);
      const file = key && process.env.TILE_DIR && path.join(process.env.TILE_DIR, key + '.jpg');
      if (file && fs.existsSync(file)) return r.fulfill({ body: fs.readFileSync(file), contentType: 'image/jpeg', headers: { 'access-control-allow-origin': '*' } });
      if (process.env.FAKE_TILE) return r.fulfill({ body: fs.readFileSync(process.env.FAKE_TILE), contentType: 'image/png', headers: { 'access-control-allow-origin': '*' } });
      return r.continue();
    });
  }
  // Elevation tiles: fetched with curl into a cache folder and served from there
  // (Chromium here doesn't trust the sandbox proxy's certificate, so it got none
  // and the first video came out flat).
  const demDir = process.env.DEM_DIR || path.join(OUT, 'dem');
  fs.mkdirSync(demDir, { recursive: true });
  await ctx.route('**/elevation-tiles-prod/**', async r => {
    const url = r.request().url(), m = /terrarium\/(\d+)\/(\d+)\/(\d+)\.png/.exec(url);
    if (!m) return r.continue();
    const file = path.join(demDir, m.slice(1).join('_') + '.png');
    if (!fs.existsSync(file)) {
      await new Promise(res => execFile('curl', ['-sSf', '--retry', '3', '-o', file, url], () => res()));
    }
    if (!fs.existsSync(file)) return r.fulfill({ status: 404, headers: { 'access-control-allow-origin': '*' } });
    return r.fulfill({ body: fs.readFileSync(file), contentType: 'image/png', headers: { 'access-control-allow-origin': '*' } });
  });
  await ctx.route(/open-meteo|firestore|googleapis/, r => r.abort());
  await ctx.addInitScript(() => {
    try {
      localStorage.setItem('si_lang', 'es'); localStorage.setItem('si_lang_hint', '1'); localStorage.setItem('si_3d_hint', '9');
      localStorage.setItem('si_install_hint', '1'); localStorage.setItem('si_fav_nudge', '9');
    } catch (e) {}
    // Get hold of the 3D map (map3d.js returns its API from SkiMap3D.open).
    let real;
    Object.defineProperty(window, 'SkiMap3D', { configurable: true, get() { return real; },
      set(v) { real = Object.assign({}, v, { open(o) { const a = v.open(o); window.__m3d = a; return a; } }); } });
  });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto(`${BASE}/?estacion=${STATION}&vista=mapa`);
  await page.waitForSelector('#map-svg polyline', { timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.click('#map-3d-btn');
  await page.waitForFunction(() => window.__m3d && window.__m3d.map && window.__m3d.map.isStyleLoaded(), null, { timeout: 120000 });

  // Only the 3D map, full screen, no buttons.
  await page.addStyleTag({ content: `
    body * { visibility: hidden !important; }
    #map-3d, #map-3d * { visibility: visible !important; }
    #map-3d { position: fixed !important; inset: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 9998 !important; opacity: 1 !important; }
    #map-3d .maplibregl-control-container { display: none !important; }
  ` });

  // The camera: the app's own framing, a little closer. Names placed at once
  // (no fade), since each frame is a single draw.
  const startBearing = await page.evaluate(({ ZOOM, NAMES }) => {
    const m = window.__m3d.map;
    m.resize();
    m._fadeDuration = 0;
    if (!NAMES && m.getLayer('labels')) m.setLayoutProperty('labels', 'visibility', 'none');
    m.jumpTo({ zoom: m.getZoom() + ZOOM, pitch: 64 });
    return m.getBearing();
  }, { ZOOM, NAMES });
  const idle = (max) => page.evaluate((max) => new Promise(res => {
    const m = window.__m3d.map;
    let done = false;
    const finish = () => { if (!done) { done = true; res(); } };
    if (m.loaded() && m.areTilesLoaded()) { requestAnimationFrame(() => requestAnimationFrame(finish)); }
    m.once('idle', finish);
    setTimeout(finish, max);
  }), max);
  const turnTo = b => page.evaluate(b => window.__m3d.map.jumpTo({ bearing: b }), b);
  // Let the first view load fully (imagery and terrain), then warm the tile
  // cache all the way round, so each frame then only has to draw.
  await page.evaluate(() => window.__m3d.map.triggerRepaint());
  for (let i = 0; i < 3; i++) await idle(15000);
  const steps = STILL ? 0 : LIST || 8;
  for (let k = 1; k <= steps; k++) { await turnTo(startBearing + 360 / steps * k); await idle(15000); await idle(4000); }

  if (STILL) {
    await turnTo(startBearing);
    await idle(15000); await idle(4000);
    const jpg = await page.evaluate(() => { const m = window.__m3d.map; m.redraw(); return m.getCanvas().toDataURL('image/jpeg', 0.84); });
    fs.writeFileSync(STILL, Buffer.from(jpg.split(',')[1], 'base64'));
    console.log('still:', STILL);
  } else if (!LIST) {
    await turnTo(startBearing);
    await idle(15000);
    const t0 = Date.now();
    const total = Math.round(SECONDS * FPS);
    for (let f = 0; f < total; f++) {
      // Ease in and out over the full turn, so the loop doesn't jerk.
      const t = f / total, e = t - Math.sin(2 * Math.PI * t) / (2 * Math.PI) * 0.15;
      let jpg = await page.evaluate(b => {
        const m = window.__m3d.map;
        m.jumpTo({ bearing: b });
        m.redraw();
        // Tiles still loading (areTilesLoaded() stays false here even when all are in).
        const caches = Object.values(m.style.tileManagers || m.style.sourceCaches || {});
        if (m.terrain) caches.push(m.terrain.tileManager || m.terrain.sourceCache);
        const waiting = caches.some(c => c && Object.values(c._tiles || {}).some(t => t.state === 'loading' || t.state === 'reloading'));
        return waiting ? null : m.getCanvas().toDataURL('image/jpeg', 0.92);
      }, startBearing + 360 * e);
      if (!jpg) {   // a tile still on its way: wait for it, then draw again
        await idle(3000);
        jpg = await page.evaluate(() => { const m = window.__m3d.map; m.redraw(); return m.getCanvas().toDataURL('image/jpeg', 0.92); });
      }
      fs.writeFileSync(path.join(OUT, 'frames', String(f + 1).padStart(4, '0') + '.jpg'), Buffer.from(jpg.split(',')[1], 'base64'));
      if (f % 24 === 0) console.log(`frame ${f + 1}/${total} · ${Math.round((Date.now() - t0) / 1000)} s`);
    }
    console.log('done:', total, 'frames in', Math.round((Date.now() - t0) / 1000), 's');
  }
  await browser.close();
  if (process.env.TILE_LOG) fs.writeFileSync(process.env.TILE_LOG, [...asked].sort().join('\n') + '\n');
  if (process.env.TILE_DIR) {
    const missing = [...asked].filter(k => !fs.existsSync(path.join(process.env.TILE_DIR, k + '.jpg')));
    console.log('tiles asked', asked.size, 'missing', missing.length);
  }
})().catch(e => { console.error(e); process.exit(1); });

// A vertical (1080x1920) "¿Qué estación de esquí es?" video for TikTok / Reels /
// Shorts: the station's 3D view turning a full circle over the satellite
// imagery, with the question on top, a clue and a call to comment. Frame by
// frame (the bearing is stepped and each frame waits for its tiles), so it's
// smooth however slow the machine draws; ffmpeg then joins the frames.
//
// Run by .github/workflows/make-video.yml (the imagery is reachable there),
// against docs/ served on localhost:8903:
//   node marketing/make_video.js --station <id> --hint "Pirineo aragonés" --out out/ [--seconds 12]
// Writes out/frames/0001.jpg... ; the workflow turns them into the mp4.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const arg = (name, def) => { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : def; };
const STATION = arg('station');
const HINT = arg('hint', '');
const OUT = arg('out', 'out');
const SECONDS = +arg('seconds', 12);
const FPS = +arg('fps', 24);
const SCALE = +arg('scale', 1.5);   // drawn at 810x1440, scaled to 1080x1920 by ffmpeg: WebGL in software is slow
const TITLE = arg('title', '¿Qué estación\nde esquí es?');
const CTA = arg('cta', 'Respuesta en los comentarios 👇');
const OUTRO = arg('outro', 'Mapa 3D de 1.400 estaciones · skiinfoapp.com');
const BASE = arg('base', 'http://localhost:8903');
const ZOOM = +arg('zoom', 0.6);           // closer than the default framing
const W = 540, H = 960;                   // CSS px; x2 = 1080x1920

(async () => {
  if (!STATION) throw new Error('--station is required');
  fs.mkdirSync(path.join(OUT, 'frames'), { recursive: true });
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || undefined,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: SCALE, serviceWorkers: 'block', locale: 'es-ES' });
  // Keep the open-meteo/stats/other calls from slowing things down; a mock route can be set for local tests.
  if (process.env.FAKE_TILE) {
    await ctx.route('**/World_Imagery/**', r => r.fulfill({ body: fs.readFileSync(process.env.FAKE_TILE), contentType: 'image/png', headers: { 'access-control-allow-origin': '*' } }));
  }
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

  // Video mode: only the 3D map, full screen, no names (they'd give the answer
  // away) and no buttons; the overlay with the texts on top.
  await page.addStyleTag({ content: `
    body * { visibility: hidden !important; }
    #map-3d, #map-3d *, #video-overlay, #video-overlay * { visibility: visible !important; }
    #map-3d { position: fixed !important; inset: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 9998 !important; opacity: 1 !important; }
    #map-3d .maplibregl-control-container { display: none !important; }
    #video-overlay { position: fixed; inset: 0; z-index: 9999; pointer-events: none; font-family: 'Barlow Condensed', sans-serif; color: #fff; }
    #video-overlay .top { position: absolute; top: 0; left: 0; right: 0; padding: 70px 28px 60px; text-align: center;
      background: linear-gradient(rgba(0,0,0,0.62), rgba(0,0,0,0)); }
    #video-overlay .title { white-space: pre-line; font-size: 50px; font-weight: 700; line-height: 1.0; text-transform: uppercase; letter-spacing: 0.5px; text-shadow: 0 3px 14px rgba(0,0,0,0.7); }
    #video-overlay .hint { display: inline-block; margin-top: 16px; font-size: 27px; font-weight: 700; padding: 6px 16px; border-radius: 999px;
      background: rgba(255,255,255,0.18); border: 1.5px solid rgba(255,255,255,0.55); text-shadow: 0 2px 8px rgba(0,0,0,0.6); }
    #video-overlay .bottom { position: absolute; left: 0; right: 0; bottom: 0; padding: 70px 28px 150px; text-align: center;
      background: linear-gradient(rgba(0,0,0,0), rgba(0,0,0,0.6)); }
    #video-overlay .cta { font-size: 34px; font-weight: 700; text-shadow: 0 3px 12px rgba(0,0,0,0.7); }
    #video-overlay .credit { position: absolute; left: 0; right: 0; bottom: 118px; text-align: center; font-family: 'IBM Plex Sans', sans-serif;
      font-size: 10.5px; opacity: 0.75; }
  ` });
  await page.evaluate(({ TITLE, HINT, CTA }) => {
    const o = document.createElement('div');
    o.id = 'video-overlay';
    o.innerHTML = '<div class="top"><div class="title"></div>' + (HINT ? '<div class="hint"></div>' : '') + '</div>' +
      '<div class="bottom"><div class="cta"></div></div><div class="credit">© OpenStreetMap (ODbL) · OpenSkiMap · Esri, Maxar, Earthstar Geographics · Terrain Tiles</div>';
    o.querySelector('.title').textContent = TITLE;
    if (HINT) o.querySelector('.hint').textContent = HINT;
    o.querySelector('.cta').textContent = CTA;
    document.body.appendChild(o);
  }, { TITLE, HINT, CTA });

  // The camera: the app's own framing, a little closer, no names.
  const startBearing = await page.evaluate((ZOOM) => {
    const m = window.__m3d.map;
    m.resize();
    if (m.getLayer('labels')) m.setLayoutProperty('labels', 'visibility', 'none');
    m.jumpTo({ zoom: m.getZoom() + ZOOM, pitch: 64 });
    return m.getBearing();
  }, ZOOM);
  const idle = (max) => page.evaluate((max) => new Promise(res => {
    const m = window.__m3d.map;
    let done = false;
    const finish = () => { if (!done) { done = true; res(); } };
    if (m.loaded() && m.areTilesLoaded()) { requestAnimationFrame(() => requestAnimationFrame(finish)); }
    m.once('idle', finish);
    setTimeout(finish, max);
  }), max);
  // Let the first view load fully (imagery and terrain), then step round.
  await page.evaluate(() => window.__m3d.map.triggerRepaint());
  for (let i = 0; i < 3; i++) await idle(15000);
  // Warm the tile cache all the way round, so each frame then only has to draw.
  for (let k = 1; k <= 8; k++) {
    await page.evaluate(b => window.__m3d.map.jumpTo({ bearing: b }), startBearing + 45 * k);
    await idle(15000);
  }
  await page.evaluate(b => window.__m3d.map.jumpTo({ bearing: b }), startBearing);
  await idle(15000);
  const t0 = Date.now();

  const total = Math.round(SECONDS * FPS);
  const outroFrom = total - Math.round(2.5 * FPS);
  for (let f = 0; f < total; f++) {
    if (f === outroFrom) await page.evaluate(OUTRO => { document.querySelector('#video-overlay .cta').textContent = OUTRO; }, OUTRO);
    // Ease in and out over the full turn, so the loop doesn't jerk.
    const t = f / total, e = t - Math.sin(2 * Math.PI * t) / (2 * Math.PI) * 0.15;
    await page.evaluate(b => window.__m3d.map.jumpTo({ bearing: b }), startBearing + 360 * e);
    await idle(1500);
    await page.screenshot({ path: path.join(OUT, 'frames', String(f + 1).padStart(4, '0') + '.jpg'), type: 'jpeg', quality: 92 });
    if (f % 24 === 0) console.log(`frame ${f + 1}/${total} · ${Math.round((Date.now() - t0) / 1000)} s`);
  }
  await browser.close();
  console.log('done:', total, 'frames');
})().catch(e => { console.error(e); process.exit(1); });

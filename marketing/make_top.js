// "Las 5 pistas más empinadas de …" for TikTok (the user's idea, 10 Oct): a
// countdown from #5 to #1, each run a few seconds of its own 3D view (the
// camera looking up the run, the run lit in its slope colours, a slow orbit)
// with its slope profile and steepest 50 m on a card, as in the app.
//
//   node marketing/make_top.js --spec marketing/top-es.json --phase list    # writes marketing/tiles/<name>.txt
//   (fetch-tiles.yml with that name downloads the satellite tiles)
//   node marketing/make_top.js --spec marketing/top-es.json --phase frames  # /tmp/top-<name>/<i>/0001.jpg…
//   node marketing/make_top.js --spec marketing/top-es.json --phase video --out marketing/videos/top-es.mp4
//
// The spec: { name, hook, title, cta, runs: [{ station, resort, run }…] }, runs
// from #5 to #1. Numbers (max. % and degrees) come from docs/profile.js, the
// same as the app. Docs served on localhost:8903; WebGL in software, so each
// frame is drawn once and read from the canvas (as make_video.js).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFile, execFileSync } = require('child_process');

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const SPEC = JSON.parse(fs.readFileSync(arg('spec'), 'utf8'));
const PHASE = arg('phase', 'frames'), OUT = arg('out', `marketing/videos/${SPEC.name}.mp4`);
const PITCH = SPEC.pitch || 60;   // the camera's tilt (lower for long runs, seen from further off)
const SEG = +arg('seconds', 4), LAST = +arg('last', 5), FPS = 12, HOOK_T = 1.6;
const WORK = arg('work', `/tmp/top-${SPEC.name}`), ONLY = arg('only', '');
const ROOT = path.join(__dirname, '..'), BASE = 'http://localhost:8903';
const W = 540, H = 960;
const TILES = path.join(ROOT, 'marketing', 'tiles', SPEC.name);
const runs = SPEC.runs.map((r, i) => Object.assign({ rank: SPEC.runs.length - i, i }, r));
// With a voice-over (tts.yml: marketing/voice/<name>/<voice>/{intro,5…1}.wav),
// each run lasts as long as its line (the intro too, on the first) plus a pause.
const VOICE = SPEC.voice && path.join(ROOT, 'marketing', 'voice', SPEC.name, SPEC.voice);
const wav = key => VOICE && fs.existsSync(path.join(VOICE, key + '.wav')) ? path.join(VOICE, key + '.wav') : null;
function wavDur(file) {
  const b = fs.readFileSync(file);
  let o = 12, rate = 0, bytes = 0;
  while (o < b.length - 8) {
    const id = b.toString('ascii', o, o + 4), size = b.readUInt32LE(o + 4);
    if (id === 'fmt ') rate = b.readUInt32LE(o + 16);   // byte rate
    if (id === 'data') { bytes = Math.min(size, b.length - o - 8); break; }
    o += 8 + size + (size & 1);
  }
  return bytes / rate;
}
const LEAD = 0.1, PAUSE = 0.6;
const introDur = () => (wav('intro') ? wavDur(wav('intro')) : 0);
const secondsOf = r => {
  if (!wav(String(r.rank))) return r.rank === 1 ? LAST : SEG;
  const first = r.rank === SPEC.runs.length;
  return Math.max(3.5, LEAD + (first ? introDur() : 0) + wavDur(wav(String(r.rank))) + PAUSE);
};

// The run's geometry from the station's data, and the camera: looking up it
// (from its lowest point to its highest), framed on it.
function runGeom(r) {
  const raw = JSON.parse(fs.readFileSync(path.join(ROOT, 'docs', 'data', r.station + '.json'), 'utf8'));
  const parts = [];
  raw.runs.forEach(x => { if (x.name === r.run) parts.push(...(x.geom || [])); });
  if (!parts.length) throw new Error(`no run ${r.run} in ${r.resort}`);
  const pts = parts.flat();
  const lo = pts.reduce((a, p) => (p[2] < a[2] ? p : a)), hi = pts.reduce((a, p) => (p[2] > a[2] ? p : a));
  const rad = Math.PI / 180;
  const y = Math.sin((hi[0] - lo[0]) * rad) * Math.cos(hi[1] * rad);
  const x = Math.cos(lo[1] * rad) * Math.sin(hi[1] * rad) - Math.sin(lo[1] * rad) * Math.cos(hi[1] * rad) * Math.cos((hi[0] - lo[0]) * rad);
  // The run's main direction (principal axis, in metres) and the bearing that
  // sees it from the side, on the side closer to looking uphill.
  const mx = pts.reduce((t, p) => t + p[0], 0) / pts.length, my = pts.reduce((t, p) => t + p[1], 0) / pts.length, kx = Math.cos(my * rad);
  let sxx = 0, syy = 0, sxy = 0;
  pts.forEach(p => { const dx = (p[0] - mx) * kx, dy = p[1] - my; sxx += dx * dx; syy += dy * dy; sxy += dx * dy; });
  const axis = (90 - Math.atan2(2 * sxy, sxx - syy) / 2 / rad + 360) % 360;   // compass bearing of the axis
  const up = (Math.atan2(y, x) / rad + 360) % 360, diff = b => Math.abs(((b - up) % 360 + 540) % 360 - 180);
  const side = [axis + 90, axis - 90].map(b => (b + 360) % 360).sort((a, b) => diff(a) - diff(b))[0];
  let len = 0, vert = 0;
  raw.runs.forEach(x => { if (x.name === r.run && (!x.uses || x.uses.split(',').includes('downhill'))) { len += x.length_m || 0; vert += x.vertical_m || 0; } });
  return {
    avg: len ? vert / len * 100 : null, len, vert, side, parts, bearing: (Math.atan2(y, x) / rad + 360) % 360,
    bbox: [[Math.min(...pts.map(p => p[0])), Math.min(...pts.map(p => p[1]))], [Math.max(...pts.map(p => p[0])), Math.max(...pts.map(p => p[1]))]],
  };
}

async function draw3d(browser) {
  const asked = new Set();
  const fake = path.join(WORK, 'fake.jpg');
  for (const r of runs) {
    if (ONLY && !ONLY.split(',').includes(String(r.rank))) continue;
    const g = runGeom(r);
    const ctx = await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 1.5, serviceWorkers: 'block', locale: 'es-ES' });
    await ctx.route('**/World_Imagery/**', rt => {
      const m = /\/tile\/(\d+)\/(\d+)\/(\d+)/.exec(rt.request().url());
      const key = m ? m.slice(1).join('_') : null, file = key && path.join(TILES, key + '.jpg');
      if (key) asked.add(key);
      const body = file && fs.existsSync(file) ? fs.readFileSync(file) : fs.readFileSync(fake);
      return rt.fulfill({ body, contentType: 'image/jpeg', headers: { 'access-control-allow-origin': '*' } });
    });
    const demDir = path.join(WORK, 'dem');
    await ctx.route('**/elevation-tiles-prod/**', async rt => {
      const url = rt.request().url(), m = /terrarium\/(\d+)\/(\d+)\/(\d+)\.png/.exec(url);
      if (!m) return rt.continue();
      const file = path.join(demDir, m.slice(1).join('_') + '.png');
      if (!fs.existsSync(file)) await new Promise(res => execFile('curl', ['-sSf', '--retry', '3', '-o', file, url], () => res()));
      if (!fs.existsSync(file)) return rt.fulfill({ status: 404, headers: { 'access-control-allow-origin': '*' } });
      return rt.fulfill({ body: fs.readFileSync(file), contentType: 'image/png', headers: { 'access-control-allow-origin': '*' } });
    });
    await ctx.route(/open-meteo|firestore|googleapis/, rt => rt.abort());
    await ctx.addInitScript(() => {
      try {
        localStorage.setItem('si_lang', 'es'); localStorage.setItem('si_lang_hint', '1'); localStorage.setItem('si_3d_hint', '9');
        localStorage.setItem('si_install_hint', '1'); localStorage.setItem('si_fav_nudge', '9'); localStorage.setItem('si_map_mode', 'slope');
      } catch (e) {}
      let real;
      Object.defineProperty(window, 'SkiMap3D', { configurable: true, get() { return real; },
        set(v) { real = Object.assign({}, v, { open(o) { const a = v.open(o); window.__m3d = a; return a; } }); } });
    });
    const page = await ctx.newPage();
    page.on('pageerror', e => console.error('page error:', e.message));
    await page.goto(`${BASE}/?estacion=${r.station}&vista=mapa`);
    await page.waitForSelector('#map-svg polyline', { timeout: 60000 });
    await page.waitForTimeout(1500);
    await page.click('#map-3d-btn');
    await page.waitForFunction(() => window.__m3d && window.__m3d.map && window.__m3d.map.isStyleLoaded() && window.__m3d.map.getSource('runs'), null, { timeout: 120000 });
    await page.evaluate(p => { window.__pitch = p; }, PITCH);
    await page.addStyleTag({ content: `
      body * { visibility: hidden !important; }
      #map-3d, #map-3d * { visibility: visible !important; }
      #map-3d { position: fixed !important; inset: 0 !important; width: 100vw !important; height: 100vh !important; z-index: 9998 !important; opacity: 1 !important; }
      #map-3d .maplibregl-control-container, .map3d-route-start, .map3d-route-end { display: none !important; }` });
    // The run lit in its slope colours over everything else, which is dimmed.
    const cam = await page.evaluate(async ({ coords, bbox, bearing }) => {
      const api = window.__m3d, m = api.map;
      m.resize();
      m._fadeDuration = 0;
      api.setMode('slope');
      const src = m.getSource('runs');
      const data = src.getData ? await src.getData() : src._data;
      const want = new Set(coords);
      // A feature is the run when (nearly) all its points are the run's: neighbours
      // share a junction point or two with it.
      const fis = data.features.filter(f => {
        const cs = f.geometry.coordinates, hit = cs.filter(c => want.has(c[0].toFixed(6) + ',' + c[1].toFixed(6))).length;
        return hit >= Math.max(2, cs.length * 0.8);
      }).map(f => f.properties.fi);
      const filter = ['in', ['get', 'fi'], ['literal', fis]];
      m.addLayer({ id: 'top-glow', type: 'line', source: 'slope', filter, layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: { 'line-color': '#ffffff', 'line-width': 13, 'line-blur': 3, 'line-opacity': 0.95 } }, 'labels');
      m.addLayer({ id: 'top-run', type: 'line', source: 'slope', filter, layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: { 'line-color': ['get', 'color'], 'line-width': 6.5 } }, 'labels');
      ['slope', 'run-halo', 'lift', 'lift-casing'].forEach(id => m.setPaintProperty(id, 'line-opacity', 0.45));
      m.setPaintProperty('labels', 'icon-opacity', 0.6);
      m.fitBounds(bbox, { padding: { top: 270, bottom: 330, left: 50, right: 50 }, bearing, pitch: window.__pitch, maxZoom: 16.2, duration: 0 });
      const c = m.getCenter();
      return { fis: fis.length, center: [c.lng, c.lat], zoom: m.getZoom() };
    }, { coords: g.parts.flat().map(p => p[0].toFixed(6) + ',' + p[1].toFixed(6)), bbox: g.bbox, bearing: g.bearing });
    console.log(`#${r.rank} ${r.run} (${r.resort}): ${cam.fis} parts, zoom ${cam.zoom.toFixed(2)}`);
    const idle = max => page.evaluate(max => new Promise(res => {
      const m = window.__m3d.map; let done = false;
      const finish = () => { if (!done) { done = true; res(); } };
      m.once('idle', finish); m.triggerRepaint(); setTimeout(finish, max);
    }), max);
    // fitBounds doesn't allow for the relief and the tilt (long runs came out
    // small and off to one side): fit the run's own points, on the relief,
    // into the free part of the screen between the texts and the card.
    await idle(15000); await idle(4000);
    // Long runs are seen from the side (g.side): looking up them, a 6 km run
    // came out tiny, end-on.
    Object.assign(cam, await page.evaluate(({ pts, bearings, box }) => {
      // Start from the run's middle, at the zoom where its length spans the box
      // (fitBounds' start, from the whole bounds tilted, left long runs over the horizon).
      const m = window.__m3d.map, R = 6371000, rad = Math.PI / 180;
      const lon = pts.reduce((t, p) => t + p[0], 0) / pts.length, lat = pts.reduce((t, p) => t + p[1], 0) / pts.length;
      const ext = Math.max(...pts.map(p => Math.hypot((p[0] - lon) * rad * R * Math.cos(lat * rad), (p[1] - lat) * rad * R))) * 2;
      const c0 = { lng: lon, lat }, z0 = Math.min(16.2, Math.log2(40075016 * Math.cos(lat * rad) / 512 / (ext / (box[2] - box[0]))));
      const onScreen = () => {
        const ps = pts.map(p => m.project([p[0], p[1]]));
        return [Math.min(...ps.map(p => p.x)), Math.min(...ps.map(p => p.y)), Math.max(...ps.map(p => p.x)), Math.max(...ps.map(p => p.y))];
      };
      const miss = b => Math.abs((b[0] + b[2]) / 2 - (box[0] + box[2]) / 2) + Math.abs((b[1] + b[3]) / 2 - (box[1] + box[3]) / 2)
        + Math.max(0, box[0] - b[0]) + Math.max(0, b[2] - box[2]) + Math.max(0, box[1] - b[1]) + Math.max(0, b[3] - box[3]);
      let best = null;
      // Damped steps, gentler on each try: a full step sometimes overshot (the
      // relief under the new centre isn't known until it's drawn).
      for (const bearing of bearings) for (const gain of [1, 0.6, 0.35]) {
        let c = c0, z = z0;
        for (let k = 0; k < 16; k++) {
          m.jumpTo({ center: c, zoom: z, bearing, pitch: window.__pitch });
          m.redraw();   // the camera's height over the relief is only updated on a draw
          const [x0, y0, x1, y1] = onScreen();
          if (y0 < -2000) { z -= 0.5; continue; }   // part of it beyond the horizon: back off
          const sc = Math.min((box[2] - box[0]) / Math.max(1, x1 - x0), (box[3] - box[1]) / Math.max(1, y1 - y0));
          // Move the centre so the run's middle lands on the box's: how far a small
          // step east and north moves the screen (unproject() reads the last
          // frame's relief, which threw long runs off to one side).
          const dx = gain * ((x0 + x1) / 2 - (box[0] + box[2]) / 2), dy = gain * ((y0 + y1) / 2 - (box[1] + box[3]) / 2);
          const o = m.project(c), e = m.project([c.lng + 0.001, c.lat]), n = m.project([c.lng, c.lat + 0.001]);
          const a11 = e.x - o.x, a12 = n.x - o.x, a21 = e.y - o.y, a22 = n.y - o.y, det = a11 * a22 - a12 * a21;
          if (det) c = { lng: c.lng + 0.001 * (a22 * dx - a12 * dy) / det, lat: c.lat + 0.001 * (a11 * dy - a21 * dx) / det };
          z = Math.max(z0 - 1.5, Math.min(16.2, z0 + 1.5, z + gain * Math.max(-1, Math.min(1, Math.log2(sc) * 0.8))));
        }
        m.jumpTo({ center: c, zoom: z, bearing, pitch: window.__pitch });
        m.redraw();
        const b = onScreen(), err = miss(b);
        if (!best || err < best.err) best = { center: [c.lng, c.lat], zoom: z, bearing, err, box: b.map(Math.round) };
        if (err < 40) break;
      }
      m.jumpTo({ center: best.center, zoom: best.zoom, bearing: best.bearing, pitch: window.__pitch });
      return best;
    }, { pts: g.parts.flat().filter((_, i, a) => i % Math.ceil(a.length / 300) === 0).concat(g.parts.map(p => p[p.length - 1])),
         bearings: [SPEC.metric === 'len' ? g.side : g.bearing],
         box: [60, 265, 480, 495] }));
    console.log(`  fitted: zoom ${cam.zoom.toFixed(2)}, bearing ${Math.round(cam.bearing - g.bearing)}° from uphill, on screen ${cam.box}`);
    // A slow orbit (28°) while closing in a little, eased at both ends.
    const view = t => { const e = (1 - Math.cos(Math.PI * t)) / 2; return { center: cam.center, zoom: cam.zoom - 0.2 + 0.2 * e, bearing: cam.bearing - 14 + 28 * e, pitch: PITCH }; };
    const total = Math.round(secondsOf(r) * FPS);
    for (let k = 0; k <= 4; k++) { await page.evaluate(v => window.__m3d.map.jumpTo(v), view(k / 4)); await idle(15000); await idle(4000); }
    if (PHASE === 'list' || PHASE === 'check') {   // a still to check the framing and the lit run
      await page.evaluate(v => window.__m3d.map.jumpTo(v), view(0.5)); await idle(8000);
      const jpg = await page.evaluate(() => { const m = window.__m3d.map; m.redraw(); return m.getCanvas().toDataURL('image/jpeg', 0.8); });
      fs.writeFileSync(path.join(WORK, `check-${r.rank}.jpg`), Buffer.from(jpg.split(',')[1], 'base64'));
    }
    if (PHASE === 'frames') {
      const dir = path.join(WORK, String(r.rank));
      fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
      await page.evaluate(v => window.__m3d.map.jumpTo(v), view(0)); await idle(15000);
      for (let f = 0; f < total; f++) {
        let jpg = await page.evaluate(v => {
          const m = window.__m3d.map;
          m.jumpTo(v); m.redraw();
          const caches = Object.values(m.style.tileManagers || m.style.sourceCaches || {});
          if (m.terrain) caches.push(m.terrain.tileManager || m.terrain.sourceCache);
          const waiting = caches.some(c => c && Object.values(c._tiles || {}).some(t => t.state === 'loading' || t.state === 'reloading'));
          return waiting ? null : m.getCanvas().toDataURL('image/jpeg', 0.92);
        }, view(f / (total - 1)));
        if (!jpg) { await idle(3000); jpg = await page.evaluate(() => { const m = window.__m3d.map; m.redraw(); return m.getCanvas().toDataURL('image/jpeg', 0.92); }); }
        fs.writeFileSync(path.join(dir, String(f + 1).padStart(4, '0') + '.jpg'), Buffer.from(jpg.split(',')[1], 'base64'));
      }
      console.log(`  ${total} frames`);
    }
    await ctx.close();
  }
  if (PHASE === 'list' && !ONLY) {
    fs.mkdirSync(path.dirname(TILES), { recursive: true });
    fs.writeFileSync(path.join(ROOT, 'marketing', 'tiles', SPEC.name + '.txt'), [...asked].sort().join('\n') + '\n');
    console.log(asked.size, 'tiles listed');
  } else if (PHASE === 'frames') {
    console.log('tiles asked', asked.size, 'missing', [...asked].filter(k => !fs.existsSync(path.join(TILES, k + '.jpg'))).length);
  }
}

const CSS = `
  html, body { margin: 0; background: transparent; }
  #o { position: fixed; inset: 0; font-family: 'Barlow Condensed', sans-serif; color: #fff; }
  .top { position: absolute; top: 0; left: 0; right: 0; padding: 62px 24px 70px; text-align: center;
    background: linear-gradient(rgba(0,0,0,0.66), rgba(0,0,0,0.35) 70%, rgba(0,0,0,0)); }
  .kicker { font-size: 25px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.92; text-shadow: 0 2px 10px rgba(0,0,0,0.7); }
  .hooktop { white-space: pre-line; font-size: 48px; font-weight: 700; line-height: 1.0; text-transform: uppercase; color: #ffd257; text-shadow: 0 3px 14px rgba(0,0,0,0.75); }
  .rank { display: flex; align-items: center; justify-content: center; gap: 14px; margin-top: 10px; }
  .num { flex: none; width: 74px; height: 74px; border-radius: 50%; background: #ffd257; color: #111; display: flex; align-items: center; justify-content: center;
    font-size: 50px; font-weight: 700; line-height: 1; box-shadow: 0 4px 16px rgba(0,0,0,0.45); }
  .name { text-align: left; }
  .run { font-size: 48px; font-weight: 700; line-height: 0.95; text-transform: uppercase; text-shadow: 0 3px 14px rgba(0,0,0,0.75); }
  .resort { font-size: 26px; font-weight: 600; opacity: 0.95; text-shadow: 0 2px 10px rgba(0,0,0,0.75); }
  .card { position: absolute; left: 20px; right: 20px; bottom: 282px; padding: 12px 14px 8px; border-radius: 18px;
    background: rgba(255,255,255,0.93); color: #111; box-shadow: 0 8px 26px rgba(0,0,0,0.35); }
  .row { display: flex; align-items: baseline; justify-content: space-between; }
  .big { font-size: 40px; font-weight: 700; line-height: 1; }
  .big small { font-size: 22px; font-weight: 600; color: #444; margin-left: 4px; }
  .site { font-size: 18px; font-weight: 600; color: #555; }
  svg { display: block; width: 100%; height: auto; margin-top: 4px; }
  .lbl { font-family: 'IBM Plex Sans', sans-serif; font-size: 10px; fill: #444; }
  .steep { font-family: 'Barlow Condensed', sans-serif; font-size: 17px; font-weight: 700; fill: #111; }
  .kicker.cta1 { color: #ffd257; font-size: 30px; text-transform: none; }
  .credit { position: absolute; left: 0; right: 0; bottom: 258px; text-align: center; font-family: 'IBM Plex Sans', sans-serif; font-size: 10px; opacity: 0.8; text-shadow: 0 1px 4px rgba(0,0,0,0.8); }
`;
const esc = t => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;');

// The slope card, drawn in the page with docs/profile.js (as the app's chart:
// one quad per stretch in its slope colour, and the steepest 50 m marked).
function cardScript() {
  window.T = s => s;
  window.drawCard = function (parts, avg, label) {
    let best = null;
    buildElevationProfiles(parts).forEach(p => {
      const sm = smoothProfile(p, SLOPE_WINDOW_M), st = findSteepestSection(sm, STEEPEST_M);
      // The steepest part, or the longest when the card is about length.
      const key = label ? sm[sm.length - 1].dist : Math.abs(st ? st.pitchPct : 0);
      if (st && (!best || key > best.key)) best = { sm, st, key };
    });
    const { sm, st } = best;
    const total = sm[sm.length - 1].dist, eles = sm.map(p => p.ele);
    const lo = Math.min(...eles), hi = Math.max(...eles);
    const VW = 500, VH = 112, pl = 4, pr = 4, pt = 24, pb = 15;
    const x = d => pl + d / total * (VW - pl - pr), y = e => pt + (1 - (e - lo) / (hi - lo || 1)) * (VH - pt - pb);
    const col = { novice: 'hsl(125 82% 30%)', easy: 'hsl(208 88% 41%)', intermediate: 'hsl(359 78% 49%)', advanced: 'hsl(0 0% 12%)' };
    let s = '';
    for (let i = 0; i < sm.length - 1; i++) {
      const a = sm[i], b = sm[i + 1], dd = b.dist - a.dist;
      if (dd <= 0) continue;
      const z = pitchZoneFor((a.ele - b.ele) / dd * 100).key;
      s += `<polygon points="${x(a.dist)},${y(lo)} ${x(a.dist)},${y(a.ele)} ${x(b.dist)},${y(b.ele)} ${x(b.dist)},${y(lo)}" fill="${col[z]}" opacity="0.8"/>`;
    }
    s += `<polyline points="${sm.map(p => x(p.dist).toFixed(1) + ',' + y(p.ele).toFixed(1)).join(' ')}" fill="none" stroke="#111" stroke-width="2"/>`;
    // The steepest stretch: a bracket over it with its degrees.
    const eleAt = d => { for (let i = 1; i < sm.length; i++) if (sm[i].dist >= d) { const a = sm[i - 1], b = sm[i]; return a.ele + (b.ele - a.ele) * ((d - a.dist) / ((b.dist - a.dist) || 1)); } return sm[sm.length - 1].ele; };
    const x1 = x(st.startDist), x2 = x(st.endDist), yt = Math.min(y(eleAt(st.startDist)), y(eleAt(st.endDist))) - 6;
    s += `<line x1="${x1}" y1="${y(eleAt(st.startDist))}" x2="${x2}" y2="${y(eleAt(st.endDist))}" stroke="#ffd257" stroke-width="6" stroke-linecap="round"/>`;
    s += `<line x1="${x1}" y1="${y(eleAt(st.startDist))}" x2="${x2}" y2="${y(eleAt(st.endDist))}" stroke="#111" stroke-width="2" stroke-dasharray="3 2"/>`;
    const tx = Math.min(VW - 60, Math.max(60, (x1 + x2) / 2));
    s += `<text class="steep" x="${tx}" y="${Math.max(16, yt - 4)}" text-anchor="middle">▼ ${Math.round(Math.abs(st.pitchPct))}&#8202;% · 50 m</text>`;
    s += `<text class="lbl" x="${pl}" y="${VH - 3}">${Math.round(sm[0].ele)} m</text>`;
    s += `<text class="lbl" x="${VW - pr}" y="${VH - 3}" text-anchor="end">${Math.round(sm[sm.length - 1].ele)} m · ${total >= 1000 ? (total / 1000).toFixed(1).replace('.', ',') + ' km' : Math.round(total / 10) * 10 + ' m'}</text>`;
    document.getElementById('chart').innerHTML = `<svg viewBox="0 0 ${VW} ${VH}">${s}</svg>`;
    const pct = Math.round(Math.abs(st.pitchPct));
    document.getElementById('big').innerHTML = label ? `${label.big} <small>${label.small}</small>` : avg != null
      ? `${Math.round(avg)}&#8202;% de media <small>máx. ${pct}&#8202;%</small>`
      : `${pitchDeg(st.pitchPct)}° <small>máx. ${pct}&#8202;% de pendiente</small>`;
    return { pct, deg: pitchDeg(st.pitchPct), avg: avg != null ? `${Math.round(avg)} % (${pitchDeg(avg)}°) de media, ` : '' };
  };
}

async function overlays(browser) {
  const page = await (await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 2 })).newPage();
  const fonts = fs.readFileSync(path.join(ROOT, 'docs', 'index.html'), 'utf8').match(/@font-face[^}]*}/g).join('\n').replace(/font-display: optional/g, 'font-display: block');
  const credit = '<div class="credit">© OpenStreetMap (ODbL) · OpenSkiMap · Esri, Maxar, Earthstar Geographics · Terrain Tiles</div>';
  const out = [];
  for (const r of runs) {
    const g = runGeom(r);
    for (const hook of r.rank === runs.length && SPEC.hook ? [false, true] : [false]) {
      // The call to comment over the last run (mid-screen it hid the runs).
      const kicker = r.rank === 1 && SPEC.cta ? `<div class="kicker cta1">${esc(SPEC.cta)}</div>` : `<div class="kicker">${esc(SPEC.title)}</div>`;
      const head = hook ? `<div class="hooktop">${esc(SPEC.hook)}</div>` : kicker;
      const html = `<!doctype html><meta charset="utf-8"><style>${fonts}${CSS}</style><script>(${cardScript})()</script><script src="/profile.js"></script>
        <div id="o"><div class="top">${head}<div class="rank"><div class="num">${r.rank}</div><div class="name"><div class="run">${esc(r.run)}</div><div class="resort">${esc(r.resort)}</div></div></div></div>
        <div class="card"><div class="row"><div class="big" id="big"></div><div class="site">skiinfoapp.com</div></div><div id="chart"></div></div>${credit}</div>`;
      await page.route(BASE + '/__top', rt => rt.fulfill({ body: html, contentType: 'text/html' }));
      await page.goto(BASE + '/__top');
      await page.unroute(BASE + '/__top');
      // "len": the longest runs, "6,2 km" and its vertical.
    const num = (x, d) => x.toLocaleString('es-ES', { minimumFractionDigits: d, maximumFractionDigits: d });
    const label = SPEC.metric === 'len' ? { big: `${num(g.len / 1000, 1)} km`, small: `${num(Math.round(g.vert), 0)} m de desnivel` } : null;
    const v = await page.evaluate(([parts, avg, label]) => window.drawCard(parts, avg, label), [g.parts, SPEC.metric === 'avg' ? g.avg : null, label]);
    if (label) v.avg = `${label.big}, ${label.small}, `;
      await page.evaluate(() => Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 5000))]));
      await page.waitForTimeout(150);
      const file = path.join(WORK, `ov${r.rank}${hook ? 'h' : ''}.png`);
      await page.screenshot({ path: file, omitBackground: true });
      if (!hook) { out.push(`#${r.rank} ${r.run} (${r.resort}): ${v.avg}máx. ${v.pct} % · ${v.deg}°, ${secondsOf(r).toFixed(1)} s`); }
    }
  }
  console.log(out.join('\n'));
}

(async () => {
  fs.mkdirSync(path.join(WORK, 'dem'), { recursive: true });
  const ff = execFileSync('python3', ['-c', 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())']).toString().trim();
  if (!fs.existsSync(path.join(WORK, 'fake.jpg'))) execFileSync(ff, ['-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=0x6f7560:s=256x256', '-frames:v', '1', path.join(WORK, 'fake.jpg')]);
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium',
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  if (['list', 'check', 'frames'].includes(PHASE)) await draw3d(browser);
  if (PHASE === 'video' || PHASE === 'overlays') await overlays(browser);
  await browser.close();
  if (PHASE !== 'video') return;
  // One segment per run (#5 first), the hook over the first 1.6 s of the first.
  const segs = [];
  for (const r of runs) {
    const T = secondsOf(r), dir = path.join(WORK, String(r.rank));
    // The frames drawn always fill the segment (a line re-recorded a little
    // longer just slows the orbit slightly instead of drawing it all again).
    const nFrames = fs.readdirSync(dir).filter(f => f.endsWith('.jpg')).length;
    const inputs = ['-framerate', (nFrames / T).toFixed(4), '-i', path.join(dir, '%04d.jpg')];
    const chain = ['[0]minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=1080:1920:flags=lanczos[m]'];
    let v = '[m]', k = 1;
    const over = (file, enable) => { inputs.push('-loop', '1', '-i', path.join(WORK, file)); chain.push(`${v}[${k}]overlay${enable ? `=enable='${enable}'` : ''}[o${k}]`); v = `[o${k}]`; k++; };
    const first = r.rank === runs.length, hookT = wav('intro') ? LEAD + introDur() : HOOK_T;
    if (first && SPEC.hook) { over(`ov${r.rank}h.png`, `lt(t,${hookT.toFixed(2)})`); over(`ov${r.rank}.png`, `gte(t,${hookT.toFixed(2)})`); }
    else over(`ov${r.rank}.png`);
    // The voice: the intro then the run's line on the first, padded with silence.
    const lines = [first && wav('intro'), wav(String(r.rank))].filter(Boolean);
    const audio = ['-map', v];
    if (lines.length) {
      const a0 = k;
      lines.forEach(f => inputs.push('-i', f));
      const ins = lines.map((_, j) => `[${a0 + j}:a]`).join('');
      chain.push(`${ins}concat=n=${lines.length}:v=0:a=1,aresample=44100,adelay=${LEAD * 1000}:all=1,apad[aud]`);
    } else {
      inputs.push('-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=mono');
      chain.push(`[${k}:a]anull[aud]`);
    }
    audio.push('-map', '[aud]', '-c:a', 'aac', '-b:a', '128k', '-ac', '1', '-ar', '44100');
    const seg = path.join(WORK, `seg${r.rank}.mp4`);
    execFileSync(ff, ['-y', '-loglevel', 'error', ...inputs, '-filter_complex', chain.join(';'), ...audio, '-t', String(T), '-r', '30',
      '-c:v', 'libx264', '-crf', '21', '-pix_fmt', 'yuv420p', seg], { stdio: 'inherit' });
    segs.push(seg);
  }
  const list = path.join(WORK, 'list.txt');
  fs.writeFileSync(list, segs.map(s => `file '${s}'`).join('\n') + '\n');
  const tmp = path.join(WORK, 'out.mp4');
  execFileSync(ff, ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', tmp], { stdio: 'inherit' });
  fs.copyFileSync(tmp, OUT);
  let t = 0;
  const marks = [[0.4, 'a']];
  runs.forEach(r => { marks.push([t + secondsOf(r) / 2, String(r.rank)]); t += secondsOf(r); });
  for (const [at, suf] of marks) execFileSync(ff, ['-y', '-loglevel', 'error', '-ss', String(at), '-i', OUT, '-frames:v', '1', '-q:v', '3', OUT.replace(/\.mp4$/, `-preview-${suf}.jpg`)]);
  console.log('done:', OUT, `${t} s`);
})().catch(e => { console.error(e); process.exit(1); });

// Screenshots of a station page for the home's "Así es cada estación" band, in
// each language: docs/img/home/profile-<lang>.jpg (a run's slope profile) and
// snow-<lang>.jpg (the snow summary, with sample weather: no dates on it).
// Against docs/ served on localhost:8903 after build_seo_pages.py:
//   NODE_PATH=/opt/node22/lib/node_modules node marketing/make_home_shots.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const BASE = 'http://localhost:8903';
const OUT = path.join(__dirname, '..', 'docs', 'img', 'home');
const BAQ = '125d02338620dc079d5d635595a099370161bf83';
const RUN = 'Colhet de Marimanha';
const STATION = { es: '/estacion/', en: '/en/resort/', fr: '/fr/station/', de: '/de/skigebiet/', it: '/it/stazione/', nl: '/nl/skigebied/', pl: '/pl/osrodek/' };
const HOME = { es: '/', en: '/en/', fr: '/fr/', de: '/de/', it: '/it/', nl: '/nl/', pl: '/pl/' };

// Sample weather (a snowy week), the shape Open-Meteo answers.
function sampleMeteo(url) {
  const n = new URL(url).searchParams.get('latitude').split(',').length;
  const today = new Date(), iso = d => d.toISOString().slice(0, 10);
  const days = []; for (let i = -1; i < 7; i++) { const d = new Date(today); d.setUTCDate(d.getUTCDate() + i); days.push(iso(d)); }
  const hours = []; days.forEach(d => { for (let h = 0; h < 24; h++) hours.push(d + 'T' + String(h).padStart(2, '0') + ':00'); });
  const nowT = iso(today) + 'T' + String(today.getUTCHours()).padStart(2, '0') + ':00';
  const mk = k => ({
    utc_offset_seconds: 3600,
    current: { time: nowT, temperature_2m: -4 + 3 * k, wind_speed_10m: 22, weather_code: 73 },
    hourly: { time: hours, snowfall: hours.map((_, i) => (i > 10 && i < 30 ? 0.45 : 0)), snow_depth: hours.map(() => 0.85), freezing_level_height: hours.map(() => 1850) },
    daily: { time: days, weather_code: [71, 73, 75, 3, 0, 2, 85, 45], temperature_2m_max: days.map((_, i) => -2 + i), temperature_2m_min: days.map((_, i) => -9 + i),
      snowfall_sum: [8, 12, 22, 0.3, 0, 0, 6, 0], wind_speed_10m_max: [30, 45, 60, 20, 10, 15, 25, 18] },
  });
  const arr = Array.from({ length: n }, (_, k) => mk(k));
  return JSON.stringify(n === 1 ? arr[0] : arr);
}

(async () => {
  const slug = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'docs', 'slugs.json'), 'utf8'))[BAQ];
  const b = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium' });
  for (const lang of Object.keys(STATION)) {
    const ctx = await b.newContext({ viewport: { width: 420, height: 900 }, deviceScaleFactor: 2, serviceWorkers: 'block', isMobile: true, hasTouch: true });
    await ctx.route(/^(?!http:\/\/localhost)/, r => /open-meteo/.test(r.request().url())
      ? r.fulfill({ contentType: 'application/json', body: sampleMeteo(r.request().url()) }) : r.abort());
    await ctx.addInitScript(l => { try { localStorage.setItem('si_lang', l); localStorage.setItem('si_lang_hint', '1'); } catch (e) {} }, lang);
    const p = await ctx.newPage();
    // The slope profile, from the station's own page.
    await p.goto(BASE + STATION[lang] + slug + '/');
    await p.waitForTimeout(1200);
    await p.locator('.run-item').filter({ hasText: RUN }).first().click();
    await p.waitForTimeout(1800);
    await p.locator('.run-profile:visible').first().screenshot({ path: path.join(OUT, `profile-${lang}.jpg`), type: 'jpeg', quality: 88 });
    // The snow summary: headline and the four tiles, without the dated days.
    await p.goto(BASE + HOME[lang] + '?estacion=' + BAQ);
    await p.waitForSelector('#snow-forecast .snow-tiles', { timeout: 20000 });
    await p.waitForTimeout(800);
    await p.addStyleTag({ content: '.dash-tabbar, .lang-hint, .install-hint { display: none !important; }' });
    const box = await p.evaluate(() => {
      const r = ['.snow-head', '.snow-tiles'].map(s => document.querySelector('#snow-forecast ' + s).getBoundingClientRect());
      const x = Math.min(r[0].left, r[1].left) - 10, y = r[0].top - 3;
      return { x, y: y + window.scrollY, width: Math.max(r[0].right, r[1].right) + 10 - x, height: r[1].bottom + 10 - y };
    });
    await p.screenshot({ path: path.join(OUT, `snow-${lang}.jpg`), type: 'jpeg', quality: 88, clip: box, fullPage: true });
    console.log(lang, 'ok');
    await ctx.close();
  }
  await b.close();
})();

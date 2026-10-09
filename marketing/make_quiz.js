// "3 estaciones, ¿cuántas aciertas?": several resorts in one video, each with
// a short countdown and then its name on screen, from frames already drawn by
// make_video.js (/tmp/video-<name>/frames, one eased full turn in 240 frames).
// The user's idea (9 Oct): people stay to see if they got it right.
//
//   node marketing/make_quiz.js --out marketing/videos/quiz-1.mp4 \
//     --items "formigal-3d|España|Formigal;val-thorens|Francia|Val Thorens;zermatt|Suiza|Zermatt" \
//     [--guess 5] [--reveal 1.5] [--hook "3 estaciones.\n5 segundos cada una.\n¿Cuántas aciertas?"]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const OUT = arg('out');
const ITEMS = arg('items', '').split(';').filter(Boolean).map(s => { const [name, hint, answer] = s.split('|'); return { name, hint, answer }; });
const GUESS = +arg('guess', 5), REVEAL = +arg('reveal', 1.5), SEG = GUESS + REVEAL;
const HOOK = arg('hook', `${ITEMS.length} estaciones.\n${GUESS} segundos cada una.\n¿Cuántas aciertas?`).replace(/\\n/g, '\n');
const CTA = arg('cta', '¿Cuántas aciertas? Comenta 👇'), SITE = arg('site', 'skiinfoapp.com');
const FPS_IN = 20;   // 240 frames of a full turn: 6.5 s shows ~195°
const W = 540, H = 960, BASE = 'http://localhost:8903';
if (!OUT || !ITEMS.length) throw new Error('--out and --items are required');
const work = fs.mkdtempSync('/tmp/quiz-');

const CSS = `
  html, body { margin: 0; background: transparent; }
  #o { position: fixed; inset: 0; font-family: 'Barlow Condensed', sans-serif; color: #fff; }
  .top { position: absolute; top: 0; left: 0; right: 0; padding: 70px 28px 60px; text-align: center;
    background: linear-gradient(rgba(0,0,0,0.62), rgba(0,0,0,0)); }
  .title { font-size: 50px; font-weight: 700; line-height: 1.0; text-transform: uppercase; letter-spacing: 0.5px; text-shadow: 0 3px 14px rgba(0,0,0,0.7); }
  .hint { display: inline-block; margin-top: 16px; font-size: 27px; font-weight: 700; padding: 6px 16px; border-radius: 999px;
    background: rgba(255,255,255,0.18); border: 1.5px solid rgba(255,255,255,0.55); text-shadow: 0 2px 8px rgba(0,0,0,0.6); }
  .count { position: absolute; left: 50%; top: 245px; transform: translateX(-50%); width: 104px; height: 104px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 66px; font-weight: 700; line-height: 1;
    background: rgba(10,20,35,0.55); border: 4px solid #ffd257; text-shadow: 0 2px 10px rgba(0,0,0,0.6); }
  .count.last { border-color: #ff5a4f; }
  .answer { position: absolute; left: 24px; right: 24px; top: 380px; text-align: center; }
  .answer span { display: inline-block; padding: 10px 26px 12px; border-radius: 18px; background: #1f9d55; border: 3px solid #fff;
    font-size: 58px; font-weight: 700; line-height: 1.05; text-transform: uppercase; box-shadow: 0 10px 30px rgba(0,0,0,0.45); }
  .bottom { position: absolute; left: 0; right: 0; bottom: 0; padding: 70px 28px 300px; text-align: center;
    background: linear-gradient(rgba(0,0,0,0), rgba(0,0,0,0.45) 60%, rgba(0,0,0,0)); }
  .cta { font-size: 34px; font-weight: 700; text-shadow: 0 3px 12px rgba(0,0,0,0.7); }
  .site { margin-top: 6px; font-size: 22px; font-weight: 600; opacity: 0.9; text-shadow: 0 2px 8px rgba(0,0,0,0.7); }
  .credit { position: absolute; left: 0; right: 0; bottom: 248px; text-align: center; font-family: 'IBM Plex Sans', sans-serif; font-size: 10.5px; opacity: 0.75; }
  .hook { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; padding: 0 34px; text-align: center; white-space: pre-line;
    background: rgba(0,0,0,0.6); font-size: 60px; font-weight: 700; line-height: 1.05; text-transform: uppercase; text-shadow: 0 4px 18px rgba(0,0,0,0.8); }
`;
const esc = t => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium' });
  const page = await (await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 2 })).newPage();
  if (process.env.DEBUG) { page.on('request', r => console.log('req', r.url())); page.on('requestfailed', r => console.log('FAIL', r.url(), r.failure().errorText)); page.on('requestfinished', r => console.log('ok', r.url())); }
  const fonts = fs.readFileSync(path.join(__dirname, '..', 'docs', 'index.html'), 'utf8').match(/@font-face[^}]*}/g).join('\n')
    .replace(/font-display: optional/g, 'font-display: block');
  async function png(file, inner) {
    // Served from the local site (docs/), so the fonts load from the same origin.
    const html = `<!doctype html><meta charset="utf-8"><style>${fonts}${CSS}</style><div id="o">${inner}</div>`;
    await page.route(BASE + '/__quiz', r => r.fulfill({ body: html, contentType: 'text/html' }));
    await page.goto(BASE + '/__quiz');
    await page.unroute(BASE + '/__quiz');
    await page.evaluate(() => Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 5000))]));
    await page.screenshot({ path: path.join(work, file), omitBackground: true });
  }
  const bottom = `<div class="bottom"><div class="cta">${esc(CTA)}</div>${SITE ? `<div class="site">${esc(SITE)}</div>` : ''}</div>
    <div class="credit">© OpenStreetMap (ODbL) · OpenSkiMap · Esri, Maxar, Earthstar Geographics · Terrain Tiles</div>`;
  await png('hook.png', `<div class="hook">${esc(HOOK)}</div>`);
  for (let n = GUESS; n >= 1; n--) await png(`c${n}.png`, `<div class="count${n <= 2 ? ' last' : ''}">${n}</div>`);
  for (const [i, it] of ITEMS.entries()) {
    await png(`base${i}.png`, `<div class="top"><div class="title">¿Qué estación es?</div><div class="hint">${i + 1}/${ITEMS.length} · ${esc(it.hint)}</div></div>` + bottom);
    await png(`ans${i}.png`, `<div class="answer"><span>✅ ${esc(it.answer)}</span></div>`);
  }
  await browser.close();

  const ff = execFileSync('python3', ['-c', 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())']).toString().trim();
  const segs = [];
  for (const [i, it] of ITEMS.entries()) {
    const inputs = ['-framerate', String(FPS_IN), '-i', `/tmp/video-${it.name}/frames/%04d.jpg`];
    const chain = [`[0]minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=1080:1920:flags=lanczos[m]`];
    let v = '[m]', k = 1;
    const over = (file, enable) => {
      inputs.push('-loop', '1', '-i', path.join(work, file));
      chain.push(`${v}[${k}]overlay${enable ? `=enable='${enable}'` : ''}[o${k}]`);
      v = `[o${k}]`; k++;
    };
    over(`base${i}.png`);
    for (let n = GUESS; n >= 1; n--) { const a = GUESS - n; over(`c${n}.png`, `between(t,${a},${a + 1})`); }
    over(`ans${i}.png`, `gte(t,${GUESS})`);
    if (i === 0) over('hook.png', 'lt(t,1.5)');
    const seg = path.join(work, `seg${i}.mp4`);
    execFileSync(ff, ['-y', '-loglevel', 'error', ...inputs, '-filter_complex', chain.join(';'), '-map', v, '-t', String(SEG),
      '-r', '30', '-c:v', 'libx264', '-crf', '21', '-pix_fmt', 'yuv420p', seg], { stdio: 'inherit' });
    segs.push(seg);
    console.log('segment', i + 1, 'of', ITEMS.length);
  }
  const list = path.join(work, 'list.txt');
  fs.writeFileSync(list, segs.map(s => `file '${s}'`).join('\n') + '\n');
  execFileSync(ff, ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', '-movflags', '+faststart', OUT], { stdio: 'inherit' });
  for (const [t, suf] of [[0.5, 'a'], [3, 'b'], [GUESS + 0.6, 'c']]) {
    execFileSync(ff, ['-y', '-loglevel', 'error', '-ss', String(t), '-i', OUT, '-frames:v', '1', '-q:v', '3', OUT.replace(/\.mp4$/, `-preview-${suf}.jpg`)]);
  }
  fs.rmSync(work, { recursive: true, force: true });
  console.log('done:', OUT);
})().catch(e => { console.error(e); process.exit(1); });

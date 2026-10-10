// Shorter "¿Qué estación de esquí es?" variants from frames already drawn by
// make_video.js (/tmp/video-<name>/frames: 240 frames of one full, eased turn),
// to test what keeps people watching (the first video: 4.8 s average of 20 s,
// 3.8 % to the end). No re-rendering: ~1-2 min each.
//
//   node marketing/make_variant.js --name sierra-nevada --hint España --out marketing/videos/sierra-nevada-v1.mp4 \
//     [--seconds 12] [--countdown 10] [--hook "¿La adivinas en 10 segundos?"] [--reveal 1]
//
// What's in it:
// - the whole turn in --seconds (default 12): the last frame meets the first,
//   and there's no closing card, so it loops seamlessly (replays count);
// - --hook: big text over the first 1.6 s, the reason to stay;
// - --countdown N: a number counting down to 0 ("⏱") over the last N seconds;
// - --reveal 1: the first 2 s start zoomed in on the middle and pull back
//   (movement from the very first frame);
// - the call to comment a third of the way up (above TikTok's caption), the
//   site's name small under it, and the map credits.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');

const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const NAME = arg('name'), OUT = arg('out');
const FRAMES = arg('frames', `/tmp/video-${NAME}/frames`);
const SECONDS = +arg('seconds', 12), COUNT = +arg('countdown', 0), REVEAL = arg('reveal', '0') === '1';
const HOOK_STYLE = arg('hook-style', 'top');
const HOOK = arg('hook', ''), HINT = arg('hint', ''), TITLE = arg('title', '¿Qué estación\nde esquí es?');
const CTA = arg('cta', 'Respuesta en los comentarios 👇'), SITE = arg('site', 'skiinfoapp.com');
const W = 540, H = 960, BASE = 'http://localhost:8903';   // the site served from docs/ (make_video.sh starts it)   // CSS px; x2 = 1080x1920
if (!NAME || !OUT) throw new Error('--name and --out are required');
const work = fs.mkdtempSync('/tmp/variant-');

const CSS = `
  html, body { margin: 0; background: transparent; }
  #o { position: fixed; inset: 0; font-family: 'Barlow Condensed', sans-serif; color: #fff; }
  .top { position: absolute; top: 0; left: 0; right: 0; padding: 70px 28px 60px; text-align: center;
    background: linear-gradient(rgba(0,0,0,0.62), rgba(0,0,0,0)); }
  .title { white-space: pre-line; font-size: 50px; font-weight: 700; line-height: 1.0; text-transform: uppercase; letter-spacing: 0.5px; text-shadow: 0 3px 14px rgba(0,0,0,0.7); }
  .hint { display: inline-block; margin-top: 16px; font-size: 27px; font-weight: 700; padding: 6px 16px; border-radius: 999px;
    background: rgba(255,255,255,0.18); border: 1.5px solid rgba(255,255,255,0.55); text-shadow: 0 2px 8px rgba(0,0,0,0.6); }
  .count { position: absolute; left: 50%; top: 285px; transform: translateX(-50%); width: 104px; height: 104px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 66px; font-weight: 700; line-height: 1;
    background: rgba(10,20,35,0.55); border: 4px solid #ffd257; text-shadow: 0 2px 10px rgba(0,0,0,0.6); }
  .count.last { border-color: #ff5a4f; }
  .bottom { position: absolute; left: 0; right: 0; bottom: 0; padding: 70px 28px 300px; text-align: center;
    background: linear-gradient(rgba(0,0,0,0), rgba(0,0,0,0.45) 60%, rgba(0,0,0,0)); }
  .cta { font-size: 34px; font-weight: 700; text-shadow: 0 3px 12px rgba(0,0,0,0.7); }
  .site { margin-top: 6px; font-size: 22px; font-weight: 600; opacity: 0.9; text-shadow: 0 2px 8px rgba(0,0,0,0.7); }
  .credit { position: absolute; left: 0; right: 0; bottom: 248px; text-align: center; font-family: 'IBM Plex Sans', sans-serif; font-size: 10.5px; opacity: 0.75; }
  .title.hooktop { color: #ffd257; }
  .hook { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; padding: 0 34px; text-align: center;
    background: rgba(0,0,0,0.55); font-size: 62px; font-weight: 700; line-height: 1.02; text-transform: uppercase; text-shadow: 0 4px 18px rgba(0,0,0,0.8); }
`;
const esc = t => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium' });
  const page = await (await browser.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: 2 })).newPage();
  const fonts = fs.readFileSync(path.join(__dirname, '..', 'docs', 'index.html'), 'utf8').match(/@font-face[^}]*}/g).join('\n')
    .replace(/font-display: optional/g, 'font-display: block');
  async function png(file, inner) {
    // Served from the local site (docs/), so the fonts load from the same origin.
    const html = `<!doctype html><meta charset="utf-8"><style>${fonts}${CSS}</style><div id="o">${inner}</div>`;
    await page.route(BASE + '/__variant', r => r.fulfill({ body: html, contentType: 'text/html' }));
    await page.goto(BASE + '/__variant');
    await page.unroute(BASE + '/__variant');
    await page.evaluate(() => Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 5000))]));
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(work, file), omitBackground: true });
  }
  const top = `<div class="top"><div class="title">${esc(TITLE)}</div>${HINT ? `<div class="hint">${esc(HINT)}</div>` : ''}</div>`;
  const bottom = `<div class="bottom"><div class="cta">${esc(CTA)}</div>${SITE ? `<div class="site">${esc(SITE)}</div>` : ''}</div>
    <div class="credit">© OpenStreetMap (ODbL) · OpenSkiMap · Esri, Maxar, Earthstar Geographics · Terrain Tiles</div>`;
  await png('base.png', top + bottom);
  // The hook in the title's place, over the bright map: a dark full-screen card
  // lost most viewers in the first second (quiz-1: 951 views, 4.0 s average).
  // --hook-style card brings the old darkened card back.
  if (HOOK && HOOK_STYLE === 'card') await png('hook.png', `<div class="hook">${esc(HOOK)}</div>`);
  if (HOOK && HOOK_STYLE !== 'card') await png('basehook.png', `<div class="top"><div class="title hooktop">${esc(HOOK)}</div>${HINT ? `<div class="hint">${esc(HINT)}</div>` : ''}</div>` + bottom);
  for (let n = COUNT; n >= 0 && COUNT; n--) await png(`c${n}.png`, `<div class="count${n <= 3 ? ' last' : ''}">${n === 0 ? '⏱' : n}</div>`);
  await browser.close();

  // The video: the 240 frames over SECONDS, interpolated to 30 fps.
  const nFrames = fs.readdirSync(FRAMES).filter(f => f.endsWith('.jpg')).length;
  const inRate = (nFrames / SECONDS).toFixed(4);
  const ff = execFileSync('python3', ['-c', 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())']).toString().trim();
  const inputs = ['-framerate', inRate, '-i', path.join(FRAMES, '%04d.jpg')];
  const chain = [];
  let v = '[0]';
  // Pull back from 2.2x on the middle over the first 2 s (scaled up first so the zoom doesn't judder).
  if (REVEAL) {
    chain.push(`${v}scale=2160:3840:flags=lanczos,zoompan=z='if(lt(it,2),1+1.2*pow(1-it/2,2),1)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=${inRate}[z]`);
    v = '[z]';
  }
  chain.push(`${v}minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=1080:1920:flags=lanczos[m]`);
  v = '[m]';
  let k = 1;
  const over = (file, enable) => {
    inputs.push('-loop', '1', '-i', path.join(work, file));
    chain.push(`${v}[${k}]overlay${enable ? `=enable='${enable}'` : ''}[o${k}]`);
    v = `[o${k}]`; k++;
  };
  if (HOOK && HOOK_STYLE !== 'card') { over('basehook.png', 'lt(t,1.6)'); over('base.png', 'gte(t,1.6)'); }
  else over('base.png');
  if (COUNT) {
    // N .. 1 one second each, ending exactly at SECONDS; "⏱" for the last half second.
    const start = SECONDS - COUNT - 0.5;
    for (let n = COUNT; n >= 1; n--) { const a = start + (COUNT - n); over(`c${n}.png`, `between(t,${a.toFixed(2)},${(a + 1).toFixed(2)})`); }
    over('c0.png', `gte(t,${(SECONDS - 0.5).toFixed(2)})`);
  }
  if (HOOK && HOOK_STYLE === 'card') over('hook.png', 'lt(t,1.6)');
  execFileSync(ff, ['-y', '-loglevel', 'error', ...inputs, '-filter_complex', chain.join(';'), '-map', v,
    '-t', String(SECONDS), '-r', '30', '-c:v', 'libx264', '-crf', '21', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], { stdio: 'inherit' });
  // Preview stills: just after the hook, and mid-countdown.
  for (const [t, suf] of [[0.4, 'a'], [Math.min(SECONDS - 1, 4), 'b']]) {
    execFileSync(ff, ['-y', '-loglevel', 'error', '-ss', String(t), '-i', OUT, '-frames:v', '1', '-q:v', '3', OUT.replace(/\.mp4$/, `-preview-${suf}.jpg`)]);
  }
  fs.rmSync(work, { recursive: true, force: true });
  console.log('done:', OUT);
})().catch(e => { console.error(e); process.exit(1); });

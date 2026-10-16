// Renderiza index.html cuadro por cuadro y lo codifica con ffmpeg.
//   node render.js                 -> output/ligier-promo.mp4 (con música si existe output/soundtrack.wav)
//   node render.js --stills 1,7,20 -> PNGs de prueba en output/stills/
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); } catch { ({ chromium } = require('/opt/node22/lib/node_modules/playwright')); }

const FPS = 30;
const WORKERS = 4;
const ROOT = __dirname;
const OUT = path.join(ROOT, 'output');
const URL = 'file://' + path.join(ROOT, 'index.html') + '?render';
const launchOpts = fs.existsSync('/opt/pw-browsers/chromium') ? {} : {};

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(URL);
  await page.evaluate(() => window.ready);
  return page;
}
const grab = (page, t) => page.evaluate(t => {
  window.renderAt(t);
  return document.getElementById('c').toDataURL('image/jpeg', 0.94);
}, t);

function ffmpeg(args) {
  const p = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...args], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => p.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c))));
  return { p, done };
}

async function stills(browser, times) {
  const dir = path.join(OUT, 'stills'); fs.mkdirSync(dir, { recursive: true });
  const page = await openPage(browser);
  for (const t of times) {
    const b64 = (await grab(page, t)).split(',')[1];
    fs.writeFileSync(path.join(dir, `t${String(t).replace('.', '_')}.jpg`), Buffer.from(b64, 'base64'));
  }
}

async function video(browser) {
  const page0 = await openPage(browser);
  const duration = await page0.evaluate(() => window.DURATION);
  await page0.close();
  const total = Math.round(duration * FPS);
  const per = Math.ceil(total / WORKERS);
  const segs = [];
  const t0 = Date.now();
  await Promise.all(Array.from({ length: WORKERS }, async (_, w) => {
    const a = w * per, b = Math.min(total, a + per);
    const seg = path.join(OUT, `seg${w}.mp4`); segs[w] = seg;
    const page = await openPage(browser);
    const { p, done } = ffmpeg(['-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', seg]);
    for (let f = a; f < b; f++) {
      const b64 = (await grab(page, f / FPS)).split(',')[1];
      if (!p.stdin.write(Buffer.from(b64, 'base64'))) await new Promise(r => p.stdin.once('drain', r));
      if (w === 0 && (f - a) % 60 === 0) console.log(`  ${Math.round((f - a) / (b - a) * 100)}%  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
    }
    p.stdin.end(); await done; await page.close();
  }));
  const list = path.join(OUT, 'segs.txt');
  fs.writeFileSync(list, segs.map(s => `file '${s}'`).join('\n'));
  const music = path.join(OUT, 'soundtrack.wav');
  const final = path.join(OUT, 'ligier-promo.mp4');
  const args = ['-f', 'concat', '-safe', '0', '-i', list];
  if (fs.existsSync(music)) args.push('-i', music, '-c:a', 'aac', '-b:a', '192k', '-shortest');
  args.push('-c:v', 'copy', '-movflags', '+faststart', final);
  await ffmpeg(args).done;
  for (const s of segs) fs.unlinkSync(s); fs.unlinkSync(list);
  console.log(`Listo: ${final}  (${total} cuadros, ${((Date.now() - t0) / 1000).toFixed(0)}s)`);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch(launchOpts);
  try {
    const i = process.argv.indexOf('--stills');
    if (i > 0) await stills(browser, process.argv[i + 1].split(',').map(Number));
    else await video(browser);
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });

// Render reel.html frame by frame with headless Chromium.
//   node render.js <outDir> [fps=30] [t0] [t1]        full/partial render
//   node render.js <outDir> stills 1.0 5.2 ...         single preview frames
// Expects the page (PAGE env, default reel.html) to be served at http://127.0.0.1:8765/.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const [out, mode, ...rest] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({
    executablePath: fs.existsSync('/opt/pw-browsers/chromium-1194/chrome-linux/chrome') ? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' : undefined,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
  page.on('pageerror', e => console.error('pageerror:', e.message));
  await page.goto('http://127.0.0.1:8765/' + (process.env.PAGE || 'reel.html'));
  await page.evaluate(() => window.ready);
  const shot = async (t, file) => {
    await page.evaluate(t => window.renderFrame(t), t);
    await page.screenshot({ path: file, type: 'jpeg', quality: 92 });
  };
  if (mode === 'stills') {
    for (const s of rest) await shot(parseFloat(s), path.join(out, `still-${s}.jpg`));
  } else {
    const fps = parseFloat(mode || '30');
    const t0 = parseFloat(rest[0] || '0'), t1 = parseFloat(rest[1] || '50');
    const n0 = Math.round(t0 * fps), n1 = Math.round(t1 * fps);
    for (let i = n0; i < n1; i++) {
      await shot(i / fps, path.join(out, `f${String(i).padStart(5, '0')}.jpg`));
      if (i % 150 === 0) console.log('frame', i);
    }
  }
  await browser.close();
})();

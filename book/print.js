// Print built volumes to PDF.  node print.js <out dir> <vol numbers, e.g. 2,4> [preview page numbers]
// Serves <out dir> itself; writes volN.pdf, and volN-pXXX.png previews of the listed pages.
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const [dir, vols, previews] = process.argv.slice(2);
const TYPES = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.png': 'image/png',
  '.jpg': 'image/jpeg', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.json': 'application/json' };
const server = http.createServer((req, res) => {
  const p = path.join(dir, decodeURIComponent(req.url.split('?')[0]));
  fs.readFile(p, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' }); res.end(data);
  });
}).listen(8770, '127.0.0.1');

(async () => {
  const browser = await chromium.launch();
  for (const v of vols.split(',')) {
    const page = await browser.newPage({ viewport: { width: 794, height: 1123 } });
    page.on('pageerror', e => console.error('pageerror', e.message));
    await page.goto(`http://127.0.0.1:8770/vol${v}.html`, { timeout: 0 });
    await page.waitForFunction(() => window.BOOK_READY === true, null, { timeout: 0, polling: 500 });
    await page.evaluate(() => Promise.all(Array.from(document.images).map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; }))));
    const n = await page.evaluate(() => window.PAGE_COUNT);
    console.log(`vol${v}: ${n} pages`);
    for (const k of (previews || '').split(',').filter(Boolean).map(Number)) {
      const el = (await page.$$('.page'))[k - 1];
      if (el) await el.screenshot({ path: path.join(dir, `vol${v}-p${String(k).padStart(3, '0')}.png`) });
    }
    await page.pdf({ path: path.join(dir, `vol${v}.pdf`), preferCSSPageSize: true, printBackground: true, timeout: 0 });
    fs.writeFileSync(path.join(dir, `vol${v}.pages.json`), JSON.stringify(await page.evaluate(() => ({ count: window.PAGE_COUNT, chapters: window.FIRST_PAGES }))));
    await page.close();
  }
  await browser.close();
  server.close();
})();

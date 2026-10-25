// Photograph many mcview scenes in one browser session.
//   node shoot.js jobs.json      jobs: [{scene, out, shots: [shot, ...]}], out gets -<i>.png per shot
// Expects render/mcview.html served at http://127.0.0.1:8766/render/mcview.html (scenes relative to it).
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2]));
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  for (const j of jobs) {
    const p = await b.newPage({ viewport: { width: 1000, height: 1000 } });
    p.on('pageerror', e => console.error('pageerror', j.scene, e.message));
    await p.goto(`http://127.0.0.1:8766/render/mcview.html?scene=../${j.scene}&w=1000&h=1000&bg=transparent`);
    await p.evaluate(() => window.ready);
    await p.addStyleTag({ content: 'html, body { background: transparent !important; }' });
    for (const [i, s] of j.shots.entries()) {
      await p.evaluate(s => window.shot(s), s);
      await p.screenshot({ path: j.out.replace('.png', `-${i}.png`), omitBackground: true });
    }
    await p.close();
    console.log('shot', j.scene);
  }
  await b.close();
})();

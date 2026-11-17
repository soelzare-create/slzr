// QA for a cinematic story page. Usage: node qa.js <file-or-url> [outdir]
// Needs playwright. In Claude cloud sessions launch the preinstalled Chromium (see CHROME below).
// Steps through the page one wheel tick at a time on desktop and phone, saves a screenshot per stop,
// and reports: JS errors, horizontal overflow, stop count, reduced-motion static mode, em/en dashes in visible text.
const { chromium } = require('playwright');
const fs = require('fs');
const target = process.argv[2], out = process.argv[3] || 'qa-out';
const url = /^https?:|^file:/.test(target) ? target : 'file://' + require('path').resolve(target);
const CHROME = fs.existsSync('/opt/pw-browsers') ? (fs.readdirSync('/opt/pw-browsers').filter(d => d.startsWith('chromium-')).map(d => `/opt/pw-browsers/${d}/chrome-linux/chrome`).find(fs.existsSync)) : undefined;
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(CHROME ? { executablePath: CHROME, ignoreDefaultArgs: ['--headless=old'], args: ['--headless=new'] } : {});
  for (const [tag, w, h, touch] of [['desktop', 1440, 900, false], ['phone', 390, 844, true]]) {
    const c = await b.newContext({ viewport: { width: w, height: h }, hasTouch: touch, isMobile: touch });
    const p = await c.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.goto(url + (url.includes('?') ? '' : '?qa')); await p.waitForTimeout(1200);
    await p.mouse.move(w / 2, h / 2);
    let prev = -1, n = 0;
    for (let i = 0; i < 80; i++) {
      await p.mouse.wheel(0, 100); await p.waitForTimeout(1500);
      const y = await p.evaluate(() => Math.round(scrollY));
      if (y === prev) break; prev = y; n++;
      await p.screenshot({ path: `${out}/${tag}_${String(i).padStart(2, '0')}.png` });
    }
    const overflow = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    console.log(`${tag}: ${n} stops, horizontal overflow ${overflow}px, errors ${JSON.stringify(errs)}`);
    await c.close();
  }
  const c = await b.newContext({ viewport: { width: 1280, height: 800 }, reducedMotion: 'reduce' });
  const p = await c.newPage(); await p.goto(url); await p.waitForTimeout(800);
  console.log('reduced motion static:', await p.evaluate(() => document.body.classList.contains('no-story')));
  await p.screenshot({ path: `${out}/reduced-motion-full.png`, fullPage: true });
  const dashes = await p.evaluate(() => (document.body.innerText.match(/[–—]/g) || []).length);
  const words = await p.evaluate(() => [...document.querySelectorAll('.cap')].map(c => c.innerText.trim().split(/\s+/).length));
  console.log('em/en dashes in visible text:', dashes, '| words per caption:', JSON.stringify(words));
  await b.close();
})();

// Usage: NODE_PATH=$(npm root -g) node render.cjs input.html output.pdf
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [input, output] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.emulateMedia({ media: 'print' });
  await page.goto('file://' + path.resolve(input), { waitUntil: 'networkidle' });
  // Load every declared font before printing; a font that arrives mid-print can cut the PDF short.
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.fonts].map((f) => f.load().catch(() => null)));
    await document.fonts.ready;
    document.body.getBoundingClientRect();
  });
  await page.waitForTimeout(1000);
  await page.pdf({
    path: output,
    preferCSSPageSize: true,
    printBackground: true,
    outline: true,
    tagged: true,
  });
  await browser.close();
})();

import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const landingUrl = process.argv[2] || 'http://127.0.0.1:8771/';
const outPath = process.argv[3] || join(__dirname, '../landing/assets/.hero-capture.png');

const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 2 });
await page.goto(landingUrl, { waitUntil: 'networkidle0', timeout: 60000 });
await page.addStyleTag({
  content: `
    body { background: #0a1628 !important; }
    .site-header, .hero-cta, .hero-desc, .eyebrow { visibility: hidden !important; }
    .hero-title { position: absolute; width: 1px; height: 1px; overflow: hidden; }
    .hero-scene { margin: 0 auto; max-width: 1100px; }
  `,
});

const el = await page.$('.hero-scene');
if (!el) throw new Error('.hero-scene not found');
const box = await el.boundingBox();
const pad = { top: 16, right: 16, bottom: 24, left: 16 };
await page.screenshot({
  path: outPath,
  clip: {
    x: Math.max(0, box.x - pad.left),
    y: Math.max(0, box.y - pad.top),
    width: box.width + pad.left + pad.right,
    height: box.height + pad.top + pad.bottom,
  },
});
await browser.close();
console.log('saved', outPath);

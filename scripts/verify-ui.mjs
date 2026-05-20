import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";

const baseUrl = process.env.PROMPTEER_WEB_URL ?? "http://127.0.0.1:3000/en";
const outDir = new URL("../.verify/screenshots/", import.meta.url);

await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
await page.goto(baseUrl, { waitUntil: "networkidle" });
await page.screenshot({ path: new URL("home.png", outDir).pathname, fullPage: true });
await browser.close();

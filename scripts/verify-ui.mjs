// Playwright-based screenshot helper for manual UI verification. Captures the
// main public, authenticated, and dev-only screens in desktop and mobile sizes.
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";

const webRequire = createRequire(
  new URL("../apps/web/package.json", import.meta.url),
);
const { chromium } = webRequire("@playwright/test");

const configuredUrl = new URL(
  process.env.PROMPTEER_WEB_URL ?? "http://localhost/en",
);
const origin = configuredUrl.origin;
const outDir = new URL("../.verify/screenshots/", import.meta.url);

const routes = [
  { name: "01-landing", path: "/en", auth: false },
  { name: "02-login", path: "/en/login", auth: false },
  { name: "03-coding-challenge", path: "/en/challenges/coding", auth: true },
  { name: "04-billing", path: "/en/billing", auth: true },
  { name: "05-board", path: "/en/board", auth: true },
  { name: "06-settings", path: "/en/profile", auth: true },
  { name: "07-mailbox", path: "/dev/mailbox", auth: false },
];

const viewports = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

function routeUrl(path) {
  return new URL(path, origin).toString();
}

async function ensureSeedLogin(page) {
  await page.goto(routeUrl("/dev/login-as/admin%40prompteer.dev"), {
    waitUntil: "domcontentloaded",
  });
  if (!page.url().endsWith("/en")) {
    throw new Error(
      `Seed login did not redirect to /en; current URL is ${page.url()}.`,
    );
  }
}

await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
const failures = [];

for (const viewport of viewports) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
  });
  const page = await context.newPage();
  let authenticated = false;

  page.on("console", (message) => {
    if (message.type() === "error") {
      failures.push(`[${viewport.name}] console error: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    failures.push(`[${viewport.name}] page error: ${error.message}`);
  });

  for (const route of routes) {
    if (route.auth && !authenticated) {
      await ensureSeedLogin(page);
      authenticated = true;
    }

    await page.goto(routeUrl(route.path), { waitUntil: "domcontentloaded" });
    if (route.auth && page.url().includes("/login")) {
      failures.push(
        `[${viewport.name}] ${route.path} redirected to login after seed auth.`,
      );
    }
    await page.locator("body").waitFor({ state: "visible" });
    await page.waitForLoadState("networkidle", { timeout: 5_000 }).catch(() => {
      // Some server-rendered pages keep background fetches open; visible body is
      // the screenshot readiness gate, while network idle is only a stabilizer.
    });
    await page.screenshot({
      path: new URL(`${route.name}-${viewport.name}.png`, outDir).pathname,
      fullPage: true,
    });
  }

  await context.close();
}

await browser.close();

if (failures.length > 0) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log(
  `Saved ${routes.length * viewports.length} screenshots to ${outDir.pathname}`,
);

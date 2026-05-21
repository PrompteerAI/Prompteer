// Playwright-based screenshot helper for the legacy-preview frontend. It
// captures the bounded set of legacy screenshots referenced by the README.
import { mkdir } from "node:fs/promises";
import { createRequire } from "node:module";
import { resolve } from "node:path";

const webRequire = createRequire(
  new URL("../apps/web/package.json", import.meta.url),
);
const { chromium } = webRequire("@playwright/test");

const configuredUrl = new URL(
  process.env.PROMPTEER_LEGACY_WEB_URL ??
    `http://localhost:${process.env.WEB_LEGACY_PORT ?? "3001"}/en`,
);
const origin = configuredUrl.origin;
const outDir = resolve(
  process.cwd(),
  process.env.PROMPTEER_LEGACY_SCREENSHOT_DIR || ".verify/screenshots/legacy",
);

const desktop = { width: 1440, height: 900 };
const mobile = { width: 390, height: 844 };

const captures = [
  {
    name: "09-legacy-home",
    path: "/en",
    viewport: desktop,
  },
  {
    name: "10-legacy-coding-category",
    path: "/en/category/coding",
    viewport: desktop,
  },
  {
    name: "11-legacy-board",
    path: "/en/board",
    viewport: desktop,
  },
  {
    name: "12-legacy-login",
    path: "/en/login",
    viewport: desktop,
  },
  {
    name: "13-legacy-problem-runner",
    path: "/en/category/coding",
    viewport: desktop,
    authenticated: true,
    afterGoto: async (page) => {
      await page.getByRole("link", { name: /challenge now/i }).click();
      await page.waitForURL(/\/en\/coding\/problem\//);
      await page
        .getByRole("textbox", { name: "Prompt" })
        .fill(
          "Explain the constraints, outline edge cases, and provide a concise implementation plan.",
        );
      await page.getByRole("checkbox", { name: /publish this run/i }).uncheck();
      await page.getByRole("button", { name: "Run prompt" }).click();
      await page.getByText("Private run").waitFor({
        timeout: 15_000,
      });
    },
  },
  {
    name: "14-legacy-billing",
    path: "/en/billing",
    viewport: desktop,
    authenticated: true,
  },
  {
    name: "15-legacy-mobile-home",
    path: "/en",
    viewport: mobile,
  },
  {
    name: "16-legacy-mobile-coding",
    path: "/en/category/coding",
    viewport: mobile,
  },
];

function routeUrl(path) {
  return new URL(path, origin).toString();
}

async function ensureSeedLogin(page) {
  await page.goto(routeUrl("/dev/login-as/admin%40prompteer.dev?locale=en"), {
    waitUntil: "domcontentloaded",
  });
  const currentPath = new URL(page.url()).pathname;
  if (currentPath !== "/en") {
    throw new Error(
      `Legacy seed login did not redirect to /en; current URL is ${page.url()}.`,
    );
  }
}

async function hideNextDevTools(page) {
  await page.addStyleTag({
    content: `
      nextjs-portal,
      [data-nextjs-dev-tools],
      [data-nextjs-toast],
      [data-nextjs-dialog-overlay],
      [data-nextjs-dialog],
      [aria-label="Next.js static indicator"],
      [aria-label="Next.js development tools"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
      }
    `,
  });
}

await mkdir(outDir, { recursive: true });

const browser = await chromium.launch();
const failures = [];

for (const capture of captures) {
  const context = await browser.newContext({
    viewport: capture.viewport,
  });
  const page = await context.newPage();

  page.on("console", (message) => {
    if (message.type() === "error") {
      failures.push(`[${capture.name}] console error: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    failures.push(`[${capture.name}] page error: ${error.message}`);
  });

  if (capture.authenticated) {
    await ensureSeedLogin(page);
  }

  await page.goto(routeUrl(capture.path), { waitUntil: "domcontentloaded" });
  await hideNextDevTools(page);
  if (capture.authenticated && page.url().includes("/login")) {
    failures.push(`${capture.name} redirected to login after seed auth.`);
  }
  if (capture.afterGoto) {
    await capture.afterGoto(page);
    await hideNextDevTools(page);
  }
  await page.locator("body").waitFor({ state: "visible" });
  await page.waitForLoadState("networkidle", { timeout: 5_000 }).catch(() => {
    // Some server-rendered pages keep background fetches open; visible body is
    // the screenshot readiness gate, while network idle is only a stabilizer.
  });
  await hideNextDevTools(page);
  await page.screenshot({
    path: resolve(outDir, `${capture.name}.png`),
    fullPage: true,
  });

  await context.close();
}

await browser.close();

if (failures.length > 0) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log(`Saved ${captures.length} legacy screenshots to ${outDir}`);

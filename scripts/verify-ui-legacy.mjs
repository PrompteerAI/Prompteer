// Playwright-based screenshot helper for the legacy-preview frontend. It
// captures the bounded set of legacy screenshots referenced by the README.
import { mkdir, readdir, unlink } from "node:fs/promises";
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
const extraOutDir = resolve(
  process.cwd(),
  process.env.PROMPTEER_LEGACY_EXTRA_SCREENSHOT_DIR ||
    ".verify/screenshots/legacy-extra",
);

const desktop = { width: 1440, height: 900 };
const mobile = { width: 390, height: 844 };

const hideNextDevToolsStyle = `
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
`;

const captures = [
  {
    name: "09-legacy-home",
    path: "/en",
    viewport: desktop,
    expectedText: ["Top Challenges", "Product hero image prompt"],
  },
  {
    name: "10-legacy-coding-category",
    path: "/en/category/coding",
    viewport: desktop,
    expectedText: ["Algorithm", "FizzBuzz prompt repair"],
  },
  {
    name: "11-legacy-board",
    path: "/en/board",
    viewport: desktop,
    expectedText: ["Board", "Shared questions and prompt runs"],
  },
  {
    name: "12-legacy-login",
    path: "/en/login",
    viewport: desktop,
    expectedText: ["Login", "Demo login"],
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
    expectedText: ["Prompt editor", "Private run"],
  },
  {
    name: "14-legacy-billing",
    path: "/en/billing",
    viewport: desktop,
    authenticated: true,
    expectedText: ["Prompteer Pro", "Billing email"],
  },
  {
    name: "15-legacy-mobile-home",
    path: "/en",
    viewport: mobile,
    expectedText: ["Top Challenges", "Challenge Category"],
    readme: false,
  },
  {
    name: "16-legacy-mobile-coding",
    path: "/en/category/coding",
    viewport: mobile,
    expectedText: ["Algorithm", "FizzBuzz prompt repair"],
    readme: false,
  },
  {
    name: "legacy-error-boundary",
    path: "/en/coding/problem/not-a-real-challenge",
    viewport: desktop,
    expectedText: ["Legacy preview interrupted", "Retry", "Reported"],
    readme: false,
    allowExpectedErrors: true,
    afterGoto: async (page) => {
      await page.getByRole("button", { name: "Report" }).click();
      await page.getByRole("button", { name: "Reported" }).waitFor({
        timeout: 10_000,
      });
    },
  },
];

function routeUrl(path) {
  return new URL(path, origin).toString();
}

async function clearPngFiles(directory) {
  try {
    const entries = await readdir(directory, { withFileTypes: true });
    await Promise.all(
      entries
        .filter((entry) => entry.isFile() && entry.name.endsWith(".png"))
        .map((entry) => unlink(resolve(directory, entry.name))),
    );
  } catch (error) {
    if (error && typeof error === "object" && "code" in error) {
      if (error.code === "ENOENT") {
        return;
      }
    }
    throw error;
  }
}

async function ensureSeedLogin(page) {
  await page.goto(routeUrl("/dev/login-as/admin%40prompteer.dev?locale=en"), {
    timeout: 60_000,
    waitUntil: "commit",
  });
  await page.waitForURL((url) => url.pathname === "/en", { timeout: 30_000 });
  const currentPath = new URL(page.url()).pathname;
  if (currentPath !== "/en") {
    throw new Error(
      `Legacy seed login did not redirect to /en; current URL is ${page.url()}.`,
    );
  }
}

async function settleForScreenshot(page) {
  await page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
  });
  await page.mouse.move(0, 0);
  await page.waitForTimeout(100);
}

await mkdir(outDir, { recursive: true });
await mkdir(extraOutDir, { recursive: true });
await clearPngFiles(outDir);
await clearPngFiles(extraOutDir);

const browser = await chromium.launch();
const failures = [];

for (const capture of captures) {
  const context = await browser.newContext({
    viewport: capture.viewport,
  });
  const page = await context.newPage();
  let allowExpectedErrors = Boolean(capture.allowExpectedErrors);

  page.on("console", (message) => {
    if (message.type() === "error" && !allowExpectedErrors) {
      failures.push(`[${capture.name}] console error: ${message.text()}`);
    }
  });
  page.on("pageerror", (error) => {
    if (!allowExpectedErrors) {
      failures.push(`[${capture.name}] page error: ${error.message}`);
    }
  });

  if (capture.authenticated) {
    await ensureSeedLogin(page);
  }

  await page.goto(routeUrl(capture.path), {
    timeout: 60_000,
    waitUntil: "commit",
  });
  if (capture.authenticated && page.url().includes("/login")) {
    failures.push(`${capture.name} redirected to login after seed auth.`);
  }
  if (capture.afterGoto) {
    await capture.afterGoto(page);
  }
  await page.locator("body").waitFor({ state: "visible" });
  for (const expectedText of capture.expectedText ?? []) {
    await page.getByText(expectedText).first().waitFor({
      state: "visible",
      timeout: 10_000,
    });
  }
  await page.waitForLoadState("networkidle", { timeout: 5_000 }).catch(() => {
    // Some server-rendered pages keep background fetches open; visible body is
    // the screenshot readiness gate, while network idle is only a stabilizer.
  });
  await settleForScreenshot(page);
  try {
    await page.screenshot({
      path: resolve(
        capture.readme === false ? extraOutDir : outDir,
        `${capture.name}.png`,
      ),
      fullPage: true,
      style: hideNextDevToolsStyle,
    });
  } finally {
    if (!capture.allowExpectedErrors) {
      allowExpectedErrors = false;
    }
  }

  await context.close();
}

await browser.close();

if (failures.length > 0) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log(
  `Saved ${captures.filter((capture) => capture.readme !== false).length} legacy screenshots to ${outDir}`,
);
console.log(
  `Saved ${captures.filter((capture) => capture.readme === false).length} legacy verification screenshots to ${extraOutDir}`,
);

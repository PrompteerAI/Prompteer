// Playwright-based screenshot helper for manual UI verification. Captures the
// main public, authenticated, and dev-only screens in desktop and mobile sizes.
import { mkdir, readdir, unlink } from "node:fs/promises";
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
const updateReadmeScreenshots =
  process.env.PROMPTEER_UPDATE_README_SCREENSHOTS === "1";
const readmeOutDir = new URL("../.verify/screenshots/readme/", import.meta.url);
const promotedReadmeOutDir = new URL("../docs/screenshots/", import.meta.url);

const routes = [
  {
    name: "01-landing",
    path: "/en",
    auth: false,
    expectedText: ["Prompt challenge workspace"],
    readme: true,
  },
  {
    name: "02-login",
    path: "/en/login",
    auth: false,
    expectedText: ["Sign in"],
    readme: true,
  },
  {
    name: "03-coding-challenge",
    path: "/en/challenges/coding",
    auth: true,
    expectedText: ["Prompt repair workspace", "FizzBuzz prompt repair"],
    readme: true,
  },
  {
    name: "04-prompt-editor",
    path: "/en/challenges/coding",
    auth: true,
    expectedText: ["Mock run result", "Run kept private"],
    readme: true,
    afterGoto: async (page) => {
      await page
        .getByRole("textbox", { name: "Prompt" })
        .fill(
          "Explain FizzBuzz rules, then produce concise Python with clear edge cases.",
        );
      await page.getByRole("checkbox", { name: /Publish to board/ }).uncheck();
      await page.getByRole("button", { name: "Run prompt" }).click();
      await page.getByText("Mock run result").waitFor({ timeout: 15_000 });
    },
  },
  {
    name: "05-billing-checkout",
    path: "/en/billing",
    auth: true,
    expectedText: ["Subscription checkout", "Checkout session"],
    readme: true,
  },
  {
    name: "06-board",
    path: "/en/board",
    auth: true,
    expectedText: ["Shared prompt reviews", "Public prompt shares"],
    readme: true,
  },
  {
    name: "07-mailbox",
    path: "/dev/mailbox",
    auth: false,
    expectedText: ["Mock mailbox"],
    readme: true,
  },
  {
    name: "08-settings",
    path: "/en/profile",
    auth: true,
    expectedText: ["Profile settings", "Integration mode"],
    readme: true,
  },
  {
    name: "17-board-share-detail",
    path: "/en/board",
    auth: true,
    expectedText: ["Prompt share detail", "Submitted prompt"],
    readme: true,
    afterGoto: async (page) => {
      await page
        .getByRole("link", { name: /Read prompt share:/ })
        .first()
        .click();
      await page.waitForURL(/\/en\/board\/shares\/[^/]+$/);
    },
  },
  {
    name: "18-board-post-detail",
    path: "/en/board",
    auth: true,
    expectedText: ["Question detail"],
    readme: true,
    afterGoto: async (page) => {
      await page
        .getByRole("link", { name: /Read question:/ })
        .first()
        .click();
      await page.waitForURL(/\/en\/board\/posts\/[^/]+$/);
    },
  },
  {
    name: "19-image-challenges",
    path: "/en/challenges/image",
    auth: true,
    expectedText: ["Image prompt challenges", "product-hero.png"],
    readme: true,
  },
  {
    name: "20-image-challenge-detail",
    path: "/en/challenges/image",
    auth: true,
    detailLinkName: /View details: Product hero image prompt/,
    expectedUrl: /\/en\/challenges\/image\/[^/]+$/,
    expectedText: [
      "Product hero image prompt",
      "Prompt execution",
      "Product hero",
      "Hero composition with product focus",
    ],
    readme: true,
  },
  {
    name: "21-video-challenges",
    path: "/en/challenges/video",
    auth: true,
    expectedText: ["Video prompt challenges", "launch-teaser.mp4"],
    readme: true,
  },
  {
    name: "22-video-challenge-detail",
    path: "/en/challenges/video",
    auth: true,
    detailLinkName: /View details: Launch teaser video prompt/,
    expectedUrl: /\/en\/challenges\/video\/[^/]+$/,
    expectedText: [
      "Launch teaser video prompt",
      "Prompt execution",
      "Launch teaser",
      "16:9 launch teaser storyboard",
    ],
    readme: true,
  },
  {
    name: "23-billing-success",
    path: "/en/billing",
    auth: true,
    authEmail: "free@prompteer.dev",
    expectedText: ["Checkout complete", "Payment status", "paid"],
    afterGoto: async (page) => {
      await page.getByRole("button", { name: /Start (new )?checkout/ }).click();
      await page
        .getByText("A local Stripe-compatible session is ready.")
        .waitFor({
          timeout: 15_000,
        });
      const sessionId = (
        await page
          .locator("dd", { hasText: /^cs_test_/ })
          .first()
          .innerText()
      ).trim();
      await page
        .getByRole("button", { name: "Complete mock checkout" })
        .click();
      await page.getByText("checkout.session.completed").waitFor({
        timeout: 15_000,
      });
      await page.goto(
        routeUrl(
          `/en/billing/success?session_id=${encodeURIComponent(sessionId)}`,
        ),
        { waitUntil: "domcontentloaded" },
      );
    },
  },
  {
    name: "24-primary-route-error",
    path: "/en?__verify_error_boundary=locale",
    auth: false,
    expectedText: [
      "Something went wrong",
      "An unexpected error interrupted this page.",
      "Retry",
      "Reported",
    ],
    allowExpectedErrors: true,
    afterGoto: async (page) => {
      await page.getByRole("button", { name: "Report" }).click();
      await page.getByRole("button", { name: "Reported" }).waitFor({
        timeout: 10_000,
      });
    },
  },
  {
    name: "25-primary-app-error",
    path: "/en/billing?__verify_error_boundary=app",
    auth: true,
    expectedText: [
      "Workspace interrupted",
      "An unexpected error interrupted this workspace route.",
      "Retry",
      "Reported",
    ],
    allowExpectedErrors: true,
    afterGoto: async (page) => {
      await page.getByRole("button", { name: "Report" }).click();
      await page.getByRole("button", { name: "Reported" }).waitFor({
        timeout: 10_000,
      });
    },
  },
];

const viewports = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

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

function routeUrl(path) {
  return new URL(path, origin).toString();
}

async function clearPngFiles(directoryUrl) {
  try {
    const entries = await readdir(directoryUrl, { withFileTypes: true });
    await Promise.all(
      entries
        .filter((entry) => entry.isFile() && entry.name.endsWith(".png"))
        .map((entry) => unlink(new URL(entry.name, directoryUrl))),
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

async function ensureSeedLogin(page, email = "admin@prompteer.dev") {
  await page.goto(routeUrl(`/dev/login-as/${encodeURIComponent(email)}`), {
    waitUntil: "domcontentloaded",
  });
  if (!page.url().endsWith("/en")) {
    throw new Error(
      `Seed login did not redirect to /en; current URL is ${page.url()}.`,
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
await mkdir(readmeOutDir, { recursive: true });
if (updateReadmeScreenshots) {
  await mkdir(promotedReadmeOutDir, { recursive: true });
}
await clearPngFiles(outDir);
await clearPngFiles(readmeOutDir);

const browser = await chromium.launch();
const failures = [];

for (const viewport of viewports) {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
  });
  const page = await context.newPage();
  let authenticatedEmail = null;
  let allowExpectedErrors = false;
  let activeRouteName = "startup";

  page.on("console", (message) => {
    if (message.type() === "error" && !allowExpectedErrors) {
      failures.push(
        `[${viewport.name}] ${activeRouteName} console error at ${page.url()}: ${message.text()}`,
      );
    }
  });
  page.on("pageerror", (error) => {
    if (!allowExpectedErrors) {
      failures.push(
        `[${viewport.name}] ${activeRouteName} page error at ${page.url()}: ${error.message}`,
      );
    }
  });

  for (const route of routes) {
    allowExpectedErrors = Boolean(route.allowExpectedErrors);
    activeRouteName = route.name;
    try {
      if (route.auth && authenticatedEmail === null) {
        const authEmail = route.authEmail ?? "admin@prompteer.dev";
        await ensureSeedLogin(page, authEmail);
        authenticatedEmail = authEmail;
      } else if (route.auth) {
        const authEmail = route.authEmail ?? "admin@prompteer.dev";
        if (authenticatedEmail !== authEmail) {
          await ensureSeedLogin(page, authEmail);
          authenticatedEmail = authEmail;
        }
      }

      await page.goto(routeUrl(route.path), { waitUntil: "domcontentloaded" });
      if (route.auth && page.url().includes("/login")) {
        failures.push(
          `[${viewport.name}] ${route.path} redirected to login after seed auth.`,
        );
      }
      await page.locator("body").waitFor({ state: "visible" });
      if (route.detailLinkName) {
        await page
          .getByRole("link", { name: route.detailLinkName })
          .first()
          .click();
        await page.waitForURL(route.expectedUrl);
        await page.locator("body").waitFor({ state: "visible" });
      }
      if (route.afterGoto) {
        await route.afterGoto(page);
        await page.locator("body").waitFor({ state: "visible" });
      }
      for (const expectedText of route.expectedText ?? []) {
        await page.getByText(expectedText).first().waitFor({
          state: "visible",
          timeout: 10_000,
        });
      }
      await page
        .waitForLoadState("networkidle", { timeout: 5_000 })
        .catch(() => {
          // Some server-rendered pages keep background fetches open; visible body is
          // the screenshot readiness gate, while network idle is only a stabilizer.
        });
      await settleForScreenshot(page);
      await page.screenshot({
        path: new URL(`${route.name}-${viewport.name}.png`, outDir).pathname,
        fullPage: true,
        style: hideNextDevToolsStyle,
      });
      if (route.readme && viewport.name === "desktop") {
        await page.screenshot({
          path: new URL(`${route.name}.png`, readmeOutDir).pathname,
          fullPage: true,
          style: hideNextDevToolsStyle,
        });
        if (updateReadmeScreenshots) {
          await page.screenshot({
            path: new URL(`${route.name}.png`, promotedReadmeOutDir).pathname,
            fullPage: true,
            style: hideNextDevToolsStyle,
          });
        }
      }
    } finally {
      activeRouteName = route.name;
      if (!route.allowExpectedErrors) {
        allowExpectedErrors = false;
      }
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
  `Saved ${routes.length * viewports.length} screenshots to ${outDir.pathname}`,
);
console.log(
  updateReadmeScreenshots
    ? `Updated primary README screenshots in ${promotedReadmeOutDir.pathname}`
    : `Saved README-name screenshots to ${readmeOutDir.pathname}`,
);

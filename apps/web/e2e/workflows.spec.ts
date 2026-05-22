// End-to-end checks for authenticated prompt, billing, board, and settings flows.
import { expect, test } from "@playwright/test";
import type { Locator, Page } from "@playwright/test";

import { loginAs } from "./helpers";

async function openLinkedRoute(
  page: Page,
  link: Locator,
  url: RegExp,
): Promise<void> {
  await expect(link).toBeVisible();
  const href = await link.getAttribute("href");

  if (href === null) {
    throw new Error("Expected navigational link to expose an href.");
  }
  expect(href).toEqual(expect.stringMatching(url));
  await page.goto(href);
  await expect(page).toHaveURL(url);
}

test("seeded user can run a coding prompt", async ({ page }) => {
  await loginAs(page);
  const prompt =
    "Explain FizzBuzz rules, then produce concise Python with clear edge cases.";

  await page.goto("/en/challenges/coding");
  await expect(
    page.getByRole("heading", { name: "Prompt repair workspace" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "FizzBuzz prompt repair" }),
  ).toBeVisible();

  await page.getByRole("textbox", { name: "Prompt" }).fill(prompt);
  await page.getByRole("button", { name: "Run prompt" }).click();

  await expect(page.getByText("Mock run result")).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByText(/Mock Prompteer response/)).toBeVisible();
  await expect(page.getByText(/tokens/)).toBeVisible();
  await expect(page.getByText("Published to board")).toBeVisible();

  await Promise.all([
    page.waitForURL(/\/en\/board$/),
    page.getByRole("link", { name: "View board" }).click(),
  ]);
  await expect(page.getByText(prompt)).toBeVisible();

  await Promise.all([
    page.waitForURL(/\/en\/board\/shares\//),
    page
      .getByRole("link", { name: /Read prompt share: FizzBuzz prompt repair/ })
      .first()
      .click(),
  ]);
  await expect(
    page.getByRole("heading", { name: "FizzBuzz prompt repair" }),
  ).toBeVisible();
  await expect(page.getByText(prompt)).toBeVisible();

  await Promise.all([
    page.waitForURL(/\/en\/board$/),
    page.getByRole("link", { name: "Back to board" }).click(),
  ]);
  await Promise.all([
    page.waitForURL(/\/en\/board\/posts\//),
    page
      .getByRole("link", { name: /Read question:/ })
      .first()
      .click(),
  ]);
  await expect(
    page.getByRole("heading", { name: /prompt|review|debug|image|video/i }),
  ).toBeVisible();
});

test("seeded user can browse media challenge lists and details", async ({
  page,
}) => {
  await loginAs(page);

  await page.goto("/en/challenges/coding");
  const challengeTypeNav = page.getByRole("navigation", {
    name: "Challenge types",
  });
  await openLinkedRoute(
    page,
    challengeTypeNav.getByRole("link", { exact: true, name: "Image" }),
    /\/en\/challenges\/image$/,
  );
  await expect(
    page.getByRole("link", { name: "Challenges" }),
  ).not.toHaveAttribute("aria-current", "page");
  await expect(
    challengeTypeNav.getByRole("link", { exact: true, name: "Image" }),
  ).toHaveAttribute("aria-current", "page");
  await expect(
    page.getByRole("heading", { name: "Image prompt challenges" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Product hero image prompt" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "product-hero.png" }),
  ).toBeVisible();
  await expect(page.getByText("image/png")).toBeVisible();
  await expect(
    page.getByText("Hero composition with product focus"),
  ).toBeVisible();
  await expect(page.getByText("Local preview", { exact: true })).toBeVisible();

  await openLinkedRoute(
    page,
    page.getByRole("link", { name: /View details: Product hero image prompt/ }),
    /\/en\/challenges\/image\/[^/]+$/,
  );
  await expect(
    page.getByRole("heading", { name: "Product hero image prompt" }),
  ).toBeVisible();
  await expect(page.getByText("Product hero").first()).toBeVisible();
  await page.locator("summary", { hasText: "Stored path" }).click();
  await expect(
    page.getByText("seed/references/product-hero.png"),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Prompt" })
    .fill(
      "Create a product hero prompt with lighting, composition, and accessibility-safe copy space.",
    );
  await page.getByRole("button", { name: "Run media prompt" }).click();
  await expect(page.getByText("Mock media run result")).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByText(/Mock Prompteer response/)).toBeVisible();
  await expect(page.getByText("Published to board")).toBeVisible();

  await openLinkedRoute(
    page,
    page.getByRole("link", { name: "Back to image challenges" }),
    /\/en\/challenges\/image$/,
  );

  await openLinkedRoute(
    page,
    challengeTypeNav.getByRole("link", { exact: true, name: "Video" }),
    /\/en\/challenges\/video$/,
  );
  await expect(
    page
      .getByRole("navigation", { name: "Challenge types" })
      .getByRole("link", { exact: true, name: "Video" }),
  ).toHaveAttribute("aria-current", "page");
  await expect(
    page.getByRole("heading", { name: "Video prompt challenges" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Launch teaser video prompt" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "launch-teaser.mp4" }),
  ).toBeVisible();
  await expect(page.getByText("video/mp4")).toBeVisible();
  await expect(page.getByText("16:9 launch teaser storyboard")).toBeVisible();

  await openLinkedRoute(
    page,
    page.getByRole("link", {
      name: /View details: Launch teaser video prompt/,
    }),
    /\/en\/challenges\/video\/[^/]+$/,
  );
  await expect(
    page.getByRole("heading", { name: "Launch teaser video prompt" }),
  ).toBeVisible();
  await expect(page.getByText("Launch teaser").first()).toBeVisible();
  await page.locator("summary", { hasText: "Stored path" }).click();
  await expect(
    page.getByText("seed/references/launch-teaser.mp4"),
  ).toBeVisible();
  await page
    .getByRole("textbox", { name: "Prompt" })
    .fill(
      "Create a launch teaser video prompt with scene beats, motion notes, and a clear call to action.",
    );
  await page.getByRole("button", { name: "Run media prompt" }).click();
  await expect(page.getByText("Mock media run result")).toBeVisible({
    timeout: 15_000,
  });
  await expect(page.getByText(/Mock Prompteer response/)).toBeVisible();
  await expect(page.getByText("Published to board")).toBeVisible();
});

test("paid demo user can complete mock checkout", async ({ page }) => {
  await loginAs(page, "paid@prompteer.dev");

  await page.goto("/en/billing");
  await expect(
    page.getByRole("heading", { name: "Subscription checkout" }),
  ).toBeVisible();

  await page.getByRole("button", { name: /Start (new )?checkout/ }).click();
  await expect(page.getByText(/cs_test_/)).toBeVisible();
  await expect(page.getByText("unpaid")).toBeVisible();

  await page.getByRole("button", { name: "Complete mock checkout" }).click();

  await expect(page.getByText("paid", { exact: true })).toBeVisible();
  await expect(
    page.getByText(/Subscription active for paid@prompteer.dev/),
  ).toBeVisible();
  await expect(page.getByText("checkout.session.completed")).toBeVisible();

  const sessionId = await page
    .getByText(/cs_test_/)
    .first()
    .textContent();
  expect(sessionId).toContain("cs_test_");
  await page.goto(`/en/billing/success?session_id=${sessionId}`);

  await expect(
    page.getByRole("heading", { name: "Checkout complete" }),
  ).toBeVisible();
  await expect(page.getByText(sessionId ?? "")).toBeVisible();
});

test("billing checkout uses the active session email", async ({ page }) => {
  await loginAs(page, "admin@prompteer.dev");

  await page.goto("/en/billing");
  await expect(
    page.getByText("admin@prompteer.dev", { exact: true }),
  ).toBeVisible();

  await page.getByRole("button", { name: /Start (new )?checkout/ }).click();
  await expect(page.getByText(/cs_test_/)).toBeVisible();
  await expect(
    page.getByText("admin@prompteer.dev", { exact: true }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Complete mock checkout" }).click();
  await expect(
    page.getByText(/Subscription active for admin@prompteer.dev/),
  ).toBeVisible();
});

test("real checkout sessions expose hosted Stripe URL", async ({ page }) => {
  await loginAs(page, "paid@prompteer.dev");

  await page.goto("/en/billing");
  await page.route("**/api/backend/api/v1/billing/checkout", async (route) => {
    await route.fulfill({
      json: {
        id: "cs_test_hosted",
        mode: "subscription",
        status: "open",
        payment_status: "unpaid",
        amount_total: 1200,
        currency: "usd",
        url: "https://checkout.stripe.com/c/pay/cs_test_hosted",
        customer_email: "paid@prompteer.dev",
        provider: "stripe",
      },
    });
  });

  await page.getByRole("button", { name: /Start (new )?checkout/ }).click();

  await expect(page.getByText("Hosted URL")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open Stripe Checkout" }),
  ).toHaveAttribute("href", "https://checkout.stripe.com/c/pay/cs_test_hosted");
  await expect(
    page.getByRole("button", { name: "Complete mock checkout" }),
  ).toHaveCount(0);
});

test("seeded user can view profile settings", async ({ page }) => {
  await loginAs(page);

  await Promise.all([
    page.waitForURL(/\/en\/profile$/),
    page.getByRole("link", { name: "Profile settings" }).click(),
  ]);
  await expect(
    page.getByRole("heading", { name: "Profile settings" }),
  ).toBeVisible();
  await expect(page.getByText("Prompteer Admin")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Feature availability" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Integration mode" }),
  ).toBeVisible();
  await expect(page.locator("dd", { hasText: "MOCK" })).toHaveCount(4);
});

test("seeded user can log out", async ({ page }) => {
  await loginAs(page);

  await expect(page.getByText("Prompteer Admin")).toBeVisible();
  await page.getByRole("button", { name: "Log out" }).click();

  await page.waitForURL("/en/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

// End-to-end checks for authenticated prompt, billing, board, and settings flows.
import { randomUUID } from "node:crypto";

import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

test("seeded user can run a coding prompt", async ({ page }) => {
  await loginAs(page);
  const prompt = `Explain FizzBuzz rules, then produce concise Python with E2E-created board proof. Run ${randomUUID()}.`;

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

  await page.getByRole("link", { name: "View board" }).click();
  await expect(page).toHaveURL(/\/en\/board$/);
  await expect(page.getByText(prompt)).toBeVisible();
});

test("paid demo user can complete mock checkout", async ({ page }) => {
  await loginAs(page, "paid@prompteer.dev");

  await page.goto("/en/billing");
  await expect(
    page.getByRole("heading", { name: "Subscription checkout" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Start checkout" }).click();
  await expect(page.getByText(/cs_test_/)).toBeVisible();
  await expect(page.getByText("unpaid")).toBeVisible();

  await page.getByRole("button", { name: "Complete mock checkout" }).click();

  await expect(page.getByText("paid", { exact: true })).toBeVisible();
  await expect(
    page.getByText(/Subscription active for paid@prompteer.dev/),
  ).toBeVisible();
  await expect(page.getByText("checkout.session.completed")).toBeVisible();
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

  await page.getByRole("button", { name: "Start checkout" }).click();

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

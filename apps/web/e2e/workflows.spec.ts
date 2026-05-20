import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

test("seeded user can run a coding prompt", async ({ page }) => {
  await loginAs(page);

  await page.goto("/en/challenges/coding");
  await expect(
    page.getByRole("heading", { name: "Prompt repair workspace" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "FizzBuzz prompt repair" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Run prompt" }).click();

  await expect(page.getByText("Mock run result")).toBeVisible();
  await expect(page.getByText(/Mock Prompteer response/)).toBeVisible();
  await expect(page.getByText(/tokens/)).toBeVisible();
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

test("seeded user can view profile settings", async ({ page }) => {
  await loginAs(page);

  await page.getByRole("link", { name: "Profile settings" }).click();
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

import { expect, test } from "@playwright/test";

test("mock Google OAuth login completes through Auth.js", async ({ page }) => {
  await page.goto("/en/login");
  await page.getByRole("button", { name: "Admin demo" }).click();
  await page.waitForURL("/en");
  await expect(
    page.getByRole("heading", { name: "Prompt challenge workspace" }),
  ).toBeVisible();
});

test("seed login route issues an Auth.js session", async ({ page }) => {
  await page.goto("/dev/login-as/admin%40prompteer.dev");
  await page.waitForURL("/en");
  await expect(
    page.getByRole("heading", { name: "Prompt challenge workspace" }),
  ).toBeVisible();
});

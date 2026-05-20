import { expect, test } from "@playwright/test";

test("mock Google OAuth login completes through Auth.js", async ({ page }) => {
  await page.goto("/en/login");
  await page.getByRole("button", { name: "Admin demo" }).click();
  await page.waitForURL("/en");
  await expect(
    page.getByRole("heading", { name: "Prompt challenge workspace" }),
  ).toBeVisible();
});

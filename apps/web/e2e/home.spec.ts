// End-to-end checks for the public landing page and unauthenticated flows.
import { expect, test } from "@playwright/test";

test("home page renders the challenge workspace", async ({ page }) => {
  await page.goto("/en");
  await expect(
    page.getByRole("heading", { name: "Prompt challenge workspace" }),
  ).toBeVisible();
});

test("app routes redirect signed-out users to login", async ({ page }) => {
  await page.goto("/en/board");

  await page.waitForURL("/en/login");
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

import type { Page } from "@playwright/test";

export async function loginAs(
  page: Page,
  email = "admin@prompteer.dev",
): Promise<void> {
  await page.goto(`/dev/login-as/${encodeURIComponent(email)}`);
  await page.waitForURL("/en");
}

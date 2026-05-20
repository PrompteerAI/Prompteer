// End-to-end checks for the development mock mailbox screens.
import { expect, test } from "@playwright/test";

test("dev mailbox shows seeded captured emails", async ({ page }) => {
  await page.goto("/dev/mailbox");

  await expect(
    page.getByRole("heading", { name: "Mock mailbox" }),
  ).toBeVisible();
  await expect(
    page.getByText("Prompteer admin workspace is ready"),
  ).toBeVisible();
  await expect(page.getByText("Mock subscription receipt")).toBeVisible();

  await page.getByRole("link", { name: "Mock subscription receipt" }).click();
  await expect(
    page.getByRole("heading", { name: "Mock subscription receipt" }),
  ).toBeVisible();
  await expect(page.getByText("checkout has completed")).toBeVisible();
});

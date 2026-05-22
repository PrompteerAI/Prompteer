// End-to-end checks for mock Google OAuth and seeded development login.
import { expect, test, type Page } from "@playwright/test";

test("mock Google OAuth login completes through the local OIDC server", async ({
  page,
}) => {
  await page.goto("/en/login");
  await page.getByRole("button", { name: "Admin demo" }).click();
  await page.waitForURL("/en");

  const user = await sessionUser(page);
  expect(user.id).toBe("mock-google-oauth2|admin");
  expect(user.email).toBe("admin@prompteer.dev");
  await expectSessionCookieIsEncrypted(page);
  await expect(
    page.getByRole("heading", { name: "Prompt challenge workspace" }),
  ).toBeVisible();
  await expect(page.getByText("Prompteer Admin")).toBeVisible();
});

test("signed-out protected routes return to the original path after login", async ({
  page,
}) => {
  await page.goto("/en/board");
  await expect(page).toHaveURL(/\/en\/login\?callbackUrl=%2Fen%2Fboard$/);

  await page.getByRole("button", { name: "Admin demo" }).click();

  await page.waitForURL("/en/board");
  await expect(
    page.getByRole("heading", { name: "Shared prompt reviews" }),
  ).toBeVisible();
});

test("seed login route issues an Auth.js session", async ({ page }) => {
  await page.goto("/dev/login-as/admin%40prompteer.dev");
  await page.waitForURL("/en");
  const user = await sessionUser(page);
  expect(user.id).toBe("00000000-0000-4000-8000-000000000001");
  expect(user.email).toBe("admin@prompteer.dev");
  await expectSessionCookieIsEncrypted(page);
  await expect(
    page.getByRole("heading", { name: "Prompt challenge workspace" }),
  ).toBeVisible();
});

async function sessionUser(page: Page): Promise<Record<string, unknown>> {
  const sessionResponse = await page.request.get("/api/auth/session");
  if (!sessionResponse.ok()) {
    throw new Error(
      `Auth.js session endpoint returned HTTP ${sessionResponse.status()}.`,
    );
  }
  const session = (await sessionResponse.json()) as {
    user?: Record<string, unknown>;
  };
  if (!session.user) {
    throw new Error("Auth.js session endpoint did not return a user.");
  }
  return session.user;
}

async function expectSessionCookieIsEncrypted(page: Page): Promise<void> {
  const cookies = await page.context().cookies();
  const sessionCookie = cookies.find((cookie) =>
    ["authjs.session-token", "__Secure-authjs.session-token"].includes(
      cookie.name,
    ),
  );
  if (!sessionCookie) {
    throw new Error("Auth.js session cookie was not issued.");
  }
  expect(sessionCookie.value.split(".")).toHaveLength(5);
}

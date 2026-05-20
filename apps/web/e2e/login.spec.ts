// End-to-end checks for mock Google OAuth and seeded development login.
import { expect, test, type Page } from "@playwright/test";

test("mock Google OAuth login completes through the local OIDC server", async ({
  page,
}) => {
  await page.goto("/en/login");
  await page.getByRole("button", { name: "Admin demo" }).click();
  await page.waitForURL("/en");

  const claims = await sessionClaims(page);
  expect(claims.sub).toBe("mock-google-oauth2|admin");
  expect(claims.email).toBe("admin@prompteer.dev");
  await expect(
    page.getByRole("heading", { name: "Prompt challenge workspace" }),
  ).toBeVisible();
  await expect(page.getByText("Prompteer Admin")).toBeVisible();
});

test("seed login route issues an Auth.js session", async ({ page }) => {
  await page.goto("/dev/login-as/admin%40prompteer.dev");
  await page.waitForURL("/en");
  const claims = await sessionClaims(page);
  expect(claims.sub).toBe("00000000-0000-4000-8000-000000000001");
  expect(claims.email).toBe("admin@prompteer.dev");
  await expect(
    page.getByRole("heading", { name: "Prompt challenge workspace" }),
  ).toBeVisible();
});

async function sessionClaims(page: Page): Promise<Record<string, unknown>> {
  const cookies = await page.context().cookies();
  const sessionCookie = cookies.find((cookie) =>
    ["authjs.session-token", "__Secure-authjs.session-token"].includes(
      cookie.name,
    ),
  );
  if (!sessionCookie) {
    throw new Error("Auth.js session cookie was not issued.");
  }
  const [, encodedPayload] = sessionCookie.value.split(".");
  if (!encodedPayload) {
    throw new Error("Auth.js session cookie is not a JWT.");
  }
  return JSON.parse(
    Buffer.from(encodedPayload, "base64url").toString("utf8"),
  ) as Record<string, unknown>;
}

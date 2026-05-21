// Unit tests for API proxy bearer token claims. FastAPI depends on this subject
// matching the Auth.js/provider subject for per-user quotas and authz.
import type { Session } from "next-auth";
import { describe, expect, it } from "vitest";

import { apiTokenForSession } from "./api-token";

describe("apiTokenForSession", () => {
  it("uses the Auth.js session user id as the bearer subject", () => {
    const token = apiTokenForSession({
      expires: new Date(Date.now() + 60_000).toISOString(),
      user: {
        id: "mock-google-oauth2|admin",
        email: "admin@prompteer.dev",
        name: "Prompteer Admin",
      },
    } satisfies Session);

    expect(jwtPayload(token)).toMatchObject({
      sub: "mock-google-oauth2|admin",
      email: "admin@prompteer.dev",
      name: "Prompteer Admin",
      aud: "prompteer-api",
    });
  });

  it("falls back to email when a legacy session has no user id", () => {
    const token = apiTokenForSession({
      expires: new Date(Date.now() + 60_000).toISOString(),
      user: {
        email: "free@prompteer.dev",
        name: "Free Prompt Builder",
      },
    } satisfies Session);

    expect(jwtPayload(token).sub).toBe("free@prompteer.dev");
  });
});

function jwtPayload(token: string): Record<string, unknown> {
  const [, encodedPayload] = token.split(".");
  if (!encodedPayload) {
    throw new Error("API bearer token is not a JWT.");
  }
  return JSON.parse(
    Buffer.from(encodedPayload, "base64url").toString("utf8"),
  ) as Record<string, unknown>;
}

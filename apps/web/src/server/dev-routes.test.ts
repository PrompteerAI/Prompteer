// Unit tests for server-only development route gating.
import { describe, expect, it } from "vitest";

import { devRoutesEnabled } from "./dev-routes";

describe("devRoutesEnabled", () => {
  it("allows dev routes outside production when the flag is enabled", () => {
    expect(
      devRoutesEnabled({ ENV: "development", ENABLE_DEV_ROUTES: true }),
    ).toBe(true);
  });

  it("blocks dev routes when the flag is disabled", () => {
    expect(
      devRoutesEnabled({ ENV: "development", ENABLE_DEV_ROUTES: false }),
    ).toBe(false);
  });

  it("blocks dev routes in production even when the flag is set", () => {
    expect(
      devRoutesEnabled({ ENV: "production", ENABLE_DEV_ROUTES: true }),
    ).toBe(false);
  });
});

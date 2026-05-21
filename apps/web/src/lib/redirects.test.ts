// Unit tests for auth callback URL handling. These guard against open redirects
// while preserving same-locale return paths.
import { describe, expect, it } from "vitest";

import { safeLocalizedCallbackUrl } from "./redirects";

describe("safeLocalizedCallbackUrl", () => {
  it("preserves same-locale callback paths with query strings and hashes", () => {
    expect(safeLocalizedCallbackUrl("/en/board?tab=public#share", "en")).toBe(
      "/en/board?tab=public#share",
    );
  });

  it("uses the first callback value when a query param is repeated", () => {
    expect(safeLocalizedCallbackUrl(["/en/profile", "/en/billing"], "en")).toBe(
      "/en/profile",
    );
  });

  it("rejects external, scheme-relative, and malformed callback targets", () => {
    expect(safeLocalizedCallbackUrl("https://example.com/en", "en")).toBe(
      "/en",
    );
    expect(safeLocalizedCallbackUrl("//example.com/en", "en")).toBe("/en");
    expect(safeLocalizedCallbackUrl("/en\\evil", "en")).toBe("/en");
    expect(safeLocalizedCallbackUrl("/en\nboard", "en")).toBe("/en");
  });

  it("rejects callback paths for a different locale", () => {
    expect(safeLocalizedCallbackUrl("/fr/board", "en")).toBe("/en");
  });

  it("falls back to the default locale when the active locale is unknown", () => {
    expect(
      safeLocalizedCallbackUrl("/not-a-locale/board", "not-a-locale"),
    ).toBe("/en");
  });
});

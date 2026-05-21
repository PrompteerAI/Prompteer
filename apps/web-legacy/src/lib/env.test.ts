// Unit tests for legacy-preview environment validation.
import { describe, expect, it } from "vitest";

import { parseServerEnv } from "./env";

describe("parseServerEnv", () => {
  it("uses local defaults when values are absent", () => {
    const parsed = parseServerEnv({});

    expect(parsed.APP_URL).toBe("http://localhost:3000");
    expect(parsed.API_INTERNAL_URL).toBe("http://localhost:8000/api/v1");
    expect(parsed.NEXT_PUBLIC_API_URL).toBe("http://localhost:8000/api/v1");
    expect(parsed.NEXT_PUBLIC_APP_VERSION).toBe("0.1.0");
  });

  it("treats blank .env values as absent", () => {
    const parsed = parseServerEnv({
      APP_URL: " ",
      API_INTERNAL_URL: "",
      NEXT_PUBLIC_API_URL: "\t",
      NEXT_PUBLIC_APP_VERSION: "",
    });

    expect(parsed.APP_URL).toBe("http://localhost:3000");
    expect(parsed.API_INTERNAL_URL).toBe("http://localhost:8000/api/v1");
    expect(parsed.NEXT_PUBLIC_API_URL).toBe("http://localhost:8000/api/v1");
    expect(parsed.NEXT_PUBLIC_APP_VERSION).toBe("0.1.0");
  });

  it("preserves explicit HTTP URLs and app version", () => {
    const parsed = parseServerEnv({
      APP_URL: "https://auth.example.test",
      API_INTERNAL_URL: "http://api.internal.test/api/v1",
      NEXT_PUBLIC_API_URL: "https://app.example.test/api/v1",
      NEXT_PUBLIC_APP_VERSION: "2026.5.22",
    });

    expect(parsed.APP_URL).toBe("https://auth.example.test");
    expect(parsed.API_INTERNAL_URL).toBe("http://api.internal.test/api/v1");
    expect(parsed.NEXT_PUBLIC_API_URL).toBe("https://app.example.test/api/v1");
    expect(parsed.NEXT_PUBLIC_APP_VERSION).toBe("2026.5.22");
  });

  it("rejects malformed or non-HTTP URLs", () => {
    expect(() => parseServerEnv({ APP_URL: "localhost:3000" })).toThrow();
    expect(() =>
      parseServerEnv({ API_INTERNAL_URL: "file:///tmp/prompteer" }),
    ).toThrow(/HTTP/);
  });
});

// Unit tests for API client URL normalization. These guard the Compose
// server-side path handling where OpenAPI paths already include /api/v1.
import { describe, expect, it } from "vitest";

import { stripApiV1Prefix } from "./api-client";

describe("stripApiV1Prefix", () => {
  it("removes the version prefix from configured API base URLs", () => {
    expect(stripApiV1Prefix("http://api:8000/api/v1")).toBe("http://api:8000");
  });

  it("preserves non-API proxy base URLs", () => {
    expect(stripApiV1Prefix("/api/backend")).toBe("/api/backend");
  });

  it("normalizes trailing slashes before removing the prefix", () => {
    expect(stripApiV1Prefix("http://localhost:8000/api/v1/")).toBe(
      "http://localhost:8000",
    );
  });
});

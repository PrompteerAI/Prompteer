// Unit tests for Auth.js seed-login wiring without invoking real providers.
import { afterEach, describe, expect, it, vi } from "vitest";

const nextAuthMock = vi.hoisted(() =>
  vi.fn((config: unknown) => ({
    auth: vi.fn(),
    handlers: { GET: vi.fn(), POST: vi.fn() },
    signIn: vi.fn(),
    signOut: vi.fn(),
    __config: config,
  })),
);

vi.mock("next-auth", () => ({
  default: nextAuthMock,
}));

interface MockCredentialsProviderConfig {
  name?: string;
  credentials?: Record<string, unknown>;
  authorize?: (credentials: { email?: string }) => unknown;
}

vi.mock("next-auth/providers/credentials", () => ({
  default: (config: MockCredentialsProviderConfig) => ({
    id: "seed",
    type: "credentials",
    name: config.name,
    credentials: config.credentials,
    authorize: config.authorize,
  }),
}));

vi.mock("@/lib/auth-providers", () => ({
  googleProvider: () => ({ id: "google", type: "oauth" }),
}));

vi.mock("@/server/auth-jwt", () => ({
  decodeAuthJwt: vi.fn(),
  encodeAuthJwt: vi.fn(),
}));

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("seed-login auth helpers", () => {
  it("looks up seed users case-insensitively", async () => {
    vi.resetModules();
    vi.stubEnv("ENV", "test");

    const { getSeedUser } = await import("./auth");

    expect(getSeedUser("ADMIN@PROMPTEER.DEV")).toMatchObject({
      id: "00000000-0000-4000-8000-000000000001",
      email: "admin@prompteer.dev",
      name: "Prompteer Admin",
      role: "admin",
    });
    expect(getSeedUser("unknown@prompteer.dev")).toBeUndefined();
  });

  it("enables seed login only outside production when configured", async () => {
    vi.resetModules();
    vi.stubEnv("ENV", "development");
    vi.stubEnv("AUTH_ALLOW_SEED_LOGIN", "true");

    const enabledModule = await import("./auth");
    expect(enabledModule.seedLoginEnabled()).toBe(true);

    vi.resetModules();
    vi.stubEnv("ENV", "development");
    vi.stubEnv("AUTH_ALLOW_SEED_LOGIN", "false");

    const disabledModule = await import("./auth");
    expect(disabledModule.seedLoginEnabled()).toBe(false);

    vi.resetModules();
    vi.stubEnv("ENV", "production");
    vi.stubEnv("AUTH_SECRET", "replace-with-a-real-32-byte-random-secret");
    vi.stubEnv(
      "AUTH_JWT_PRIVATE_KEY",
      "-----BEGIN PRIVATE KEY-----\\nfake\\n-----END PRIVATE KEY-----",
    );
    vi.stubEnv("GOOGLE_CLIENT_ID", "google-client");
    vi.stubEnv("GOOGLE_CLIENT_SECRET", "google-secret");
    vi.stubEnv("AUTH_ALLOW_SEED_LOGIN", "true");

    const productionModule = await import("./auth");
    expect(productionModule.seedLoginEnabled()).toBe(false);
  });

  it("adds the seed credentials provider in development and authorizes known users", async () => {
    vi.resetModules();
    nextAuthMock.mockClear();
    vi.stubEnv("ENV", "development");
    vi.stubEnv("AUTH_ALLOW_SEED_LOGIN", "true");

    await import("./auth");

    const config = nextAuthMock.mock.calls.at(-1)?.[0] as {
      providers: Array<{
        id: string;
        authorize?: (credentials: { email?: string }) => unknown;
      }>;
    };
    expect(config.providers.map((provider) => provider.id)).toEqual([
      "google",
      "seed",
    ]);

    const seedProvider = config.providers.find(
      (provider) => provider.id === "seed",
    );
    expect(
      seedProvider?.authorize?.({ email: "PAID@PROMPTEER.DEV" }),
    ).toMatchObject({
      email: "paid@prompteer.dev",
      role: "user",
    });
    expect(
      seedProvider?.authorize?.({ email: "missing@prompteer.dev" }),
    ).toBeNull();
  });

  it("keeps only Google configured when seed login is disabled", async () => {
    vi.resetModules();
    nextAuthMock.mockClear();
    vi.stubEnv("ENV", "development");
    vi.stubEnv("AUTH_ALLOW_SEED_LOGIN", "false");

    await import("./auth");

    const config = nextAuthMock.mock.calls.at(-1)?.[0] as {
      providers: Array<{ id: string }>;
    };
    expect(config.providers.map((provider) => provider.id)).toEqual(["google"]);
  });
});

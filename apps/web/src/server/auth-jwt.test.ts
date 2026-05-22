// Unit tests for the RS256 API bearer tokens consumed by the FastAPI API.
import { describe, expect, it, vi } from "vitest";

describe("auth-jwt", () => {
  it("round-trips signed JWT claims and publishes a matching public JWK", async () => {
    vi.resetModules();
    vi.stubEnv("ENV", "test");
    vi.stubEnv("AUTH_JWT_AUDIENCE", "prompteer-api");
    vi.stubEnv("AUTH_JWT_ISSUER", "http://localhost:3000/");
    vi.stubEnv("AUTH_JWT_KEY_ID", "test-key");

    const { decodeAuthJwt, encodeAuthJwt, getAuthJwtPublicJwk } =
      await import("./auth-jwt");

    const token = encodeAuthJwt({
      token: {
        sub: "mock-google-oauth2|admin",
        email: "admin@prompteer.dev",
        name: "Prompteer Admin",
      },
      maxAge: 60,
      salt: "authjs.session-token",
      secret: "unused-by-rs256",
    });

    expect(token.split(".")).toHaveLength(3);
    expect(decodeAuthJwt({ token, salt: "", secret: "" })).toMatchObject({
      sub: "mock-google-oauth2|admin",
      email: "admin@prompteer.dev",
      iss: "http://localhost:3000",
      aud: "prompteer-api",
    });
    expect(getAuthJwtPublicJwk()).toMatchObject({
      alg: "RS256",
      kid: "test-key",
      kty: "RSA",
      use: "sig",
    });

    vi.unstubAllEnvs();
  });

  it("rejects missing, malformed, tampered, and expired JWTs", async () => {
    vi.resetModules();
    vi.stubEnv("ENV", "test");

    const { decodeAuthJwt, encodeAuthJwt } = await import("./auth-jwt");
    const validToken = encodeAuthJwt({
      token: { sub: "free@prompteer.dev" },
      maxAge: 60,
      salt: "",
      secret: "",
    });
    const [header, payload] = validToken.split(".");
    const tamperedPayload = Buffer.from(
      JSON.stringify({ sub: "admin@prompteer.dev", exp: 4_102_444_800 }),
    ).toString("base64url");
    const expiredToken = encodeAuthJwt({
      token: { sub: "free@prompteer.dev" },
      maxAge: -1,
      salt: "",
      secret: "",
    });

    expect(
      decodeAuthJwt({ token: undefined, salt: "", secret: "" }),
    ).toBeNull();
    expect(
      decodeAuthJwt({ token: "not-a-jwt", salt: "", secret: "" }),
    ).toBeNull();
    expect(
      decodeAuthJwt({
        token: `${header}.${tamperedPayload}.${payload}`,
        salt: "",
        secret: "",
      }),
    ).toBeNull();
    expect(
      decodeAuthJwt({ token: expiredToken, salt: "", secret: "" }),
    ).toBeNull();

    vi.unstubAllEnvs();
  });

  it("rejects tokens when issuer or audience no longer match configuration", async () => {
    vi.resetModules();
    vi.stubEnv("ENV", "test");
    vi.stubEnv("AUTH_JWT_ISSUER", "http://issuer-one.test");
    vi.stubEnv("AUTH_JWT_AUDIENCE", "prompteer-api");

    const firstModule = await import("./auth-jwt");
    const token = firstModule.encodeAuthJwt({
      token: { sub: "paid@prompteer.dev" },
      maxAge: 60,
      salt: "",
      secret: "",
    });

    vi.resetModules();
    vi.stubEnv("ENV", "test");
    vi.stubEnv("AUTH_JWT_ISSUER", "http://issuer-two.test");
    vi.stubEnv("AUTH_JWT_AUDIENCE", "prompteer-api");

    const secondModule = await import("./auth-jwt");
    expect(
      secondModule.decodeAuthJwt({ token, salt: "", secret: "" }),
    ).toBeNull();

    vi.unstubAllEnvs();
  });

  it("requires an explicit private key in production", async () => {
    vi.resetModules();
    vi.stubEnv("ENV", "production");
    vi.stubEnv("AUTH_SECRET", "replace-with-a-real-32-byte-random-secret");
    vi.stubEnv("GOOGLE_CLIENT_ID", "google-client");
    vi.stubEnv("GOOGLE_CLIENT_SECRET", "google-secret");

    await expect(import("./auth-jwt")).resolves.toBeDefined();
    const { encodeAuthJwt } = await import("./auth-jwt");
    expect(() =>
      encodeAuthJwt({
        token: { sub: "admin@prompteer.dev" },
        salt: "",
        secret: "",
      }),
    ).toThrow(/AUTH_JWT_PRIVATE_KEY/);

    vi.unstubAllEnvs();
  });
});

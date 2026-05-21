// Validates browser-visible and server-only environment variables at module load
// boundaries so runtime configuration fails loudly before requests are handled.
import { z } from "zod";

type RawEnv = Record<string, string | undefined>;

const TRUE_VALUES = new Set(["1", "true", "yes", "on"]);
const FALSE_VALUES = new Set(["0", "false", "no", "off"]);

const emptyStringToUndefined = (value: unknown): unknown => {
  if (typeof value === "string" && value.trim() === "") {
    return undefined;
  }
  return value;
};

const httpUrl = z
  .string()
  .url()
  .refine(
    (value) => {
      const protocol = new URL(value).protocol;
      return protocol === "http:" || protocol === "https:";
    },
    { message: "Expected an HTTP(S) URL" },
  );

const envUrl = (defaultValue: string) =>
  z
    .preprocess(emptyStringToUndefined, httpUrl.optional())
    .transform((value) => value ?? defaultValue);

const optionalEnvUrl = z.preprocess(emptyStringToUndefined, httpUrl.optional());

const envString = (defaultValue: string) =>
  z
    .preprocess(emptyStringToUndefined, z.string().optional())
    .transform((value) => value ?? defaultValue);

const optionalEnvString = z.preprocess(
  emptyStringToUndefined,
  z.string().optional(),
);

const envBoolean = (defaultValue: boolean) =>
  z.preprocess((value) => {
    if (value === undefined || value === null) {
      return defaultValue;
    }
    if (typeof value === "boolean") {
      return value;
    }
    if (typeof value === "string") {
      const normalized = value.trim().toLowerCase();
      if (normalized.length === 0) {
        return defaultValue;
      }
      if (TRUE_VALUES.has(normalized)) {
        return true;
      }
      if (FALSE_VALUES.has(normalized)) {
        return false;
      }
    }
    return value;
  }, z.boolean());

const pemEnvString = optionalEnvString.transform((value) =>
  value?.replaceAll("\\n", "\n").trim(),
);

export const publicEnvSchema = z.object({
  NEXT_PUBLIC_API_URL: envUrl("http://localhost:8000/api/v1"),
  NEXT_PUBLIC_APP_VERSION: envString("0.1.0"),
  NEXT_PUBLIC_USE_MOCK_GOOGLE: envBoolean(true),
  NEXT_PUBLIC_SENTRY_DSN: envString(""),
});

export const serverEnvSchema = publicEnvSchema.extend({
  ENV: z.enum(["development", "test", "production"]).default("development"),
  APP_VERSION: envString("0.1.0"),
  APP_URL: envUrl("http://localhost:3000"),
  API_INTERNAL_URL: envUrl("http://localhost:8000/api/v1"),
  AUTH_SECRET: envString("dev-auth-secret-change-in-production"),
  AUTH_URL: envUrl("http://localhost:3000"),
  AUTH_MOCK_GOOGLE_ISSUER: envUrl("http://localhost:8000"),
  AUTH_MOCK_GOOGLE_DISCOVERY_URL: optionalEnvUrl,
  AUTH_MOCK_GOOGLE_SERVER_BASE_URL: optionalEnvUrl,
  AUTH_JWT_ISSUER: optionalEnvUrl,
  AUTH_JWT_AUDIENCE: envString("prompteer-api"),
  AUTH_JWT_PRIVATE_KEY: pemEnvString,
  AUTH_JWT_KEY_ID: envString("prompteer-dev-auth"),
  GOOGLE_CLIENT_ID: optionalEnvString,
  GOOGLE_CLIENT_SECRET: optionalEnvString,
  AUTH_ALLOW_SEED_LOGIN: envBoolean(true),
  ENABLE_DEV_ROUTES: envBoolean(true),
});

export type PublicEnv = z.infer<typeof publicEnvSchema>;
export type ServerEnv = z.infer<typeof serverEnvSchema>;

let cachedServerEnv: ServerEnv | undefined;

export function parsePublicEnv(rawEnv: RawEnv): PublicEnv {
  return publicEnvSchema.parse({
    NEXT_PUBLIC_API_URL: rawEnv.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_VERSION: rawEnv.NEXT_PUBLIC_APP_VERSION,
    NEXT_PUBLIC_USE_MOCK_GOOGLE: rawEnv.NEXT_PUBLIC_USE_MOCK_GOOGLE,
    NEXT_PUBLIC_SENTRY_DSN: rawEnv.NEXT_PUBLIC_SENTRY_DSN,
  });
}

export function parseServerEnv(rawEnv: RawEnv): ServerEnv {
  return serverEnvSchema.parse({
    ENV: rawEnv.ENV,
    APP_VERSION: rawEnv.APP_VERSION,
    APP_URL: rawEnv.APP_URL,
    NEXT_PUBLIC_API_URL: rawEnv.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_VERSION: rawEnv.NEXT_PUBLIC_APP_VERSION,
    NEXT_PUBLIC_USE_MOCK_GOOGLE: rawEnv.NEXT_PUBLIC_USE_MOCK_GOOGLE,
    NEXT_PUBLIC_SENTRY_DSN: rawEnv.NEXT_PUBLIC_SENTRY_DSN,
    API_INTERNAL_URL: rawEnv.API_INTERNAL_URL,
    AUTH_SECRET: rawEnv.AUTH_SECRET,
    AUTH_URL: rawEnv.AUTH_URL,
    AUTH_MOCK_GOOGLE_ISSUER: rawEnv.AUTH_MOCK_GOOGLE_ISSUER,
    AUTH_MOCK_GOOGLE_DISCOVERY_URL: rawEnv.AUTH_MOCK_GOOGLE_DISCOVERY_URL,
    AUTH_MOCK_GOOGLE_SERVER_BASE_URL: rawEnv.AUTH_MOCK_GOOGLE_SERVER_BASE_URL,
    AUTH_JWT_ISSUER: rawEnv.AUTH_JWT_ISSUER,
    AUTH_JWT_AUDIENCE: rawEnv.AUTH_JWT_AUDIENCE,
    AUTH_JWT_PRIVATE_KEY: rawEnv.AUTH_JWT_PRIVATE_KEY,
    AUTH_JWT_KEY_ID: rawEnv.AUTH_JWT_KEY_ID,
    GOOGLE_CLIENT_ID: rawEnv.GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET: rawEnv.GOOGLE_CLIENT_SECRET,
    AUTH_ALLOW_SEED_LOGIN: rawEnv.AUTH_ALLOW_SEED_LOGIN,
    ENABLE_DEV_ROUTES: rawEnv.ENABLE_DEV_ROUTES,
  });
}

export function getServerEnv(): ServerEnv {
  cachedServerEnv ??= parseServerEnv(process.env);
  return cachedServerEnv;
}

export const publicEnv = parsePublicEnv({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION,
  NEXT_PUBLIC_USE_MOCK_GOOGLE: process.env.NEXT_PUBLIC_USE_MOCK_GOOGLE,
  NEXT_PUBLIC_SENTRY_DSN: process.env.NEXT_PUBLIC_SENTRY_DSN,
});

// Compatibility alias for older imports. New code should prefer publicEnv.
export const env = publicEnv;

// Minimal runtime environment validation for the legacy-preview frontend.
import { z } from "zod";

type RawEnv = Record<string, string | undefined>;

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

const envString = (defaultValue: string) =>
  z
    .preprocess(emptyStringToUndefined, z.string().optional())
    .transform((value) => value ?? defaultValue);

const serverEnvSchema = z.object({
  APP_URL: envUrl("http://localhost:3000"),
  API_INTERNAL_URL: envUrl("http://localhost:8000/api/v1"),
  NEXT_PUBLIC_API_URL: envUrl("http://localhost:8000/api/v1"),
  NEXT_PUBLIC_APP_VERSION: envString("0.1.0"),
});

export type ServerEnv = z.infer<typeof serverEnvSchema>;

let cachedServerEnv: ServerEnv | undefined;

export function parseServerEnv(rawEnv: RawEnv): ServerEnv {
  return serverEnvSchema.parse({
    APP_URL: rawEnv.APP_URL,
    API_INTERNAL_URL: rawEnv.API_INTERNAL_URL,
    NEXT_PUBLIC_API_URL: rawEnv.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_VERSION: rawEnv.NEXT_PUBLIC_APP_VERSION,
  });
}

export function getServerEnv(): ServerEnv {
  cachedServerEnv ??= parseServerEnv(process.env);
  return cachedServerEnv;
}

export function authGatewayOrigin(): string {
  return getServerEnv().APP_URL.replace(/\/+$/, "");
}

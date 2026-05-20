import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().url().default("http://localhost:8000/api/v1"),
  NEXT_PUBLIC_USE_MOCK_GOOGLE: z.coerce.boolean().default(true),
  NEXT_PUBLIC_SENTRY_DSN: z.string().optional().default(""),
});

export const env = envSchema.parse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  NEXT_PUBLIC_USE_MOCK_GOOGLE: process.env.NEXT_PUBLIC_USE_MOCK_GOOGLE,
  NEXT_PUBLIC_SENTRY_DSN: process.env.NEXT_PUBLIC_SENTRY_DSN,
});

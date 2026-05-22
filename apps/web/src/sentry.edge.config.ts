// Edge runtime Sentry configuration for Next.js proxy and edge handlers.
// Empty NEXT_PUBLIC_SENTRY_DSN keeps local development silent.

import * as Sentry from "@sentry/nextjs";

import { getServerEnv } from "@/lib/env";

const env = getServerEnv();

if (env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: env.NEXT_PUBLIC_SENTRY_DSN,
    environment: env.ENV,
    release: env.APP_VERSION,
    sendDefaultPii: false,
    tracesSampleRate: process.env.NODE_ENV === "development" ? 1.0 : 0.1,
  });
}

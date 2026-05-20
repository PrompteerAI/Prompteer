// Edge runtime Sentry configuration for Next.js proxy and edge handlers.
// Empty NEXT_PUBLIC_SENTRY_DSN keeps local development silent.

import * as Sentry from "@sentry/nextjs";

if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    environment: process.env.ENV ?? process.env.NODE_ENV,
    release: process.env.APP_VERSION,
    sendDefaultPii: false,
    tracesSampleRate: process.env.NODE_ENV === "development" ? 1.0 : 0.1,
  });
}

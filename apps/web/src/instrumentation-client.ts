// Browser-side optional Sentry initialization. The SDK only starts when
// NEXT_PUBLIC_SENTRY_DSN is configured.

import * as Sentry from "@sentry/nextjs";

import { publicEnv } from "@/lib/env";

if (publicEnv.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: publicEnv.NEXT_PUBLIC_SENTRY_DSN,
    environment: process.env.NODE_ENV,
    release: publicEnv.NEXT_PUBLIC_APP_VERSION,
    sendDefaultPii: false,
    tracesSampleRate: process.env.NODE_ENV === "development" ? 1.0 : 0.1,
    enableLogs: true,
  });
}

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart;

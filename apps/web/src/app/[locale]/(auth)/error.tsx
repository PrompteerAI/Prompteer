// Auth route-group error boundary.
"use client";

import * as Sentry from "@sentry/nextjs";
import { useMutation } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useEffect } from "react";

import { publicEnv } from "@/lib/env";

export default function AuthRouteGroupError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.ReactElement {
  const t = useTranslations("errors");
  const reportMutation = useMutation({
    mutationKey: ["client-error-report", "auth", error.digest ?? error.message],
    mutationFn: () => reportError(error),
  });
  const showDetail = process.env.NODE_ENV !== "production";

  useEffect(() => {
    if (publicEnv.NEXT_PUBLIC_SENTRY_DSN) {
      Sentry.captureException(error);
    }
  }, [error]);

  return (
    <main className="grid min-h-screen place-items-center bg-zinc-50 px-6">
      <section className="w-full max-w-md rounded-lg border border-zinc-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-zinc-950">
          {t("authTitle")}
        </h1>
        <p className="mt-2 text-sm leading-6 text-zinc-600">
          {showDetail ? error.message : t("authUnexpectedDescription")}
        </p>
        {error.digest ? (
          <p className="mt-3 break-all font-mono text-xs text-zinc-500">
            {t("supportId")}: {error.digest}
          </p>
        ) : null}
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            className="rounded-md bg-zinc-950 px-4 py-2 text-sm text-white"
            onClick={reset}
            type="button"
          >
            {t("retry")}
          </button>
          <button
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm text-zinc-900 disabled:cursor-not-allowed disabled:text-zinc-500"
            disabled={reportMutation.isPending || reportMutation.isSuccess}
            onClick={() => {
              reportMutation.mutate();
            }}
            type="button"
          >
            {reportMutation.isSuccess ? t("reported") : t("report")}
          </button>
        </div>
      </section>
    </main>
  );
}

async function reportError(error: Error & { digest?: string }): Promise<void> {
  const response = await fetch("/api/errors", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      message: error.message,
      digest: error.digest,
      path: window.location.pathname,
      userAgent: window.navigator.userAgent,
    }),
  });
  if (!response.ok) {
    throw new Error("Error report failed.");
  }
}
